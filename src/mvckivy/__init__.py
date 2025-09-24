import logging
from mvckivy.utils.config_reader import ConfigReader
from kivy.factory import Factory


logger = logging.getLogger("mvckivy")
logger.setLevel(logging.DEBUG if ConfigReader.get_debug_mode() else logging.INFO)


register = Factory.register
register("MVCGridLayout", module="mvckivy.uix.layout")
register("MVCRelativeLayout", module="mvckivy.uix.layout")
register("MVCBoxLayout", module="mvckivy.uix.layout")
register("MVCAnchorLayout", module="mvckivy.uix.layout")
register("MVCFloatLayout", module="mvckivy.uix.layout")
register("MVCStackLayout", module="mvckivy.uix.layout")

register("MKVSettings", module="mvckivy.uix.settings")

register("MKVDialog", module="mvckivy.uix.dialog")
register("MKVDialogScrim", module="mvckivy.uix.dialog")
register("MKVDialogIcon", module="mvckivy.uix.dialog")
register("MKVDialogHeadlineText", module="mvckivy.uix.dialog")
register("MKVDialogSupportingText", module="mvckivy.uix.dialog")
register("MKVDialogContentContainer", module="mvckivy.uix.dialog")
register("MKVDialogButtonContainer", module="mvckivy.uix.dialog")

register("MKVTabsPrimary", module="mvckivy.uix.tabs")
register("MKVTabsSecondary", module="mvckivy.uix.tabs")
register("MKVTabsItem", module="mvckivy.uix.tabs")
register("MKVTabsItemSecondary", module="mvckivy.uix.tabs")
register("MKVTabsItemIcon", module="mvckivy.uix.tabs")
register("MKVTabsItemText", module="mvckivy.uix.tabs")
register("MKVTabsCarousel", module="mvckivy.uix.tabs")
register("MKVTabsBadge", module="mvckivy.uix.tabs")

register("AutoResizeMDIconButton", module="mvckivy.uix.button")
