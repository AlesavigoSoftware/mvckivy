from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from mvckivy.properties.extended_alias_property import ExtendedAliasProperty

KV = """
<Separator@Widget>:
    size_hint_y: None
    height: "1dp"
    canvas:
        Color:
            rgba: .6,.6,.6,1
        Rectangle:
            pos: self.pos
            size: self.size

<Root>:
    orientation: "vertical"
    spacing: "8dp"
    padding: "8dp"

    BoxLayout:
        size_hint_y: None
        height: "40dp"
        spacing: "8dp"
        Button:
            text: "Label A: +"
            on_release: root.label_a.text = root.label_a.text + "A" if root.label_a else ""
        Button:
            text: "Label B: +"
            on_release: root.label_b.text = root.label_b.text + "B" if root.label_b else ""
        Button:
            text: "Switch to A"
            on_release: root.current_label = root.label_a
        Button:
            text: "Switch to B"
            on_release: root.current_label = root.label_b

    BoxLayout:
        size_hint_y: None
        height: "36dp"
        spacing: "8dp"
        Label:
            text: "Label A:"
        Label:
            id: la
            text: "Hello"
        Label:
            text: "Label B:"
        Label:
            id: lb
            text: "World"

    Separator:

    BoxLayout:
        size_hint_y: None
        height: "36dp"
        spacing: "8dp"
        Label:
            text: "current_label ->"
        Label:
            text: "A" if root.current_label is root.label_a else ("B" if root.current_label is root.label_b else "None")

    BoxLayout:
        size_hint_y: None
        height: "48dp"
        spacing: "8dp"
        Label:
            text: "mirror_text (alias of current_label.text):"
        Label:
            text: root.mirror_text
"""


class Root(BoxLayout):
    label_a = ObjectProperty(allownone=True, rebind=True)
    label_b = ObjectProperty(allownone=True, rebind=True)
    current_label = ObjectProperty(allownone=True, rebind=True)

    def _get_mirror(self, ext: ExtendedAliasProperty):
        lbl = self.current_label
        return "" if lbl is None else getattr(lbl, "text", "")

    def _set_mirror(self, value, ext: ExtendedAliasProperty):
        lbl = self.current_label
        if lbl is None:
            return False
        lbl.text = value
        return None

    mirror_text = ExtendedAliasProperty(
        _get_mirror,
        _set_mirror,
        bind=("current_label.text",),
        cache=False,
        watch_before_use=True,
        respect_rebind_flag=True,
    )

    def on_kv_post(self, *args):
        self.label_a = self.ids.la
        self.label_b = self.ids.lb
        self.current_label = self.label_a


class DemoApp(App):
    def build(self):
        Builder.load_string(KV)
        return Root()


if __name__ == "__main__":
    DemoApp().run()
