from __future__ import annotations

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    StringProperty,
    ObjectProperty,
    ListProperty,
)

from kivy.uix.widget import Widget

from kivymd.uix.segmentedbutton import MDSegmentedButton, MDSegmentedButtonItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dropdownitem import (  # noqa: F401 - register in Factory
    MDDropDownItem,
    MDDropDownItemText,
)

import logging

from mvckivy.mvc_base import BaseScreen
from mvckivy.mvc_base.base_app_screen import BaseAppScreen

logger = logging.getLogger("swap_card")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[swap_card] %(levelname)s: %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.DEBUG)


class StretchSegmentedButton(MDSegmentedButton):
    """Растягиваем контейнер сегментов по ширине карточки и снимаем min-width."""

    fit_to_parent = BooleanProperty(True)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        if self.fit_to_parent and "container" in self.ids:
            c = self.ids.container
            c.size_hint_min_x = 0
            self.bind(width=lambda *_: setattr(c, "width", self.width))


class SmartSegmentItem(MDSegmentedButtonItem):
    """Сегмент с простой логикой показа подписи.

    Лейбл показывается всегда, если :attr:`show_only_active_label` == False,
    и только у активного сегмента, если True.
    Текст и иконка задаются через свойства :attr:`label_text` и :attr:`icon_name`.
    """

    show_only_active_label = BooleanProperty(False)
    label_text = StringProperty("")
    icon_name = StringProperty("")
    display_text = StringProperty("")
    display_padding = ListProperty([dp(12), 0, dp(12), 0])
    _text_shown = BooleanProperty(False)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._refresh_label()

    def on_active(self, instance, value):
        # Сохраняем анимации родителя и обновляем подпись
        super().on_active(instance, value)
        self._refresh_label()

    def on_show_only_active_label(self, *_):
        self._refresh_label()

    def on_label_text(self, *_):
        self._refresh_label()

    def _refresh_label(self):
        show = (not self.show_only_active_label) or bool(self.active)
        # Пересчёт min-width панели при переключении подписи
        if self._label and self._segmented_button and show != self._text_shown:
            try:
                self._segmented_button._set_size_hint_min_x(
                    self._label, sign=(1 if show else -1)
                )
            except Exception:
                pass
            self._text_shown = show
        self.display_text = self.label_text if show else ""
        self.display_padding = [dp(12), 0, dp(12), 0] if show else [0, 0, 0, 0]
        logger.debug(
            f"SmartSegmentItem refresh: text='{self.label_text}', active={self.active}, "
            f"show_only_active={self.show_only_active_label}, display='{self.display_text}'"
        )


class CollapsibleMenuController(Widget):
    """Сворачиваемая карточка с drag по «ручке» и клиппингом контента."""

    title = StringProperty("Управление миссией БПЛА")

    # текущий транспорт и его иконка
    current_transport = StringProperty("Квадрокоптер")
    transport_icon = StringProperty("quadcopter")

    # Прямые ссылки на важные виджеты (минимум .ids в Python)
    menu_card = ObjectProperty(None, rebind=True)
    grip = ObjectProperty(None, rebind=True)
    header = ObjectProperty(None, rebind=True)
    segbar = ObjectProperty(None, rebind=True)
    sections = ObjectProperty(None, rebind=True)
    scroll = ObjectProperty(None, rebind=True)
    seg_control = ObjectProperty(None, rebind=True)
    # нижняя панель вкладок (footer)
    tabs = ObjectProperty(None, rebind=True)
    carousel = ObjectProperty(None, rebind=True)
    body_box = ObjectProperty(None, rebind=True)

    # авто 1↔2 столбца
    cols = NumericProperty(1)
    # Порог переключения на 2 колонки чуть выше, чтобы на ширине ~520px
    # оставаться в 1 колонке (как ожидается при старте)
    two_cols_breakpoint = NumericProperty(dp(560))
    # Признак компактного мобильного режима (горизонтальная ориентация, невысокий экран)
    mobile_mode = BooleanProperty(False)
    # В мобильном режиме подписи только у активного сегмента
    show_only_active_label = BooleanProperty(False)
    # Плотности/размеры для адаптации
    header_h = NumericProperty(dp(60))
    header_pad_v = NumericProperty(dp(10))
    header_spacing = NumericProperty(dp(12))
    divider_pad = NumericProperty(dp(12))
    list_item_h = NumericProperty(dp(84))
    content_pad_top = NumericProperty(dp(8))
    sections_spacing = NumericProperty(dp(12))
    list_grid_spacing = NumericProperty(dp(8))
    section_label_extra = NumericProperty(dp(6))
    # Хедер и иконки
    show_header_title = BooleanProperty(True)
    icon_size = NumericProperty(dp(18))
    header_title_text = StringProperty("")
    # Шрифты
    font_headline_sp = NumericProperty(sp(16))
    font_support_sp = NumericProperty(sp(12))
    font_section_sp = NumericProperty(sp(16))

    # нормированное состояние
    slide = NumericProperty(0.0)  # 0.0 = раскрыто, 1.0 = свернуто
    open_h = NumericProperty(dp(520))  # вычисляется от контента
    closed_h = NumericProperty(dp(88))  # ручка + сегмент-бар
    content_height = NumericProperty(0)
    # Доля, которую должен занимать body от полной высоты карточки
    body_min_ratio = NumericProperty(0.70)

    # drag state
    _dragging = BooleanProperty(False)
    _start_y = NumericProperty(0.0)
    _start_slide = NumericProperty(0.0)
    swipe_threshold_px = NumericProperty(dp(48))
    _layout_ready = BooleanProperty(False)
    _finalize_trigger = None
    _transport_menu: MDDropdownMenu | None = None

    def on_kv_post(self, _):
        Window.bind(size=self._on_window_resize)
        self._on_window_resize()

        # До готовности макета держим контент закрытым.
        self.slide = 1.0
        self.content_height = 0
        self._layout_ready = False

        # Триггер отложенного пересчёта (в одном кадре).
        self._finalize_trigger = Clock.create_trigger(
            lambda *_: self._finalize_layout(), 0
        )

        # Когда поменяется высота секций/хедера/сегмента — пересчёт.
        if self.sections:
            self.sections.bind(minimum_height=lambda *_: self._finalize_trigger())
        if self.header:
            self.header.bind(height=lambda *_: self._finalize_trigger())
        if self.segbar:
            self.segbar.bind(height=lambda *_: self._finalize_trigger())
        if self.tabs:
            self.tabs.bind(height=lambda *_: self._finalize_trigger())

        # Переносим карусель из футера (tabs) в body_box, сохраняя ссылку в tabs
        def _move_carousel(*_):
            try:
                if self.carousel and self.tabs:
                    # перенесём карусель вверх в body_box, если ещё не там
                    if self.carousel.parent is not self.body_box and self.body_box:
                        if self.carousel.parent:
                            try:
                                self.carousel.parent.remove_widget(self.carousel)
                            except Exception:
                                pass
                        self.body_box.clear_widgets()
                        self.body_box.add_widget(self.carousel)
            except Exception:
                pass
            # после переноса свяжем свойства табов
            try:
                self._link_tab_props()
            except Exception:
                pass
            # Первый пересчёт после сборки KV.
            if self._finalize_trigger is not None:
                self._finalize_trigger()

        Clock.schedule_once(_move_carousel, 0)

    def _finalize_layout(self):
        """Единая точка: пересчитать высоты и применить slide без анимации."""
        self._recalc_heights_and_viewport()
        self._layout_ready = True
        self._apply_slide(no_anim=True)

    def _iter_tab_slides(self):
        try:
            return list(self.carousel.slides) if self.carousel else []
        except Exception:
            return []

    def _link_tab_props(self, *_):
        for slide in self._iter_tab_slides():
            try:
                if hasattr(slide, "cols_g"):
                    slide.cols_g = self.cols
                if hasattr(slide, "list_grid_spacing"):
                    slide.list_grid_spacing = self.list_grid_spacing
                if hasattr(slide, "list_item_h"):
                    slide.list_item_h = self.list_item_h
                if hasattr(slide, "divider_pad"):
                    slide.divider_pad = self.divider_pad
                if hasattr(slide, "section_label_extra"):
                    slide.section_label_extra = self.section_label_extra
                if hasattr(slide, "sections_spacing"):
                    slide.sections_spacing = self.sections_spacing
                # ссылки на ключевые виджеты для скролла
                if hasattr(slide, "ids"):
                    if "sections" in slide.ids:
                        self.sections = slide.ids["sections"]
                    if "scroll" in slide.ids:
                        self.scroll = slide.ids["scroll"]
            except Exception:
                pass

        # обновления при изменении контроллера
        self.bind(
            cols=lambda *_: [
                setattr(s, "cols_g", self.cols)
                for s in self._iter_tab_slides()
                if hasattr(s, "cols_g")
            ]
        )
        self.bind(
            list_grid_spacing=lambda *_: [
                setattr(s, "list_grid_spacing", self.list_grid_spacing)
                for s in self._iter_tab_slides()
                if hasattr(s, "list_grid_spacing")
            ]
        )
        self.bind(
            list_item_h=lambda *_: [
                setattr(s, "list_item_h", self.list_item_h)
                for s in self._iter_tab_slides()
                if hasattr(s, "list_item_h")
            ]
        )
        self.bind(
            divider_pad=lambda *_: [
                setattr(s, "divider_pad", self.divider_pad)
                for s in self._iter_tab_slides()
                if hasattr(s, "divider_pad")
            ]
        )
        self.bind(
            section_label_extra=lambda *_: [
                setattr(s, "section_label_extra", self.section_label_extra)
                for s in self._iter_tab_slides()
                if hasattr(s, "section_label_extra")
            ]
        )
        self.bind(
            sections_spacing=lambda *_: [
                setattr(s, "sections_spacing", self.sections_spacing)
                for s in self._iter_tab_slides()
                if hasattr(s, "sections_spacing")
            ]
        )

    def _on_window_resize(self, *_):
        w, h = Window.width, Window.height
        # Компактный ландшафт: близкий к мобильному. Включаем для низкой высоты
        # или умеренной ширины, чтобы тестовое окно 800x600 тоже считалось моб.
        self.mobile_mode = (w >= h) and (h <= dp(600) or w <= dp(920))
        self.show_only_active_label = self.mobile_mode
        self.show_header_title = not self.mobile_mode
        self.header_title_text = self.title if self.show_header_title else ""
        # Настройка плотностей представления
        if self.mobile_mode:
            self.header_h = dp(32)
            self.header_pad_v = dp(4)
            self.header_spacing = dp(6)
            self.icon_size = dp(16)
            self.divider_pad = dp(8)
            self.list_item_h = dp(60)
            self.content_pad_top = dp(2)
            self.sections_spacing = dp(6)
            self.list_grid_spacing = dp(4)
            self.section_label_extra = dp(0)
        else:
            self.header_h = dp(60)
            self.header_pad_v = dp(10)
            self.header_spacing = dp(12)
            self.icon_size = dp(18)
            self.divider_pad = dp(12)
            self.list_item_h = dp(84)
            self.content_pad_top = dp(8)
            self.sections_spacing = dp(12)
            self.list_grid_spacing = dp(8)
            self.section_label_extra = dp(6)

        if w >= 1400:
            card_w = max(dp(560), w * 0.40)
        elif w >= 1024:
            card_w = max(dp(520), w * 0.46)
        else:
            if self.mobile_mode:
                # Карточка: 40% ширины экрана (минимум 320dp)
                card_w = max(dp(320), w * 0.40)
            else:
                card_w = max(dp(360), w * 0.90)

        # Пропорциональное уменьшение шрифтов от базовой ширины 360dp
        base = dp(360)
        scale = max(0.85, min(1.0, card_w / base))
        self.font_headline_sp = sp(16 * scale)
        self.font_support_sp = sp(12 * scale)
        self.font_section_sp = sp(16 * scale)

        if self.menu_card:
            self.menu_card.width = card_w
        # В мобильном режиме — всегда одна колонка
        self.cols = (
            1 if self.mobile_mode else (2 if card_w >= self.two_cols_breakpoint else 1)
        )
        # Пересчитать после стабилизации лейаута
        if self._finalize_trigger is not None:
            self._finalize_trigger()
        logger.debug(
            f"resize: {w}x{h} mobile={self.mobile_mode} card_w={card_w:.1f} cols={self.cols} "
            f"header_h={self.header_h} fonts(h/s/sec)={self.font_headline_sp:.1f}/"
            f"{self.font_support_sp:.1f}/{self.font_section_sp:.1f}"
        )

    # ресайз + колонк
    def _recalc_heights_and_viewport(self):
        handle_h = self.grip.height if self.grip else dp(18)
        header_h = self.header.height if self.header else dp(60)
        segbar_h = self.segbar.height if self.segbar else dp(56)
        pad_tb = dp(8) + dp(8)
        sections_h = self.sections.minimum_height if self.sections else 0

        if self.mobile_mode:
            # Высота карточки ~ 80% экрана. Переводим в open_h через content.
            target_card_h = Window.height * 0.80
            target_content = max(target_card_h - handle_h - segbar_h, dp(56))
            self.open_h = self.closed_h + target_content
        else:
            desired_open = header_h + pad_tb + sections_h
            max_open = max(dp(240), Window.height * 0.70)
            self.open_h = min(desired_open, max_open)

        # Обеспечиваем, чтобы body занимал не менее body_min_ratio от общей высоты
        # Полная высота карточки при раскрытии: handle + content_height + segbar
        # content_height включает header + pad_tb + body_height
        # Требование: body_height >= body_min_ratio * total_card_h
        # Пусть S = handle_h + header_h + pad_tb + segbar_h
        # Тогда body_h >= body_min_ratio * (S + body_h) =>
        # (1 - body_min_ratio) * body_h >= body_min_ratio * S
        # body_h >= body_min_ratio * S / (1 - body_min_ratio)
        S = handle_h + header_h + pad_tb + segbar_h
        min_body_h = (self.body_min_ratio * S) / max(1e-3, (1.0 - self.body_min_ratio))
        # текущий body_h (при полном раскрытии) = open_h - header_h - pad_tb
        curr_body_h = self.open_h - header_h - pad_tb
        if curr_body_h < min_body_h:
            self.open_h = min_body_h + header_h + pad_tb

        self.closed_h = handle_h + segbar_h + dp(8)

        if self.scroll:
            viewport_h = self.open_h - header_h - pad_tb
            self.scroll.do_scroll_y = sections_h > viewport_h

    # slide → content_height
    def on_slide(self, *_):
        self._apply_slide(no_anim=True)

    def _apply_slide(self, *, no_anim: bool = False):
        if not self._layout_ready:
            # До готовности держим закрытым без анимации.
            self.content_height = 0
            return
        total_delta = max(self.open_h - self.closed_h, 1)
        target_content = (1.0 - self.slide) * total_delta
        if no_anim:
            self.content_height = target_content
        else:
            Animation.cancel_all(self, "content_height")
            Animation(content_height=target_content, d=0.22, t="out_cubic").start(self)

    # кнопки
    def toggle(self):
        target = 0.0 if self.slide >= 0.5 else 1.0
        self.animate_to(target)

    def expand(self):
        self.animate_to(0.0)

    def collapse(self):
        self.animate_to(1.0)

    def on_segment_pressed(self, _key: str):
        self.expand()

    def animate_to(self, target: float, duration: float = 0.22):
        Animation.cancel_all(self, "slide")
        Animation(slide=target, d=duration, t="out_cubic").start(self)

    # --- Транспорт: выпадающее меню в заголовке ---
    def open_transport_menu(self, caller_widget):
        """Открыть меню выбора транспорта, закрепив его за `caller_widget`."""
        base_item = {"height": dp(40), "viewclass": "MDDropdownTextItem"}
        items = [
            {
                "text": "Квадрокоптер",
                "on_release": lambda: self._set_transport("Квадрокоптер", "quadcopter"),
                **base_item,
            },
            {
                "text": "Самолёт",
                "on_release": lambda: self._set_transport("Самолёт", "airplane"),
                **base_item,
            },
            {
                "text": "Вездеход",
                "on_release": lambda: self._set_transport("Вездеход", "car"),
                **base_item,
            },
            {
                "text": "Вертолёт",
                "on_release": lambda: self._set_transport("Вертолёт", "helicopter"),
                **base_item,
            },
        ]

        if self._transport_menu is None:
            self._transport_menu = MDDropdownMenu(
                items=items,
                position="bottom",
                width=dp(200),
                border_margin=dp(8),
                md_bg_color=(0.14, 0.15, 0.16, 1),
            )

        # Каждый раз переопределяем якорь и перечень (чтобы ламбды ссылались на актуальный self)
        self._transport_menu.caller = caller_widget
        self._transport_menu.items = items
        # Выбираем направление роста меню по доступному месту
        try:
            from kivy.core.window import Window

            item_h = base_item["height"]
            need_h = item_h * len(items) + dp(16)
            space_below = Window.height - caller_widget.to_window(*caller_widget.pos)[1]
            self._transport_menu.ver_growth = "down" if space_below > need_h else "up"
        except Exception:
            self._transport_menu.ver_growth = "down"
        self._transport_menu.open()

    def _set_transport(self, name: str, icon: str):
        self.current_transport = name
        self.transport_icon = icon
        if self._transport_menu:
            self._transport_menu.dismiss()

    # жест по ручке
    def _in_handle(self, touch) -> bool:
        if not self.grip:
            return False
        lx, ly = self.grip.to_widget(*touch.pos)
        return self.grip.collide_point(lx, ly)

    def on_touch_down(self, touch):
        if self._in_handle(touch):
            self._dragging = True
            self._start_y = touch.y
            self._start_slide = self.slide
            touch.grab(self)
            if self.scroll:
                self.scroll.do_scroll_y = False
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self._dragging:
            total = max(self.open_h - self.closed_h, 1)
            dy = touch.y - self._start_y
            self.slide = min(1.0, max(0.0, self._start_slide + (-dy / total)))
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.scroll:
            self.scroll.do_scroll_y = True

        if touch.grab_current is self and self._dragging:
            touch.ungrab(self)
            self._dragging = False
            target = 1.0 if self.slide >= 0.5 else 0.0
            self.animate_to(target)
            return True
        return super().on_touch_up(touch)


class AppScreen(BaseAppScreen):
    pass


class InitialScreen(BaseScreen):
    pass
