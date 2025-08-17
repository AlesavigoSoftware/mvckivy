from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.properties import ObjectProperty, Property
from kivy.uix.widget import Widget
from kivymd.app import MDApp

if TYPE_CHECKING:
    from mvckivy.app import MVCApp
    from mvckivy.base_mvc import BaseModel, BaseScreen, BaseController


class ParentClassUnsupported(Exception):
    pass


class MVCWidget(Widget):
    model: ObjectProperty[BaseModel] = ObjectProperty(None, allownone=True)
    controller: ObjectProperty[BaseController] = ObjectProperty(None, allownone=True)
    screen: ObjectProperty[BaseScreen] = ObjectProperty(None, allownone=True)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.app: MVCApp = MDApp.get_running_app()


class MVCBehavior(MVCWidget):
    def __init__(self, *args, ignore_parent_mvc: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._ignore_parent_mvc = ignore_parent_mvc
        self._set_mvc_attrs_from_parent()
        Clock.schedule_once(lambda dt: self._bind_all(), 0)
        Clock.schedule_once(lambda dt: self._init_all(), 0)

    def on_parent(self, widget, parent):
        with suppress(AttributeError):
            super().on_parent(widget, parent)

        self._set_mvc_attrs_from_parent()

    def _set_mvc_attrs_from_parent(self) -> None:
        """
        Sets MVC attributes from the parent widget if they are not already set.

        This method checks whether a parent widget exists and if it implements the MVCWidget interface.
        If the parent exists and is an instance of MVCWidget, then the current object's attributes
        (model, view, controller, and screen) are assigned the corresponding values from the parent,
        but only if they are not already defined.

        Raises
        ------
        ParentClassUnsupported
            If the parent object exists but does not implement the MVCWidget interface.
        """
        if not self._ignore_parent_mvc:
            parent = self.parent

            if parent:

                if not isinstance(parent, MVCWidget):
                    raise ParentClassUnsupported(
                        f'Parent class "{parent}" must implement MVCWidget class. Called from: {self}'
                    )

                if not self.model and parent.model:
                    self.model = parent.model

                if not self.controller and parent.controller:
                    self.controller = parent.controller

                if not self.screen and parent.screen:
                    self.screen = parent.screen

    def bind_property_to_model(
        self,
        prop_name: str,
        custom_model: EventDispatcher | None = None,
        model_prop_name: str | None = None,
        prop_source: EventDispatcher | None = None,
    ) -> None:
        """
        Binds a widget property to a property of the model.

        This method binds a specified widget property to a corresponding property in the model.
        If any of the parameters (custom_model, model_prop_name, or prop_source) are not provided,
        default values are used (i.e., self.model for the model, and prop_name for the model property).

        Parameters
        ----------
        prop_name : str
            The name of the widget property to bind.
        custom_model : EventDispatcher | None, optional
            The model object to bind to. If not provided, defaults to self.model.
        model_prop_name : str | None, optional
            The name of the property in the model to bind to. If not provided, defaults to prop_name.
        prop_source : EventDispatcher | None, optional
            The source object from which the setter method is retrieved. If not provided, defaults to the current object.

        Returns
        -------
        None
        """
        if not custom_model:
            custom_model = self.model

        if not model_prop_name:
            model_prop_name = prop_name

        if not prop_source:
            prop_source = self

        custom_model.bind(**{model_prop_name: prop_source.setter(prop_name)})

    def bind_to_model(
        self, custom_model: EventDispatcher | None = None, **kwargs
    ) -> None:
        """
        Binds one or more properties to the model.

        This method binds one or more properties to the model by passing the provided keyword arguments
        to the model's bind method. It ensures that if a custom model is not provided, the default self.model
        is used.

        Parameters
        ----------
        custom_model : EventDispatcher | None, optional
            The model object to bind to. If not provided, defaults to self.model.
        **kwargs
            Keyword arguments representing the property names and corresponding callback functions for binding.

        Returns
        -------
        None
        """
        if not custom_model:
            custom_model = self.model

        custom_model.bind(**kwargs)

    def get_property_from_model(
        self, property_name: str, custom_model: EventDispatcher | None = None
    ) -> Property:
        """
        Retrieves a property object from the model.

        This method returns the Property object associated with the given property name
        from the specified model. If no model is provided, it defaults to using self.model.

        Parameters
        ----------
        property_name : str
            The name of the property to retrieve from the model.
        custom_model : EventDispatcher | None, optional
            The model from which to retrieve the property. If not provided, defaults to self.model.

        Returns
        -------
        Property
            The Property object corresponding to the requested property name.
        """
        if not custom_model:
            custom_model = self.model

        return custom_model.property(property_name)

    def _bind_all(self) -> None:
        """
        Calls by Clock.schedule_once on app start before _init_all
        :return: None
        """

    def _init_all(self) -> None:
        """
        Calls by Clock.schedule_once on app start after _bind_all
        :return: None
        """
