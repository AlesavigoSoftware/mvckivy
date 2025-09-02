from kivy.properties import ObjectProperty, ColorProperty, StringProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.label import MDIcon
from kivymd_extensions.akivymd.uix.behaviors.labelanimation import AKAnimationIconBehavior

from .label import AutoResizeLabel


class MDIconRemake(MDLabel):
    """
    Icon class.

    For more information, see in the
    :class:`~MDLabel` class documentation.
    """

    icon = StringProperty("blank")
    """
    Label icon name.

    :attr:`icon` is an :class:`~kivy.properties.StringProperty`
    and defaults to `'blank'`.
    """

    source = StringProperty(None, allownone=True)
    """
    Path to icon.

    :attr:`source` is an :class:`~kivy.properties.StringProperty`
    and defaults to `None`.
    """

    icon_color = ColorProperty(None)
    """
    Icon color in (r, g, b, a) or string format.

    .. versionadded:: 2.0.0

    :attr:`icon_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    icon_color_disabled = ColorProperty(None)
    """
    The icon color in (r, g, b, a) or string format of the button when
    the button is disabled.

    .. versionadded:: 2.0.0

    :attr:`icon_color_disabled` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    # kivymd.uix.badge.badge.MDBadge object.
    _badge = ObjectProperty()

    def add_widget(self, widget, index=0, canvas=None):
        from kivymd.uix.badge import MDBadge

        if isinstance(widget, MDBadge):
            self._badge = widget
            return super().add_widget(widget)


class AutoResizeIcon(AutoResizeLabel):
    """
    Icon class.

    For more information, see in the
    :class:`~MDLabel` class documentation.
    """

    icon = StringProperty("blank")
    """
    Label icon name.

    :attr:`icon` is an :class:`~kivy.properties.StringProperty`
    and defaults to `'blank'`.
    """

    source = StringProperty(None, allownone=True)
    """
    Path to icon.

    :attr:`source` is an :class:`~kivy.properties.StringProperty`
    and defaults to `None`.
    """

    icon_color = ColorProperty(None)
    """
    Icon color in (r, g, b, a) or string format.

    .. versionadded:: 2.0.0

    :attr:`icon_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    icon_color_disabled = ColorProperty(None)
    """
    The icon color in (r, g, b, a) or string format of the button when
    the button is disabled.

    .. versionadded:: 2.0.0

    :attr:`icon_color_disabled` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    # kivymd.uix.badge.badge.MDBadge object.
    _badge = ObjectProperty()

    def add_widget(self, widget, index=0, canvas=None):
        from kivymd.uix.badge import MDBadge

        if isinstance(widget, MDBadge):
            self._badge = widget
            return super().add_widget(widget)


class RotationAnimatedIcon(MDIcon, AKAnimationIconBehavior):
    pass
