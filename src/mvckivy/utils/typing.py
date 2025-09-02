from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from mvckivy.app.screen_registrator import MVCTrio, ScreenRegistrator
    from mvckivy.app.screens_schema import ScreensSchema
    from mvckivy.base_mvc import BaseScreen, BaseController, BaseModel


T_M = TypeVar("T_M", bound="BaseModel", covariant=True)
T_C = TypeVar("T_C", bound="BaseController", covariant=True)
T_S = TypeVar("T_S", bound="BaseScreen", covariant=True)

T_Trio = TypeVar('T_Trio', bound="MVCTrio", covariant=True)
T_SS = TypeVar('T_SS', bound="ScreensSchema")
T_SR = TypeVar('T_SR', bound="ScreenRegistrator")
