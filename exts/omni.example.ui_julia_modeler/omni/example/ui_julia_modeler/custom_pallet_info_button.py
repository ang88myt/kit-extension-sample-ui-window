__all__ = ["CustomPalletInfoWidget"]

from typing import Callable, Optional
import omni.ui as ui
from .style import ATTR_LABEL_WIDTH, BLOCK_HEIGHT

class CustomPalletInfoWidget:
    """A compound widget for gathering pallet info in a StringField and a button to execute a callback"""

    def __init__(self, label: str, btn_callback: Optional[Callable] = None):
        self.__label = label
        self.__input_field: Optional[ui.StringField] = None
        self.__btn: Optional[ui.Button] = None
        self.__frame = ui.Frame()
        self.__btn_callback = btn_callback

        with self.__frame:
            self._build_fn()

    def destroy(self):
        """Destroys the widget's children components"""
        self.__input_field = None
        self.__btn = None
        self.__frame = None

    @property
    def model(self) -> Optional[ui.AbstractItem]:
        """The widget's model"""
        if self.__input_field:
            return self.__input_field.model
        return None

    @model.setter
    def model(self, value: ui.AbstractItem):
        """The widget's model setter"""
        if self.__input_field:
            self.__input_field.model = value

    def get_input_value(self) -> str:
        """Returns the value typed in the StringField box"""
        if self.__input_field and self.__input_field.model:
            return self.__input_field.model.get_value_as_string()
        return ""

    def _button_callback(self):
        """Callback wrapper for the button press to use the provided callback"""
        if self.__btn_callback:
            self.__btn_callback()

    def _build_fn(self):
        """Draw all of the widget parts and set up the button callback."""
        with ui.HStack():
            ui.Label(
                self.__label,
                name="attribute_name",
                width=ATTR_LABEL_WIDTH
            )

            self.__input_field = ui.StringField(
                name="input_field",
                height=BLOCK_HEIGHT,
                width=ui.Fraction(2),
            )

            self.__btn = ui.Button(
                "Search",
                name="tool_button",
                height=BLOCK_HEIGHT,
                width=ui.Fraction(1),
                clicked_fn=self._button_callback,
            )
