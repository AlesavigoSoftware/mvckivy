from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.scrollview import ScrollView

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
)
from kivymd.uix.textfield import MDTextField


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def top(self) -> float:
        return self.y + self.h

    @property
    def bottom(self) -> float:
        return self.y


class KeyboardAvoidingRoot(MDBoxLayout):
    """
    Корневой контейнер:
      - управляет высотой «клавиатуры» (эмулятор снизу),
      - гарантирует видимость активного MDTextField (скролл/сдвиг),
      - умеет переключаться в диалоговый режим ввода.
    """

    orientation = "vertical"

    keyboard_height = NumericProperty(0.0)
    offset_y = NumericProperty(0.0)  # сдвиг только зоны контента (не клавиатуры)
    use_dialog_mode = BooleanProperty(False)

    # ссылки из KV
    content_scroll: Optional[ScrollView] = ObjectProperty(None, rebind=True)
    shift_container: Optional[MDBoxLayout] = ObjectProperty(None, rebind=True)

    # служебное
    _focused: Optional[MDTextField] = None
    _anim: Optional[Animation] = None
    _dialog: Optional[MDDialog] = None

    def on_keyboard_height(self, *_):
        if self._focused and self._focused.focus:
            Clock.schedule_once(lambda *_: self.ensure_visible(self._focused), 0)

    def on_field_focus(self, field: MDTextField, value: bool):
        self._focused = field if value else None
        if not value:
            self._animate_offset(0)
            return
        if self.use_dialog_mode:
            Clock.schedule_once(lambda *_: self._open_input_dialog(field), 0)
        else:
            Clock.schedule_once(lambda *_: self.ensure_visible(field), 0)

    def ensure_visible(self, field: MDTextField, padding: float = dp(12)):
        """Держим поле в видимой зоне над «клавиатурой»."""
        if not field.get_root_window():
            return

        fx, fy = field.to_window(field.x, field.y)
        fw, fh = field.size
        fr = Rect(fx, fy, fw, fh)

        _win_w, win_h = Window.size
        free_top = win_h
        free_bottom = self.keyboard_height

        # 1) Пытаемся нативно проскроллить ScrollView
        if isinstance(self.content_scroll, ScrollView):
            try:
                self.content_scroll.scroll_to(field, padding=padding, animate=True)
                # После scroll_to проверим перекрытие «клавиатурой» и при необходимости слегка сдвинем контейнер
                Clock.schedule_once(
                    lambda *_: self._post_scroll_adjust(field, padding), 0.05
                )
                return
            except Exception:
                pass

        # 2) Фолбэк: двигаем shift_container через offset_y
        shift = 0.0
        if fr.top > free_top - padding:
            shift = fr.top - (free_top - padding)
        elif fr.bottom < free_bottom + padding:
            shift = (free_bottom + padding) - fr.bottom
        self._animate_offset(shift)

    def _post_scroll_adjust(self, field: MDTextField, padding: float):
        """Доп. корректировка после scroll_to, если низ поля все ещё под «клавиатурой»."""
        fx, fy = field.to_window(field.x, field.y)
        fw, fh = field.size
        fr = Rect(fx, fy, fw, fh)
        free_bottom = self.keyboard_height

        if fr.bottom < free_bottom + padding:
            self._animate_offset((free_bottom + padding) - fr.bottom)
        else:
            self._animate_offset(0)

    def _animate_offset(self, shift: float):
        if self._anim:
            self._anim.cancel(self)
        self._anim = Animation(offset_y=max(0.0, shift), d=0.18, t="out_quad")
        self._anim.start(self)

    # ---------- Диалоговый режим (новый API MDDialog) ----------
    def _open_input_dialog(self, field: MDTextField):
        if self._dialog:
            self._dialog.dismiss()
            self._dialog = None

        proxy_box = MDBoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        proxy_input = MDTextField(text=field.text or "", mode="outlined")
        proxy_box.add_widget(proxy_input)

        def accept(*_):
            field.text = proxy_input.text
            field.focus = False
            if self._dialog:
                self._dialog.dismiss()
                self._dialog = None

        self._dialog = MDDialog(
            MDDialogHeadlineText(text="Ввод", halign="left"),
            MDDialogContentContainer(proxy_box, orientation="vertical"),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Готово"),
                    style="text",
                    on_release=accept,
                ),
                spacing="8dp",
            ),
        )
        self._dialog.open()
        # Разместим диалог над «клавиатурой»
        kb = self.keyboard_height
        if kb:
            self._dialog.pos = (self._dialog.pos[0], kb + dp(8))

    # ---------- Эмулятор «клавиатуры» ----------
    def toggle_keyboard(self):
        self.keyboard_height = 0 if self.keyboard_height > 0 else dp(280)
        self.on_keyboard_height()


KV = r"""
#:import dp kivy.metrics.dp

<KeyboardAvoidingRoot>:
    # Верхняя панель управления (на новых кнопках)
    MDBoxLayout:
        size_hint_y: None
        height: dp(56)
        padding: dp(12), 0
        spacing: dp(10)
        md_bg_color: app.theme_cls.primaryColor

        MDButton:
            style: "tonal"
            on_release: root.toggle_keyboard()
            MDButtonIcon:
                icon: "keyboard"
            MDButtonText:
                text: "Показать/Спрятать клавиатуру"

        MDButton:
            style: "outlined"
            on_release: setattr(root, "use_dialog_mode", not root.use_dialog_mode)
            MDButtonIcon:
                icon: "message-text-outline"
            MDButtonText:
                text: "Диалог вместо сдвига"

    # Текст-индикатор режима
    MDLabel:
        text: "Режим: " + ("Диалог" if root.use_dialog_mode else "Сдвиг экрана")
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(28)

    # Сдвигаем ТОЛЬКО этот контейнер (клавиатура внизу не двигается)
    MDBoxLayout:
        id: shift_container
        orientation: "vertical"
        on_kv_post: setattr(root, "shift_container", self)

        canvas.before:
            PushMatrix
            Translate:
                xy: 0, root.offset_y
        canvas.after:
            PopMatrix

        ScrollView:
            id: scroll
            on_kv_post: setattr(root, "content_scroll", self)
            do_scroll_x: False

            MDBoxLayout:
                orientation: "vertical"
                padding: dp(16), dp(8)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

                MDTextField:
                    mode: "outlined"
                    on_focus: root.on_field_focus(self, self.focus)
                    MDTextFieldHintText:
                        text: "Имя"

                MDTextField:
                    mode: "outlined"
                    on_focus: root.on_field_focus(self, self.focus)
                    MDTextFieldHintText:
                        text: "Фамилия"

                MDTextField:
                    mode: "outlined"
                    on_focus: root.on_field_focus(self, self.focus)
                    MDTextFieldHintText:
                        text: "E-mail"

                MDTextField:
                    mode: "outlined"
                    on_focus: root.on_field_focus(self, self.focus)
                    MDTextFieldHintText:
                        text: "Телефон"

                MDLabel:
                    text: "Демо-текст\\n" * 10
                    adaptive_height: True
                    theme_text_color: "Secondary"

                MDTextField:
                    mode: "outlined"
                    on_focus: root.on_field_focus(self, self.focus)
                    MDTextFieldHintText:
                        text: "Поле у самого низа (проверь смещение)"

                MDTextField:
                    mode: "outlined"
                    on_focus: root.on_field_focus(self, self.focus)
                    MDTextFieldHintText:
                        text: "Еще одно поле у низа"

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(100)

    # НИЖНЯЯ ПАНЕЛЬ — «экранная клавиатура» (эмулятор)
    MDBoxLayout:
        md_bg_color: app.theme_cls.primaryColor
        size_hint_y: None
        height: root.keyboard_height
        padding: dp(12)
        spacing: dp(12)

        MDButton:
            style: "text"
            disabled: True
            MDButtonIcon:
                icon: "keyboard-variant"
            MDButtonText:
                text: "Экранная клавиатура (эмуляция)"

        MDLabel:
            text: "Высота: " + str(int(root.keyboard_height)) + "dp"
            theme_text_color: "Custom"
            text_color: app.theme_cls.onPrimaryColor


MDScreen:
    md_bg_color: app.theme_cls.backgroundColor
    KeyboardAvoidingRoot:
"""


class App(MDApp):
    def build(self):
        self.title = "Keyboard-aware TextField (KivyMD 2.0)"
        self.theme_cls.primary_palette = "Blue"
        Window.softinput_mode = (
            "below_target"  # удобно, если целитесь в мобильные платформы
        )
        return Builder.load_string(KV)


if __name__ == "__main__":
    App().run()
