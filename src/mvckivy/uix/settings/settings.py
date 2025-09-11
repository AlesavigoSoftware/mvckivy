from __future__ import annotations

import os

import kivy.utils as utils
from kivy.factory import Factory
from kivy.metrics import dp, sp
from kivy.config import ConfigParser
from kivy.compat import string_types, text_type
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanelHeader
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.properties import (
    ObjectProperty,
    StringProperty,
    ListProperty,
    BooleanProperty,
    NumericProperty,
    DictProperty,
)
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.behaviors import CommonElevationBehavior
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDListItem
from kivymd.uix.divider import MDDivider

from mvckivy.uix.dialog import MKVDialog
from mvckivy.uix.scroll_view import MVCScrollView


class AttributeIsUnset(ValueError):
    pass


class MKVSettingItem(MDListItem):
    """mvckivy class for individual settings (within a panel). This class cannot
    be used directly; it is used for implementing the other setting classes.
    It builds a row with a title/description (left) and a setting control
    (right).

    Look at :class:`MDSettingBoolean`, :class:`MDSettingNumeric` and
    :class:`MDSettingOptions` for usage examples.

    """

    title = StringProperty("<No title set>")
    """Title of the setting, defaults to '<No title set>'.

    :attr:`title` is a :class:`~kivy.properties.StringProperty` and defaults
    to '<No title set>'.
    """

    desc = StringProperty(None, allownone=True)
    """Description of the setting, rendered on the line below the title.

    :attr:`desc` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.
    """

    key = StringProperty(None)
    """Key of the token inside the :attr:`section` in the
    :class:`~kivy.utils.ConfigParser` instance.

    :attr:`key` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.
    """

    value = ObjectProperty(None)
    """Value of the token according to the :class:`~kivy.utils.ConfigParser`
    instance. Any change to this value will trigger a
    :meth:`MDSettings.on_config_change` event.

    :attr:`value` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    """

    panel = ObjectProperty(None)
    """(internal) Reference to the MDSettingsPanel for this setting. You don't
    need to use it.

    :attr:`panel` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    """

    content = ObjectProperty(None)
    """(internal) Reference to the widget that contains the real setting.
    As soon as the content object is set, any further call to add_widget will
    call the content.add_widget. This is automatically set.

    :attr:`content` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    """

    icon = StringProperty("checkbox-blank-circle")

    def _open_dialog(self):
        pass

    def on_release(self):
        self._open_dialog()

    def add_widget(self, *args, **kwargs):
        if self.content is None:
            return super(MKVSettingItem, self).add_widget(*args, **kwargs)
        return self.content.add_widget(*args, **kwargs)


class MKVSettingBoolean(MKVSettingItem):
    values = ListProperty([0, 1])


class MKVSettingString(MKVSettingItem):
    """Implementation of a string setting on top of a :class:`MDSettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.textinput.Textinput` so the user can enter a custom
    value.
    """

    popup = ObjectProperty(None, allownone=True)
    """(internal) Used to store the current popup when it's shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    """

    textinput = ObjectProperty(None)
    """(internal) Used to store the current textinput from the popup and
    to listen for changes.

    :attr:`textinput` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    """

    def _dismiss(self, *largs):
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.text.strip()
        self.value = value

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation="vertical", spacing="5dp")
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            title=self.title,
            content=content,
            size_hint=(None, None),
            size=(popup_width, dp(250)),
        )

        # create the textinput used for numeric input
        self.textinput = textinput = TextInput(
            text=self.value,
            font_size=sp(24),
            multiline=False,
            size_hint_y=None,
            height=sp(42),
        )
        textinput.bind(on_text_validate=self._validate)
        self.textinput = textinput

        # construct the content, widget are used as a spacer
        content.add_widget(Widget())
        content.add_widget(textinput)
        content.add_widget(Widget())
        content.add_widget(MDDivider())

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        btn = Button(text="Ok")
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text="Cancel")
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup
        popup.open()


class MKVSettingInfo(MKVSettingItem):
    pass


class MKVSettingButton(MKVSettingItem):
    def __init__(self, **kwargs):
        super(MKVSettingItem, self).__init__(**kwargs)

    def on_release(self, *args):
        pass


class MKVSettingPath(MKVSettingItem):
    """Implementation of a Path setting on top of a :class:`MDSettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.filechooser.FileChooserListView` so the user can enter
    a custom value.

    .. versionadded:: 1.1.0
    """

    popup = ObjectProperty(None, allownone=True)
    """(internal) Used to store the current popup when it is shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    """

    textinput = ObjectProperty(None)
    """(internal) Used to store the current textinput from the popup and
    to listen for changes.

    :attr:`textinput` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    """

    show_hidden = BooleanProperty(False)
    """Whether to show 'hidden' filenames. What that means is
    operating-system-dependent.

    :attr:`show_hidden` is an :class:`~kivy.properties.BooleanProperty` and
    defaults to False.

    .. versionadded:: 1.10.0
    """

    dirselect = BooleanProperty(True)
    """Whether to allow selection of directories.

    :attr:`dirselect` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.

    .. versionadded:: 1.10.0
    """

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind("on_release", self._create_popup)

    def _dismiss(self, *largs):
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.selection

        if not value:
            return

        self.value = os.path.realpath(value[0])

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation="vertical", spacing=5)
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, 0.9), width=popup_width
        )

        # create the filechooser
        initial_path = self.value or os.getcwd()
        self.textinput = textinput = FileChooserListView(
            path=initial_path,
            size_hint=(1, 1),
            dirselect=self.dirselect,
            show_hidden=self.show_hidden,
        )
        textinput.bind(on_path=self._validate)

        # construct the content
        content.add_widget(textinput)
        content.add_widget(MDDivider())

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height="50dp", spacing="5dp")
        btn = Button(text="Ok")
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text="Cancel")
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()


class MKVSettingColor(MKVSettingItem):
    """Implementation of a color setting on top of a :class:`MDSettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget and a
    colored canvas rectangle that, when clicked, will open a
    :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.colorpicker.ColorPicker` so the user can choose a color.

    .. versionadded:: 2.0.1
    """

    popup = ObjectProperty(None, allownone=True)
    """(internal) Used to store the current popup when it's shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    """

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _dismiss(self, *largs):
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
        value = utils.get_hex_from_color(self.colorpicker.color)
        self.value = value

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation="vertical", spacing="5dp")
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, 0.9), width=popup_width
        )

        self.colorpicker = colorpicker = ColorPicker(
            color=utils.get_color_from_hex(self.value)
        )
        colorpicker.bind(on_color=self._validate)

        self.colorpicker = colorpicker
        content.add_widget(colorpicker)
        content.add_widget(MDDivider())

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height="50dp", spacing="5dp")
        btn = Button(text="Ok")
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text="Cancel")
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()


class MKVSettingNumeric(MKVSettingString):
    """Implementation of a numeric setting on top of a :class:`MDSettingString`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.textinput.Textinput` so the user can enter a custom
    value.
    """

    def _validate(self, instance):
        # we know the type just by checking if there is a '.' in the original
        # value
        is_float = "." in str(self.value)
        self._dismiss()
        try:
            if is_float:
                self.value = text_type(float(self.textinput.text))
            else:
                self.value = text_type(int(self.textinput.text))
        except ValueError:
            return


class MKVSettingOptions(MKVSettingItem):
    """Implementation of an option list on top of a :class:`MDSettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    list of options from which the user can select.
    """

    options = ListProperty([])
    """List of all availables options. This must be a list of "string" items.
    Otherwise, it will crash. :)

    :attr:`options` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].
    """

    popup = ObjectProperty(None, allownone=True)
    """(internal) Used to store the current popup when it is shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    """

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind("on_release", self._create_popup)

    def _set_option(self, instance):
        self.value = instance.text
        self.popup.dismiss()

    def _create_popup(self, instance):
        # create the popup
        content = BoxLayout(orientation="vertical", spacing="5dp")
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            content=content,
            title=self.title,
            size_hint=(None, None),
            size=(popup_width, "400dp"),
        )
        popup.height = len(self.options) * dp(55) + dp(150)

        # add all the options
        content.add_widget(Widget(size_hint_y=None, height=1))
        uid = str(self.uid)
        for option in self.options:
            state = "down" if option == self.value else "normal"
            btn = ToggleButton(text=option, state=state, group=uid)
            btn.bind(on_release=self._set_option)
            content.add_widget(btn)

        # finally, add a cancel button to return on the previous panel
        content.add_widget(MDDivider())
        btn = Button(text="Cancel", size_hint_y=None, height=dp(50))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)

        # and open the popup !
        popup.open()


class MKVSettingTitle(MDBoxLayout):
    """A simple title label, used to organize the settings in sections."""

    title = StringProperty()
    panel = ObjectProperty(None)


class MKVSettingsPanel(MDGridLayout):
    """This class is used to construct panel settings, for use with a
    :class:`MDSettings` instance or subclass.
    """

    title = StringProperty("Default title")
    """Title of the panel. The title will be reused by the :class:`MDSettings` in
    the sidebar.
    """

    config = ObjectProperty(None, allownone=True)
    """A :class:`kivy.utils.ConfigParser` instance. See module documentation
    for more information.
    """

    settings = ObjectProperty(None)
    """A :class:`MDSettings` instance that will be used to fire the
    `on_config_change` event.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("cols", 1)
        super(MKVSettingsPanel, self).__init__(**kwargs)

    def on_config(self, instance, value):
        if value is None:
            return
        if not isinstance(value, ConfigParser):
            raise Exception(
                "Invalid utils object, you must use a"
                "kivy.utils.ConfigParser, not another one !"
            )

    def get_value(self, key):
        return self.get_property_value_from_model(key)

    def set_value(self, key, value):
        self.controller.dispatch_to_model(**{key: value})
        print(f"Dispatched to model: {key=}, {value=}")


class MKVInterfaceWithSidebar(MDBoxLayout):
    """The default MDSettings interface class. It displays a sidebar menu
    with names of available settings panels, which may be used to switch
    which one is currently displayed.

    See :meth:`~MDInterfaceWithSidebar.add_panel` for information on the
    method you must implement if creating your own interface.

    This class also dispatches an event 'on_close', which is triggered
    when the sidebar menu's close button is released. If creating your
    own interface widget, it should also dispatch such an event which
    will automatically be caught by :class:`MDSettings` and used to
    trigger its own 'on_close' event.

    """

    menu = ObjectProperty()
    """(internal) A reference to the sidebar menu widget.

    :attr:`menu` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    """

    content = ObjectProperty()
    """(internal) A reference to the panel display widget (a
    :class:`ContentPanel`).

    :attr:`content` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    """

    __events__ = ("on_close",)

    def __init__(self, *args, **kwargs):
        super(MKVInterfaceWithSidebar, self).__init__(*args, **kwargs)
        if self.menu.close_button:
            self.menu.close_button.bind(on_release=lambda j: self.dispatch("on_close"))

    def add_panel(self, panel, name, uid):
        """This method is used by MDSettings to add new panels for possible
        display. Any replacement for ContentPanel *must* implement
        this method.

        :Parameters:
            `panel`: :class:`MDSettingsPanel`
                It should be stored and the interface should provide a way to
                switch between panels.
            `name`:
                The name of the panel as a string. It may be used to represent
                the panel but isn't necessarily unique.
            `uid`:
                A unique int identifying the panel. It should be used to
                identify and switch between panels.

        """
        self.menu.add_item(name, uid)
        self.content.add_panel(panel, name, uid)

    def on_close(self, *args):
        pass


# class MDInterfaceWithSpinner(MDBoxLayout):
#     """A settings interface that displays a spinner at the top for
#     switching between panels.
#
#     The workings of this class are considered internal and are not
#     documented. See :meth:`MDInterfaceWithSidebar` for
#     information on implementing your own interface class.
#
#     """
#
#     __events__ = ("on_close",)
#
#     menu = ObjectProperty()
#     """(internal) A reference to the sidebar menu widget.
#
#     :attr:`menu` is an :class:`~kivy.properties.ObjectProperty` and
#     defaults to None.
#     """
#
#     content = ObjectProperty()
#     """(internal) A reference to the panel display widget (a
#     :class:`ContentPanel`).
#
#     :attr:`menu` is an :class:`~kivy.properties.ObjectProperty` and
#     defaults to None.
#
#     """
#
#     def __init__(self, *args, **kwargs):
#         super(MDInterfaceWithSpinner, self).__init__(*args, **kwargs)
#         self.menu.close_button.bind(on_release=lambda j: self.dispatch("on_close"))
#
#     def add_panel(self, panel, name, uid):
#         """This method is used by MDSettings to add new panels for possible
#         display. Any replacement for ContentPanel *must* implement
#         this method.
#
#         :Parameters:
#             `panel`: :class:`MDSettingsPanel`
#                 It should be stored and the interface should provide a way to
#                 switch between panels.
#             `name`:
#                 The name of the panel as a string. It may be used to represent
#                 the panel but may not be unique.
#             `uid`:
#                 A unique int identifying the panel. It should be used to
#                 identify and switch between panels.
#
#         """
#         self.content.add_panel(panel, name, uid)
#         self.menu.add_item(name, uid)
#
#     def on_close(self, *args):
#         pass


class MKVContentPanel(MVCScrollView):
    """A class for displaying settings panels. It displays a single
    settings panel at a time, taking up the full size and shape of the
    ContentPanel. It is used by :class:`MDInterfaceWithSidebar` and
    :class:`MDInterfaceWithSpinner` to display settings.

    """

    panels = DictProperty({})
    """(internal) Stores a dictionary mapping settings panels to their uids.

    :attr:`panels` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.

    """

    container = ObjectProperty()
    """(internal) A reference to the GridLayout that contains the
    settings panel.

    :attr:`container` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    """

    current_panel = ObjectProperty(None)
    """(internal) A reference to the current settings panel.

    :attr:`current_panel` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    """

    current_uid = NumericProperty(0)
    """(internal) A reference to the uid of the current settings panel.

    :attr:`current_uid` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.

    """

    def __init__(self, *args, ignore_parent_mvc=True, **kwargs):
        super().__init__(*args, ignore_parent_mvc=ignore_parent_mvc, **kwargs)

    def add_panel(self, panel, name, uid):
        """This method is used by MDSettings to add new panels for possible
        display. Any replacement for ContentPanel *must* implement
        this method.

        :Parameters:
            `panel`: :class:`MDSettingsPanel`
                It should be stored and displayed when requested.
            `name`:
                The name of the panel as a string. It may be used to represent
                the panel.
            `uid`:
                A unique int identifying the panel. It should be stored and
                used to identify panels when switching.

        """
        self.panels[uid] = panel
        if not self.current_uid:
            self.current_uid = uid

    def on_current_uid(self, *args):
        """The uid of the currently displayed panel. Changing this will
        automatically change the displayed panel.

        :Parameters:
            `uid`:
                A panel uid. It should be used to retrieve and display
                a settings panel that has previously been added with
                :meth:`add_panel`.

        """
        uid = self.current_uid
        if uid in self.panels:
            if self.current_panel is not None:
                self.remove_widget(self.current_panel)
            new_panel = self.panels[uid]
            self.add_widget(new_panel)
            self.current_panel = new_panel
            return True
        return False  # New uid doesn't exist

    def add_widget(self, *args, **kwargs):
        if self.container is None:
            super(MKVContentPanel, self).add_widget(*args, **kwargs)
        else:
            self.container.add_widget(*args, **kwargs)

    def remove_widget(self, *args, **kwargs):
        self.container.remove_widget(*args, **kwargs)


class MKVSettings(MDBoxLayout):
    """MDSettings UI. Check module documentation for more information on how
    to use this class.

    :Events:
        `on_config_change`: ConfigParser instance, section, key, value
            Fired when the section's key-value pair of a ConfigParser changes.

            .. warning:

                value will be str/unicode type, regardless of the setting
                type (numeric, boolean, etc)
        `on_close`
            Fired by the default panel when the Close button is pressed.

    """

    interface = ObjectProperty(None)
    """(internal) Reference to the widget that will contain, organise and
    display the panel configuration panel uix.

    :attr:`interface` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    """

    interface_cls = ObjectProperty(MKVInterfaceWithSidebar)
    """The widget class that will be used to display the graphical
    interface for the settings panel. By default, it displays one MDSettings
    panel at a time with a sidebar to switch between them.

    :attr:`interface_cls` is an
    :class:`~kivy.properties.ObjectProperty` and defaults to
    :class:`MDInterfaceWithSidebar`.

    .. versionchanged:: 1.8.0
        If you set a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class.

    """

    NO_PROPERTY_CLASSES = [MKVSettingButton, MKVSettingTitle]

    def __init__(self, *args, **kwargs):
        self._types = {}
        self._items: dict[str, MKVSettingItem] = dict()
        super().__init__(**kwargs)
        self.add_interface()
        self.register_type("string", MKVSettingString)
        self.register_type("bool", MKVSettingBoolean)
        self.register_type("numeric", MKVSettingNumeric)
        self.register_type("options", MKVSettingOptions)
        self.register_type("path", MKVSettingPath)
        self.register_type("color", MKVSettingColor)
        self.register_type("info", MKVSettingInfo)

        self.register_type("title", MKVSettingTitle)
        self.register_type("button", MKVSettingButton)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            super().on_touch_down(touch)
            return True

    def register_type(self, tp, cls):
        """Register a new type that can be used in the JSON definition."""
        self._types[tp] = cls

    def add_interface(self):
        """(Internal) creates an instance of :attr:`MDSettings.interface_cls`,
        and sets it to :attr:`~MDSettings.interface`. When json panels are
        created, they will be added to this interface which will display them
        to the user.
        """
        cls = self.interface_cls
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        interface = cls()
        self.interface = interface
        self.add_widget(interface)
        self.interface.bind(on_close=lambda j: self.dispatch("on_close"))

    def create_panel(self, title: str, data: list) -> MKVSettingsPanel:
        """Create new :class:`MDSettingsPanel`"""

        panel = MKVSettingsPanel(title=title, settings=self)

        for setting in data:
            # determine the type and the class to use
            if "type" not in setting:
                print(setting)
                raise ValueError('One setting is missing the "type" element')
            ttype = setting["type"]
            cls = self._types.get(ttype)
            if cls is None:
                raise ValueError(
                    f'No class registered to handle the {setting["type"]} type'
                )

            # create an instance of the class, without the type attribute
            del setting["type"]

            debug_mode = False
            str_settings = {}

            for key, item in setting.items():

                if str(key) == "debug_only":
                    if debug_mode == item:
                        continue
                    else:
                        str_settings = None
                        break

                str_settings[str(key)] = item

            if str_settings is not None:
                instance = cls(panel=panel, **str_settings)
                panel.add_widget(instance)

                if str_settings.get("key", None):
                    self._items[str_settings["key"]]: MKVSettingItem = instance

        return panel

    def add_panel_to_interface(self, panel: MKVSettingsPanel) -> None:
        self.interface.add_panel(panel, panel.title, panel.uid)

    def create_and_add_panel_to_interface(self, title: str, data: list):
        self.add_panel_to_interface(self.create_panel(title, data))

    def disable_item(self, key: str):
        self._items[key].disabled = True

    def enable_item(self, key: str):
        self._items[key].disabled = False

    def bind_all(self, model):
        for key, instance in self._items.items():
            if instance.__class__ not in self.NO_PROPERTY_CLASSES:
                self.bind_property_to_model(
                    prop_name="value", model_prop_name=key, prop_source=instance
                )
                print(f'Bind: "value"\tModel: {key}\tInstance: {instance}')

    def init_all(self, controller):
        for key, instance in self._items.items():
            if instance.__class__ not in self.NO_PROPERTY_CLASSES:
                instance.value = self.get_property_value_from_model(key)
                print(f"Init: {instance}\tValue: {instance.value}")


class MKVSettingsWithSidebar(MKVSettings):
    pass


# class MDSettingsWithSpinner(MDSettings):
#     """A settings widget that displays one settings panel at a time with a
#     spinner at the top to switch between them.
#
#     """
#
#     def __init__(self, *args, **kwargs):
#         self.interface_cls = MDInterfaceWithSpinner
#         super(MDSettingsWithSpinner, self).__init__(*args, **kwargs)


# class MDSettingsWithTabbedPanel(MDSettings):
#     """A settings widget that displays settings panels as pages in a
#     :class:`~kivy.uix.tabbedpanel.TabbedPanel`.
#     """
#
#     __events__ = ("on_close",)
#
#     def __init__(self, *args, **kwargs):
#         self.interface_cls = MDInterfaceWithTabbedPanel
#         super(MDSettingsWithTabbedPanel, self).__init__(*args, **kwargs)
#
#     def on_close(self, *args):
#         pass


class MKVSettingsWithNoMenu(MKVSettings):
    """A settings widget that displays a single settings panel with *no*
    Close button. It will not accept more than one MDSettings panel. It
    is intended for use in programs with few enough settings that a
    full panel switcher is not useful.

    .. warning::

        This MDSettings panel does *not* provide a Close
        button, and so it is impossible to leave the settings screen
        unless you also add other behavior or override
        :meth:`~kivy.app.App.display_settings` and
        :meth:`~kivy.app.App.close_settings`.

    """

    def __init__(self, *args, **kwargs):
        self.interface_cls = MKVInterfaceWithNoMenu
        super(MKVSettingsWithNoMenu, self).__init__(*args, **kwargs)


class MKVInterfaceWithNoMenu(MKVContentPanel):
    """The interface widget used by :class:`MDSettingsWithNoMenu`. It
    stores and displays a single settings panel.

    This widget is considered internal and is not documented. See the
    :class:`ContentPanel` for information on defining your own content
    widget.

    """

    def add_widget(self, *args, **kwargs):
        if self.container is not None and len(self.container.children) > 0:
            raise Exception("ContentNoMenu cannot accept more than one settings panel")
        super(MKVInterfaceWithNoMenu, self).add_widget(*args, **kwargs)


# class MDInterfaceWithTabbedPanel(MDFloatLayout):
#     """The content widget used by :class:`MDSettingsWithTabbedPanel`. It
#     stores and displays MDSettings panels in tabs of a TabbedPanel.
#
#     This widget is considered internal and is not documented. See
#     :class:`MDInterfaceWithSidebar` for information on defining your own
#     interface widget.
#
#     """
#
#     tabbedpanel = ObjectProperty()
#     close_button = ObjectProperty()
#
#     __events__ = ("on_close",)
#
#     def __init__(self, *args, **kwargs):
#         super(MDInterfaceWithTabbedPanel, self).__init__(**kwargs)
#         self.close_button.bind(on_release=lambda j: self.dispatch("on_close"))
#
#     def add_panel(self, panel, name, uid):
#         scrollview = MVCScrollView()
#         scrollview.add_widget(panel)
#         if not self.tabbedpanel.default_tab_content:
#             self.tabbedpanel.default_tab_text = name
#             self.tabbedpanel.default_tab_content = scrollview
#         else:
#             panelitem = TabbedPanelHeader(text=name, content=scrollview)
#             self.tabbedpanel.add_widget(panelitem)
#
#     def on_close(self, *args):
#         pass


# class MDMenuSpinner(MDBoxLayout):
#     """The menu class used by :class:`MDSettingsWithSpinner`. It provides a
#     sidebar with an entry for each settings panel.
#
#     This widget is considered internal and is not documented. See
#     :class:`MenuSidebar` for information on menus and creating your own menu
#     class.
#
#     """
#
#     selected_uid = NumericProperty(0)
#     close_button = ObjectProperty(0)
#     spinner = ObjectProperty()
#     panel_names = DictProperty({})
#     spinner_text = StringProperty()
#
#     def add_item(self, name, uid):
#         values = self.spinner.values
#         if name in values:
#             i = 2
#             while name + " {}".format(i) in values:
#                 i += 1
#             name = name + " {}".format(i)
#         self.panel_names[name] = uid
#         self.spinner.values.append(name)
#         if not self.spinner.text:
#             self.spinner.text = name
#
#     def on_spinner_text(self, *args):
#         text = self.spinner_text
#         self.selected_uid = self.panel_names[text]


class MKVMenuSidebar(MDFloatLayout):
    """The menu used by :class:`MDInterfaceWithSidebar`. It provides a
    sidebar with an entry for each settings panel, which the user may
    click to select.

    """

    selected_uid = NumericProperty(0)
    """The uid of the currently selected panel. This may be used to switch
    between displayed panels, e.g. by binding it to the
    :attr:`~ContentPanel.current_uid` of a :class:`ContentPanel`.

    :attr:`selected_uid` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.

    """

    buttons_layout = ObjectProperty(None)
    """(internal) Reference to the GridLayout that contains individual
    settings panel menu buttons.

    :attr:`buttons_layout` is an
    :class:`~kivy.properties.ObjectProperty` and defaults to None.

    """

    close_button = ObjectProperty(None)
    """(internal) Reference to the widget's Close button.

    :attr:`buttons_layout` is an
    :class:`~kivy.properties.ObjectProperty` and defaults to None.

    """

    def add_item(self, name, uid):
        """This method is used to add new panels to the menu.

        :Parameters:
            `name`:
                The name (a string) of the panel. It should be used
                to represent the panel in the menu.
            `uid`:
                The name (an int) of the panel. It should be used internally
                to represent the panel and used to set self.selected_uid when
                the panel is changed.

        """

        label = MKVSettingSidebarLabel(text=name, uid=uid, menu=self)
        if self.buttons_layout and len(self.buttons_layout.children) == 0:
            label.selected = True
        if self.buttons_layout is not None:
            self.buttons_layout.add_widget(label)

    def on_selected_uid(self, *args):
        """(internal) unselects any currently selected menu buttons, unless
        they represent the current panel.

        """
        for button in self.buttons_layout.children:
            if button.uid != self.selected_uid:
                button.selected = False


class MKVSettingSidebarLabel(MDLabel):
    # Internal class, not documented.
    selected = BooleanProperty(False)
    uid = NumericProperty(0)
    menu = ObjectProperty(None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        self.selected = True
        self.menu.selected_uid = self.uid


# class MDSettingsCloseButton(MDIconButton, CommonElevationBehavior):
#     def on_enter(self):
#         super().on_enter()
#         self.md_bg_color = "grey"
#         self.icon_color = "black"
#
#     def on_leave(self):
#         super().on_leave()
#         self.md_bg_color = "black"
#         self.icon_color = "white"


# Диалоги (визуал — в .kv)


class StringValueDialog(MKVDialog):
    title = StringProperty("")
    initial = StringProperty("")
    target_item = ObjectProperty(None)

    def on_ok(self):
        text = self.content_cls.ids.input.text
        self.target_item.value = text
        self.dismiss()


class OptionsValueDialog(MKVDialog):
    title = StringProperty("")
    options = ListProperty([])
    target_item = ObjectProperty(None)

    def on_open(self, *args):
        # заполняем список вариантов программно (убрали on_open из kv)
        from kivymd.uix.list import MDListItem, MDListItemHeadlineText

        opts = getattr(self.content_cls.ids, "opts", None)
        if not opts:
            return
        opts.clear_widgets()

        # создаём элементы списка и биндим выбор
        for text in self.options or []:
            item = MDListItem()
            item.add_widget(MDListItemHeadlineText(text=text))
            # захватываем текущее значение text через аргумент по умолчанию
            item.bind(on_release=lambda _i, t=text: self.select(t))
            opts.add_widget(item)

    def select(self, text: str):
        self.target_item.value = text
        self.dismiss()


class PathValueDialog(MKVDialog):
    title = StringProperty("")
    initial = StringProperty("")
    dirselect = BooleanProperty(True)
    show_hidden = BooleanProperty(False)
    target_item = ObjectProperty(None)

    def on_accept_path(self, path: str):
        self.target_item.value = path
        self.dismiss()


class ColorValueDialog(MKVDialog):
    title = StringProperty("")
    initial = StringProperty("")
    target_item = ObjectProperty(None)

    def on_color(self, rgba):
        from kivy.utils import get_hex_from_color

        self.target_item.value = get_hex_from_color(rgba)
        self.dismiss()
