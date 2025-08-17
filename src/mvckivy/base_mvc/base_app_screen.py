from typing import Protocol

from kivy.metrics import dp

from mvckivy.base_mvc import BaseScreen


class ModalManagerProtocol(Protocol):
    def open(self, *args, **kwargs) -> None:
        """Open the modal dialog."""

    def close(self, *args, **kwargs) -> None:
        """Close the modal dialog."""

    def create(self, *args, **kwargs) -> None:
        """Create the modal dialog."""


class NotificationManager(ModalManagerProtocol):
    pass
    # def create_and_open_notification(
    #         self,
    #         text: str,
    #         supporting_text: str,
    #         notification_type: str,
    #         button_name: str | None = None,
    #         button_cb: Callable[[MDSnackbarActionButton], None] | None = None,
    # ) -> Notification:
    #
    #     if notification_type == "info":
    #         notification_cls = InfoNotification
    #     elif notification_type == "failure":
    #         notification_cls = FailureNotification
    #     elif notification_type == "error":
    #         notification_cls = ErrorNotification
    #     elif notification_type == "success":
    #         notification_cls = SuccessNotification
    #     else:
    #         raise WrongNotificationTypeException(
    #             f"Type not allowed: {notification_type}. It must be in ['info', 'failure', 'error', 'success']"
    #         )
    #
    #     buttons_container = MDSnackbarButtonContainer(pos_hint={"center_y": 0.5})
    #
    #     if button_name and button_cb:
    #         buttons_container.add_widget(
    #             MDSnackbarActionButton(
    #                 MDSnackbarActionButtonText(text=button_name, on_release=button_cb),
    #             ),
    #         )
    #
    #     buttons_container.add_widget(
    #         MDSnackbarCloseButton(
    #             icon="close",
    #         ),
    #     )
    #
    #     notification = notification_cls(
    #         MDSnackbarText(
    #             text=text,
    #         ),
    #         MDSnackbarSupportingText(
    #             text=supporting_text,
    #         ),
    #         buttons_container,
    #         y=Window.height - dp(100),
    #         orientation="horizontal",
    #         pos_hint={"center_x": 0.5},
    #         size_hint_x=0.5,
    #         size_hint_max_x=dp(700),
    #         text=text,
    #         supporting_text=supporting_text,
    #         notification_type=notification_type,
    #         button_name=button_name,
    #         button_cb=button_cb,
    #     )
    #     notification.open()
    #     return notification


class DialogManager(ModalManagerProtocol):
    def create_and_open_dialog(
        self, dialog_cls, model=None, view=None, screen=None, controller=None, app=None
    ):
        dialog = dialog_cls(
            model=model,
            controller=controller,
            screen=screen,
            ignore_parent_mvc=True,
        )
        dialog.open()
        return dialog


class DrawerManager(ModalManagerProtocol):
    pass
    # def refill_and_open_side_menu(self, content_cls: Type[Widget]) -> None:
    #     self.side_menu.clear_widgets()
    #     self.side_menu.add_widget(content_cls())
    #     self.side_menu.set_state("open")


class DropdownManager(ModalManagerProtocol):
    pass
    # def create_and_open_dropdown(
    #     self,
    #     content: Union[list[dict], Callable[..., list[dict]]],
    #     caller: Widget,
    #     header: Widget = None,
    #     **kwargs,
    # ) -> AdaptiveMDDropdownMenu:
    #     menu = AdaptiveMDDropdownMenu(
    #         items=self._create_adaptive_menu_items(content),
    #         caller=caller,
    #         header_cls=header,
    #         target_width=dp(240),
    #         item_height=dp(48),
    #         **kwargs,  # important! contains max_height
    #     )
    #
    #     Clock.schedule_once(lambda dt: menu.open(), 0.1)
    #     return menu


class BaseAppScreen(BaseScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notification_manager: NotificationManager = (
            self.create_notification_manager()
        )
        self.dialog_manager: DialogManager = self.create_dialog_manager()
        self.drawer_manager: DrawerManager = self.create_drawer_manager()

    def create_notification_manager(self) -> NotificationManager:
        """
        Creates and returns a NotificationManager instance.
        This method can be overridden in subclasses to provide custom notification management.
        """
        return NotificationManager()

    def create_dialog_manager(self) -> DialogManager:
        """
        Creates and returns a DialogManager instance.
        This method can be overridden in subclasses to provide custom dialog management.
        """
        return DialogManager()

    def create_drawer_manager(self) -> DrawerManager:
        """
        Creates and returns a DrawerManager instance.
        This method can be overridden in subclasses to provide custom drawer management.
        """
        return DrawerManager()

    def create_and_open_notification(self, *args, **kwargs) -> None:
        return self.notification_manager.create(*args, **kwargs)

    def create_and_open_dialog(self, *args, **kwargs):
        return self.dialog_manager.create(*args, **kwargs)

    def create_drawer_dialog(self, *args, **kwargs):
        return self.drawer_manager.create(*args, **kwargs)

    def create_modal(self, modal_type: str, *args, **kwargs):
        """
        Creates and returns a modal dialog based on the type.
        This method can be overridden in subclasses to provide custom modal management.
        """
        if modal_type == "notification":
            return self.create_and_open_notification(*args, **kwargs)
        elif modal_type == "dialog":
            return self.create_and_open_dialog(*args, **kwargs)
        elif modal_type == "drawer":
            return self.create_drawer_dialog(*args, **kwargs)
        else:
            raise ValueError(f"Unknown modal type: {modal_type}")

    def on_size(self, instance, size: list) -> None:
        device_type = self._choose_current_device_type(
            window_width=size[0],
            window_height=size[1],
            orientation=self.model.device_orientation,
        )
        self.controller.dispatch_to_model(device_type=device_type, force_dispatch=True)

    @staticmethod
    def _choose_current_device_type(
        window_width: float, window_height: float, orientation: str
    ) -> str:
        if orientation == "portrait":

            if window_width <= dp(400) and window_height <= dp(800):
                return "mobile"
            elif window_width <= dp(700) and window_height <= dp(1200):
                return "tablet"
            else:
                return "desktop"

        elif orientation == "landscape":

            if window_height <= dp(400) and window_width <= dp(800):
                return "mobile"
            elif window_height <= dp(700) and window_width <= dp(1200):
                return "tablet"
            else:
                return "desktop"
