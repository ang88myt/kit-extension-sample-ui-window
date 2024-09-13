__all__ = ["CustomButtonWidget"]

from typing import Callable
import omni.ui as ui
from .style import BLOCK_HEIGHT

class CustomButtonWidget:
    """A widget that displays a button and can trigger a callback function."""

    def __init__(self, btn_label: str, btn_callback: Callable):
        self.__btn_label = btn_label
        self.__btn = None
        self.__callback = btn_callback
        self.__frame = ui.Frame()

        with self.__frame:
            self._build_fn()

    def destroy(self):
        """Clean up references to UI components to ensure proper garbage collection."""
        self.__btn = None
        self.__callback = None
        self.__frame.destroy()
        self.__frame = None

    def display_expiry(self):
        """This method can be called from outside to trigger the expiry display logic."""
        # Implement the logic for displaying expiry information here.
        print("Displaying expiry information...")
        # Add any additional logic here.

    def _build_fn(self):
        """Draw the widget parts and set up the callback."""
        with ui.HStack():
            # Create the button
            self.__btn = ui.Button(
                name="tool_button",
                text=self.__btn_label,
                height=BLOCK_HEIGHT,
                width=ui.Fraction(1),
                clicked_fn=self.__callback
            )
