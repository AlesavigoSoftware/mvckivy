import logging
from mvckivy.utils.config_reader import ConfigReader
from kivy.factory import Factory


logger = logging.getLogger("mvckivy")
logger.setLevel(logging.DEBUG if ConfigReader.get_debug_mode() else logging.INFO)


register = Factory.register
register("MDAdaptiveDialog", module="mvckivy.uix.dialog")
register("MDAdaptiveDialogScrim", module="mvckivy.uix.dialog")
register("MDAdaptiveDialogIcon", module="mvckivy.uix.dialog")
register("MDAdaptiveDialogHeadlineText", module="mvckivy.uix.dialog")
register("MDAdaptiveDialogSupportingText", module="mvckivy.uix.dialog")
register("MDAdaptiveDialogContentContainer", module="mvckivy.uix.dialog")
register("MDAdaptiveDialogButtonContainer", module="mvckivy.uix.dialog")
register("MDSettings", module="mvckivy.uix.settings")
register("MVCGridLayout", module="mvckivy.uix.layouts")
register("MVCRelativeLayout", module="mvckivy.uix.layouts")
register("MVCBoxLayout", module="mvckivy.uix.layouts")
register("MVCAnchorLayout", module="mvckivy.uix.layouts")
register("MVCFloatLayout", module="mvckivy.uix.layouts")
register("MVCStackLayout", module="mvckivy.uix.layouts")
