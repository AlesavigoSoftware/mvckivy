import os
import sys
from pathlib import Path

# run in debug mode to avoid headless window requirements
os.environ["MVCKIVY_DEBUG_MODE"] = "1"

# allow importing the demo module
sys.path.append(str(Path(__file__).resolve().parent))
from swap_card_test.main import DemoApp


def test_transport_dropdown_updates_text():
    app = DemoApp()
    root = app.build()
    assert root.transport == "Квадрокоптер"
    root._set_transport("Ровер")
    assert root.transport == "Ровер"
    assert root.ids.transport_text.text == "Ровер"
