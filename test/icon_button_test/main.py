from kivy.lang import Builder
from kivy.clock import Clock
from mvckivy.app import MKVApp
from mvckivy.utils.builder import MVCBuilder

KV = """
MDScreen:
    md_bg_color: app.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(16)
        padding: dp(24)

        MDBoxLayout:
            adaptive_height: True
            spacing: dp(16)

            # different styles
            AutoResizeMDIconButton:
                id: btn_standard
                style: "standard"
                icon: "account-circle"

            AutoResizeMDIconButton:
                id: btn_filled
                style: "filled"
                icon: "account-circle"

            AutoResizeMDIconButton:
                id: btn_tonal
                style: "tonal"
                icon: "account-circle"

            AutoResizeMDIconButton:
                id: btn_outlined
                style: "outlined"
                icon: "account-circle"

        MDBoxLayout:
            adaptive_height: True
            spacing: dp(12)

            MDLabel:
                text: "Disabled preview"
                halign: "left"
                role: "medium"

            MDSwitch:
                id: sw
                size_hint_x: None
                width: dp(50)
                on_active: app.set_disabled(self.active)
"""


class DemoApp(MKVApp):
    def build(self):
        self.theme_cls.primary_palette = "Olive"
        MVCBuilder.load_libs_kv_files()
        return Builder.load_string(KV)

    def on_start(self):
        # ensure a quick disabled toggle demo
        Clock.schedule_once(lambda *_: self.set_disabled(False), 0)

    def set_disabled(self, flag: bool):
        ids = self.root.ids
        for k in ("btn_standard", "btn_filled", "btn_tonal", "btn_outlined"):
            btn = ids.get(k)
            if btn:
                btn.disabled = flag


if __name__ == "__main__":
    DemoApp().run()
