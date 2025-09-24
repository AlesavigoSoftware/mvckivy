# -------------------- Демо-виджеты с «перекрёстными» зависимостями --------------------
from kivy.properties import StringProperty, NumericProperty, ListProperty

from mvckivy.properties.dedupe_mixin import KVDedupeMixin, dump_observers
from kivy.uix.floatlayout import FloatLayout


class ParentProbe(KVDedupeMixin, FloatLayout):
    # управляем пользователем через кнопки (абсолютное позиционирование)
    self_pos = ListProperty([60.0, 50.0])

    # целевые + счётчики
    text = StringProperty("")  # зависит ТОЛЬКО от right
    calls_text_base = NumericProperty(0)
    calls_text_child = NumericProperty(0)

    calls_width = NumericProperty(0)  # width зависит ТОЛЬКО от y
    calls_height = NumericProperty(0)  # height зависит ТОЛЬКО от pos

    # глобально чистим дубликаты только для text (оставляем override)
    __kv_dedupe_targets__ = ("text",)

    # --- расчёты ---
    def calc_height_from_pos(self, pos_xy) -> float:
        self.calls_height += 1
        x, y = pos_xy
        return max(80.0, min(420.0, 120.0 + 0.25 * x + 0.15 * y))

    def calc_width_from_y(self, y: float) -> float:
        self.calls_width += 1
        return max(160.0, min(520.0, 200.0 + 0.8 * y))

    def calc_text_base(self, right_val: float) -> str:
        self.calls_text_base += 1
        return f"BASE text: right={right_val:.1f} (x+width)"

    def calc_text_child(self, right_val: float) -> str:
        self.calls_text_child += 1
        return f"CHILD text: right*0.5={0.5*right_val:.1f}"


class ChildProbe(ParentProbe):
    pass


KV = r"""
<ParentProbe>:
    # ВАЖНО: только FloatLayout вокруг, без BoxLayout — чтобы pos реально менялся.
    # Стандартные зависимости и отключение size_hint:
    pos:
        root.self_pos
    size_hint:
        None, None

    # Перекрёстные правила:
    # 1) height зависит ТОЛЬКО от pos
    height:
        root.calc_height_from_pos(root.pos)
    # 2) width зависит ТОЛЬКО от y
    width:
        root.calc_width_from_y(root.y)
    # 3) text зависит ТОЛЬКО от right (x+width)
    text:
        root.calc_text_base(root.right)

    canvas.before:
        Color:
            rgba: 0.2, 0.6, 0.9, 0.12
        Rectangle:
            pos: self.pos
            size: self.size

    # Панель управления позицией — меняем x/y → триггерим пересчёты
    BoxLayout:
        size_hint:
            None, None
        size:
            self.minimum_size
        pos:
            root.x + 8, root.top - self.height - 8
        spacing:
            "6dp"
        Button:
            text:
                "x-10"
            size_hint:
                None, None
            size:
                "56dp", "32dp"
            on_release:
                root.self_pos = [root.self_pos[0]-10, root.self_pos[1]]
        Button:
            text:
                "x+10"
            size_hint:
                None, None
            size:
                "56dp", "32dp"
            on_release:
                root.self_pos = [root.self_pos[0]+10, root.self_pos[1]]
        Button:
            text:
                "y-10"
            size_hint:
                None, None
            size:
                "56dp", "32dp"
            on_release:
                root.self_pos = [root.self_pos[0], root.self_pos[1]-10]
        Button:
            text:
                "y+10"
            size_hint:
                None, None
            size:
                "56dp", "32dp"
            on_release:
                root.self_pos = [root.self_pos[0], root.self_pos[1]+10]

    # Вывод текста и счётчиков
    BoxLayout:
        orientation:
            "vertical"
        padding:
            "6dp"
        spacing:
            "4dp"
        pos:
            root.x + 8, root.y + 8
        size_hint:
            None, None
        size:
            root.width - 16, root.height - 16
        Label:
            text:
                root.text
            halign:
                "left"
            valign:
                "top"
            text_size:
                self.size
        Label:
            size_hint_y:
                None
            height:
                "22dp"
            text:
                f"calls: height={root.calls_height}, width={root.calls_width}, text_base={root.calls_text_base}, text_child={root.calls_text_child}"


# --- МЯГКОЕ ПЕРЕОПРЕДЕЛЕНИЕ: без дефиса ---
<ChildProbe@ParentProbe>:
    text:
        root.calc_text_child(root.right)

FloatLayout:
    padding:
        "8dp"

    # Свободная раскладка, чтобы pos реально менялся
    FloatLayout:
        size_hint:
            1, 0.48
        canvas.before:
            Color:
                rgba: 0, 0, 0, 0.04
            Rectangle:
                pos: self.pos
                size: self.size
        ParentProbe:
            self_pos:
                [60, 50]

    FloatLayout:
        size_hint:
            1, 0.48
        canvas.before:
            Color:
                rgba: 0, 0, 0, 0.04
            Rectangle:
                pos: self.pos
                size: self.size
        ChildProbe:
            self_pos:
                [80, 60]
"""


from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock


class DemoApp(App):
    def build(self):
        root = Builder.load_string(KV)

        # Поздний снимок после сборки — видно бинды на right/y/pos и т.п.
        def late_dump(_dt):
            for w in root.walk():
                if isinstance(w, ParentProbe):
                    dump_observers(
                        w,
                        ("pos", "x", "y", "right", "top", "width", "height", "text"),
                        "поздний снимок после сборки",
                    )

        Clock.schedule_once(late_dump, 0)
        return root


if __name__ == "__main__":
    DemoApp().run()
