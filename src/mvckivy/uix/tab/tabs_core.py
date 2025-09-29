from __future__ import annotations

from functools import partial
from typing import Callable, Any

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from kivy.graphics import Color, RoundedRectangle
from kivymd.theming import ThemableBehavior

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin

from .components import (
    MKVBottomTabItem,
    MKVTabCarousel,
    MKVTabContent,
    MKVTabItem,
    TabDefinition,
)


class MKVTabBar(AliasDedupeMixin, ThemableBehavior, BoxLayout):
    tab_mode = OptionProperty("fixed", options=("fixed", "scrollable"))
    equal_item_widths = BooleanProperty(True)
    min_item_width = NumericProperty(dp(96))
    max_item_width = NumericProperty(dp(320))
    bar_height = NumericProperty(dp(64))
    item_spacing = NumericProperty(dp(12))

    show_indicator = BooleanProperty(True)
    indicator_height = NumericProperty(dp(4))
    indicator_radius = ListProperty([dp(2), dp(2), 0, 0])
    indicator_transition = StringProperty("out_quad")
    indicator_duration = NumericProperty(0.25)

    tabs_ref = ObjectProperty(None, rebind=True, allownone=True)
    item_cls = ObjectProperty(MKVTabItem, rebind=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = self.bar_height

        self._items: list[MKVTabItem] = []
        self._scroll_view = ScrollView(size_hint=(1, None), do_scroll_y=False, bar_width=0)
        self._scroll_view.size_hint_y = None
        self._scroll_view.height = self.bar_height
        self._container = BoxLayout(
            orientation="horizontal",
            size_hint=(None, 1),
            spacing=self.item_spacing,
            padding=(dp(12), 0, dp(12), 0),
        )
        self._container.bind(minimum_width=self._on_minimum_width)
        self._scroll_view.add_widget(self._container)
        self.add_widget(self._scroll_view)

        self._trigger_layout = Clock.create_trigger(self._layout_items, 0)
        self._indicator_animation: Animation | None = None
        self._build_indicator_canvas()

        self.bind(
            bar_height=self._on_bar_height,
            tab_mode=lambda *_: self._trigger_layout(),
            equal_item_widths=lambda *_: self._trigger_layout(),
            min_item_width=lambda *_: self._trigger_layout(),
            max_item_width=lambda *_: self._trigger_layout(),
            item_spacing=self._on_item_spacing,
            indicator_height=lambda *_: self._update_indicator_geometry(),
            indicator_radius=lambda *_: self._update_indicator_geometry(),
            show_indicator=lambda *_: self._update_indicator_visibility(),
        )
        self.theme_cls.bind(primaryColor=lambda *_: self._update_indicator_color())

    def _build_indicator_canvas(self) -> None:
        with self.canvas.after:
            self._indicator_color_instruction = Color(0, 0, 0, 0)
            self._indicator_rect = RoundedRectangle(
                size=(0, 0), pos=self.pos, radius=self.indicator_radius
            )
        self.bind(pos=self._update_indicator_geometry, size=self._update_indicator_geometry)
        self._update_indicator_color()

    def _update_indicator_color(self) -> None:
        color = list(self.theme_cls.primaryColor)
        if not self.show_indicator:
            color = [*color[:3], 0]
        self._indicator_color_instruction.rgba = color

    def _update_indicator_visibility(self) -> None:
        self._update_indicator_color()
        if not self.show_indicator:
            self._indicator_rect.size = (0, 0)

    def _update_indicator_geometry(self, *_):
        active = next((item for item in self._items if item.active), None)
        if active is not None:
            self._animate_indicator_to(active, animate=False)

    def _on_minimum_width(self, *_):
        if self.tab_mode == "scrollable":
            self._container.width = self._container.minimum_width
        self._trigger_layout()

    def _on_item_spacing(self, *_):
        self._container.spacing = self.item_spacing
        self._trigger_layout()

    def _on_bar_height(self, *_):
        self.height = self.bar_height
        self._scroll_view.height = self.bar_height
        for item in self._items:
            item.height = max(item.alias_height, self.bar_height)

    def _layout_items(self, *_):
        if not self._items:
            return
        if self.tab_mode == "fixed":
            self._scroll_view.do_scroll_x = False
            self._container.size_hint_x = 1
            self._container.width = self.width
            if self.equal_item_widths:
                item_count = len(self._items)
                width = self.width / item_count if item_count else self.width
                width = max(self.min_item_width, width)
                width = min(width, self.max_item_width)
                total_width = width * item_count
                if total_width > self.width and item_count:
                    self._scroll_view.do_scroll_x = True
                    self._container.size_hint_x = None
                    self._container.width = total_width
                for item in self._items:
                    item.size_hint_x = None
                    item.width = width
            else:
                for item in self._items:
                    item.size_hint_x = None
                    implicit = max(self.min_item_width, item.alias_implicit_width)
                    item.width = min(self.max_item_width, implicit)
        else:
            self._scroll_view.do_scroll_x = True
            self._container.size_hint_x = None
            self._container.width = max(
                self._container.minimum_width,
                self.width if self.equal_item_widths else self._container.minimum_width,
            )
            for item in self._items:
                item.size_hint_x = None
                implicit = max(self.min_item_width, item.alias_implicit_width)
                item.width = min(self.max_item_width, implicit)
        for item in self._items:
            item.height = max(item.alias_height, self.bar_height)

    def build_item(self, definition: TabDefinition) -> MKVTabItem:
        item_cls = self.item_cls if isinstance(self.item_cls, type) else MKVTabItem
        item = item_cls()
        item.definition = definition
        item.tabs_ref = self.tabs_ref
        return item

    def add_tab_item(self, definition: TabDefinition) -> MKVTabItem:
        item = self.build_item(definition)
        definition.item = item
        self._items.append(item)
        self._container.add_widget(item)
        self._trigger_layout()
        return item

    def remove_tab_item(self, item: MKVTabItem) -> None:
        if item in self._items:
            self._items.remove(item)
        if item.parent is self._container:
            self._container.remove_widget(item)
        self._trigger_layout()

    def index_of(self, item: MKVTabItem) -> int:
        try:
            return self._items.index(item)
        except ValueError:
            return -1

    def set_active(self, item: MKVTabItem | None, *, animate: bool = True) -> None:
        for candidate in self._items:
            candidate.active = candidate is item
        if item is not None and self.show_indicator:
            self._animate_indicator_to(item, animate=animate)
            if animate:
                Clock.schedule_once(lambda *_: self.scroll_to_item(item, animate=True))
            else:
                self.scroll_to_item(item, animate=False)

    def scroll_to_item(self, item: MKVTabItem, *, animate: bool = True) -> None:
        if item.parent is None:
            return
        self._scroll_view.scroll_to(item, animate=animate)

    def _animate_indicator_to(self, item: MKVTabItem, *, animate: bool) -> None:
        if not self.show_indicator:
            return
        container = item.parent
        scroll_view = self._scroll_view
        if container is None or scroll_view is None:
            return

        content_x, _ = scroll_view.to_widget(*scroll_view._viewport.to_window(item.x, 0))
        target_x = self.x + content_x
        target_pos = (target_x, self.y)
        target_size = (item.width, self.indicator_height)
        if self._indicator_animation:
            self._indicator_animation.cancel(self._indicator_rect)
        if animate and self.indicator_duration:
            self._indicator_animation = Animation(
                pos=target_pos,
                size=target_size,
                d=self.indicator_duration,
                t=self.indicator_transition,
            )
            self._indicator_animation.start(self._indicator_rect)
        else:
            self._indicator_rect.pos = target_pos
            self._indicator_rect.size = target_size
        self._indicator_rect.radius = self.indicator_radius


class MKVTabs(AliasDedupeMixin, ThemableBehavior, BoxLayout):
    tab_mode = OptionProperty("fixed", options=("fixed", "scrollable"))
    equal_item_widths = BooleanProperty(True)
    min_item_width = NumericProperty(dp(96))
    max_item_width = NumericProperty(dp(320))

    current_index = NumericProperty(-1)
    current_tab = ObjectProperty(None, rebind=True, allownone=True)

    lock_swiping = BooleanProperty(False)
    lazy_content = BooleanProperty(True)

    tab_bar_cls = ObjectProperty(MKVTabBar, rebind=True)
    tab_item_cls = ObjectProperty(MKVTabItem, rebind=True)
    tab_content_cls = ObjectProperty(MKVTabContent, rebind=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        super().__init__(**kwargs)
        self.register_event_type("on_tab_add")
        self.register_event_type("on_tab_remove")
        self.register_event_type("on_tab_switch")

        self._definitions: list[TabDefinition] = []
        self._tab_bar = self._create_tab_bar()
        self._carousel = self._create_carousel()
        self.add_widget(self._tab_bar)
        self.add_widget(self._carousel)

        self.bind(tab_mode=self._sync_bar_layout, equal_item_widths=self._sync_bar_layout)
        self.bind(min_item_width=self._sync_bar_layout, max_item_width=self._sync_bar_layout)
        self.bind(lock_swiping=lambda *_: self._apply_lock_swiping())
        self.bind(lazy_content=lambda *_: self._on_lazy_content())
        self._apply_lock_swiping()

    def _create_tab_bar(self) -> MKVTabBar:
        bar_cls = self.tab_bar_cls if isinstance(self.tab_bar_cls, type) else MKVTabBar
        bar: MKVTabBar = bar_cls()
        bar.tabs_ref = self
        bar.item_cls = self.tab_item_cls if isinstance(self.tab_item_cls, type) else MKVTabItem
        bar.tab_mode = self.tab_mode
        bar.equal_item_widths = self.equal_item_widths
        bar.min_item_width = self.min_item_width
        bar.max_item_width = self.max_item_width
        return bar

    def _create_carousel(self) -> MKVTabCarousel:
        carousel = MKVTabCarousel(direction="right", loop=False)
        carousel.lock_swiping = self.lock_swiping
        carousel.bind(index=self._on_carousel_index)
        return carousel

    def add_tab(
        self,
        title: str,
        *,
        icon: str | None = None,
        content: Widget | None = None,
        content_factory: Callable[[], Widget] | None = None,
        active_icon: str | None = None,
        inactive_icon: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> MKVTabItem:
        definition = TabDefinition(
            title=title,
            icon=icon,
            content=content,
            content_factory=content_factory,
            active_icon=active_icon,
            inactive_icon=inactive_icon,
            data=data or {},
        )
        content_cls = (
            self.tab_content_cls if isinstance(self.tab_content_cls, type) else MKVTabContent
        )
        prev_index = self.current_index

        content_slide: MKVTabContent = content_cls()
        content_slide.definition = definition
        content_slide.lazy = self.lazy_content
        if not self.lazy_content:
            content_slide.ensure_content()
        definition.content_widget = content_slide

        tab_item = self._tab_bar.add_tab_item(definition)
        self._carousel.add_widget(content_slide)
        self._definitions.append(definition)
        self.dispatch("on_tab_add", tab_item)

        if self.current_index == -1:
            self.switch_to(tab_item, animate=False)
            self._refresh_current_tab_state()
        elif prev_index != -1:
            Clock.schedule_once(
                partial(self._restore_previous_selection, prev_index),
                0,
            )
        else:
            self._refresh_current_tab_state()

        return tab_item

    def remove_tab(self, target: int | MKVTabItem) -> None:
        index = self._coerce_index(target)
        if index is None:
            return
        definition = self._definitions.pop(index)
        if definition.item:
            self._tab_bar.remove_tab_item(definition.item)
        if definition.content_widget:
            self._carousel.remove_widget(definition.content_widget)
        self.dispatch("on_tab_remove", definition.item)
        if self._definitions:
            new_index = min(index, len(self._definitions) - 1)
            self.switch_to(new_index, animate=False)
        else:
            self.current_index = -1
            self.current_tab = None

    def switch_to(self, target: int | MKVTabItem | TabDefinition, *, animate: bool = True) -> None:
        index = self._coerce_index(target)
        if index is None or index == self.current_index:
            return
        definition = self._definitions[index]
        if definition.content_widget is None:
            return
        if definition.content_widget.lazy:
            definition.content_widget.ensure_content()
        self._tab_bar.set_active(definition.item, animate=animate)
        if animate:
            self._carousel.load_slide(definition.content_widget)
        else:
            self._carousel.index = index

    def _restore_previous_selection(self, index: int, *_args: Any) -> None:
        self.switch_to(index, animate=False)
        self._refresh_current_tab_state()

    def _refresh_current_tab_state(self) -> None:
        if self.current_tab is None:
            return
        self.current_tab._apply_active_state()
        self.current_tab._update_display_icon()

    def next(self) -> None:
        if not self._definitions:
            return
        next_index = (self.current_index + 1) % len(self._definitions)
        self.switch_to(next_index)

    def previous(self) -> None:
        if not self._definitions:
            return
        prev_index = (self.current_index - 1) % len(self._definitions)
        self.switch_to(prev_index)

    def _coerce_index(self, target: int | MKVTabItem | TabDefinition) -> int | None:
        if isinstance(target, int):
            if 0 <= target < len(self._definitions):
                return target
            return None
        if isinstance(target, TabDefinition):
            try:
                return self._definitions.index(target)
            except ValueError:
                return None
        if isinstance(target, MKVTabItem):
            return self._tab_bar.index_of(target)
        return None

    def _sync_bar_layout(self, *_):
        self._tab_bar.tab_mode = self.tab_mode
        self._tab_bar.equal_item_widths = self.equal_item_widths
        self._tab_bar.min_item_width = self.min_item_width
        self._tab_bar.max_item_width = self.max_item_width

    def _apply_lock_swiping(self) -> None:
        self._carousel.lock_swiping = self.lock_swiping

    def _on_lazy_content(self) -> None:
        for definition in self._definitions:
            if definition.content_widget is not None:
                definition.content_widget.lazy = self.lazy_content
                if not self.lazy_content:
                    definition.content_widget.ensure_content()

    def _on_carousel_index(self, carousel: MKVTabCarousel, index: int) -> None:
        if index < 0 or index >= len(self._definitions):
            return
        definition = self._definitions[index]
        if definition.content_widget and definition.content_widget.lazy:
            definition.content_widget.ensure_content()
        prev_tab = self.current_tab
        self.current_index = index
        self.current_tab = definition.item
        self._tab_bar.set_active(definition.item)
        self.dispatch("on_tab_switch", definition.item, prev_tab)

    @property
    def tabs(self) -> tuple[MKVTabItem, ...]:
        return tuple(
            definition.item for definition in self._definitions if definition.item is not None
        )

    @property
    def definitions(self) -> tuple[TabDefinition, ...]:
        return tuple(self._definitions)

    def on_tab_add(self, tab_item: MKVTabItem) -> None:  # pragma: no cover
        pass

    def on_tab_remove(self, tab_item: MKVTabItem | None) -> None:  # pragma: no cover
        pass

    def on_tab_switch(
        self, tab_item: MKVTabItem | None, prev_tab: MKVTabItem | None
    ) -> None:  # pragma: no cover
        pass


class MKVBottomSwipeTabs(MKVTabs):
    swiper_position = OptionProperty("bottom", options=("top", "bottom"))
    bar_height = NumericProperty(dp(56))
    item_spacing = NumericProperty(dp(8))
    active_text_color = ColorProperty(None)
    inactive_text_color = ColorProperty(None)
    active_icon_color = ColorProperty(None)
    inactive_icon_color = ColorProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tab_item_cls = MKVBottomTabItem
        self._tab_bar.item_cls = MKVBottomTabItem
        self._tab_bar.show_indicator = False
        self._tab_bar.bar_height = self.bar_height
        self._tab_bar.item_spacing = self.item_spacing
        self._tab_bar.bind(height=self._align_carousel_position)
        self.bind(swiper_position=lambda *_: self._align_carousel_position())
        self.bind(
            bar_height=lambda *_: setattr(self._tab_bar, "bar_height", self.bar_height),
            item_spacing=lambda *_: setattr(self._tab_bar, "item_spacing", self.item_spacing),
            active_text_color=lambda *_: self._refresh_item_colors(),
            inactive_text_color=lambda *_: self._refresh_item_colors(),
            active_icon_color=lambda *_: self._refresh_item_colors(),
            inactive_icon_color=lambda *_: self._refresh_item_colors(),
        )
        self._align_carousel_position()

    def add_tab(
        self,
        title: str,
        *,
        icon: str | None = None,
        content: Widget | None = None,
        content_factory: Callable[[], Widget] | None = None,
        active_icon: str | None = None,
        inactive_icon: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> MKVTabItem:
        item = super().add_tab(
            title,
            icon=icon,
            content=content,
            content_factory=content_factory,
            active_icon=active_icon,
            inactive_icon=inactive_icon,
            data=data,
        )
        item.active_text_color = self.active_text_color
        item.inactive_text_color = self.inactive_text_color
        item.active_icon_color = self.active_icon_color
        item.inactive_icon_color = self.inactive_icon_color
        item._apply_active_state()
        return item

    def _align_carousel_position(self, *_):
        self.clear_widgets()
        if self.swiper_position == "top":
            self.add_widget(self._carousel)
            self.add_widget(self._tab_bar)
        else:
            self.add_widget(self._tab_bar)
            self.add_widget(self._carousel)

    def _refresh_item_colors(self) -> None:
        for item in self.tabs:
            item.active_text_color = self.active_text_color
            item.inactive_text_color = self.inactive_text_color
            item.active_icon_color = self.active_icon_color
            item.inactive_icon_color = self.inactive_icon_color
            item._apply_active_state()


class MKVBottomTabs(MKVBottomSwipeTabs):
    """Variant with a fixed bottom bar and content stacked above it."""

    def __init__(self, **kwargs):
        kwargs.setdefault("swiper_position", "top")
        super().__init__(**kwargs)
