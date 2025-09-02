from typing import TypeVar, List, Union, Type

from kivy.uix.widget import Widget

from utility.constants import MAX_VEHICLES_COUNT


class MultiVehicleContainerMixin(Widget):
    def add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, MultiVehicleWidget):
            for _widget in widget:
                super().add_widget(_widget, index=index, canvas=canvas)
        else:
            super().add_widget(widget, index=index, canvas=canvas)

    def remove_widget(self, widget):
        if isinstance(widget, MultiVehicleWidget):
            for _widget in widget:
                super().remove_widget(_widget)
        else:
            super().remove_widget(widget)


class WrongOptionsCountException(Exception):
    pass


class MultiVehicleWidget(list):
    T = TypeVar("T", bound=Widget)

    def __init__(
            self,
            widget_cls: Type[T],
            count_of_widgets: int = MAX_VEHICLES_COUNT,
            options: Union[dict, List[dict], None] = None,
    ):
        if isinstance(options, dict):
            super().__init__(
                [
                    widget_cls(**options) for _ in range(count_of_widgets)
                ]
            )

        elif isinstance(options, List):
            if len(options) != MAX_VEHICLES_COUNT:
                raise WrongOptionsCountException(f'Expected: {MAX_VEHICLES_COUNT}, got: {len(options)}')

            super().__init__(
                [
                    widget_cls(**kwargs) for kwargs in options
                ]
            )

        else:
            super().__init__(
                [
                    widget_cls() for _ in range(count_of_widgets)
                ]
            )
