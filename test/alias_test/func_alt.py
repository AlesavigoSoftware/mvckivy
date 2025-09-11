from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("demo")

KV = r"""
<LabelBox@BoxLayout>:
    orientation: "vertical"
    spacing: 6
    padding: 6

<BaseBox@BoxLayout>:
    # Вариант A: БЕЗ явной зависимости — пересчёт только один раз при применении правила
    # width: root.compute_width()   # ← раскомментируйте, чтобы увидеть «одиночный» вызов
    #
    # Вариант B: С явной зависимостью — пересчёт при каждом изменении size
    width: root.compute_width(root.size)  # ← этот вариант повторяет семантику bind=['size']
    size_hint_y: None
    height: 80

<ChildUses@BaseBox>:
    # Ничего не переопределяем: метод остаётся в выражении width

<ChildConst@BaseBox>:
    # Переопределяем width константой: метод базового класса будет вычислен при применении
    # правила <BaseBox> (один раз), но итоговое значение width перезапишется здесь
    width: 260

<Root>:
    orientation: "vertical"
    padding: 10
    spacing: 10

    LabelBox:
        # СЦЕНАРИЙ 1: метод ИСПОЛЬЗУЕТСЯ
        ChildUses:
            id: uses1
            tag: "uses1"
        ChildUses:
            id: uses2
            tag: "uses2"

    LabelBox:
        # СЦЕНАРИЙ 2: метод ЗАМЕНЁН константой
        ChildConst:
            id: const1
            tag: "const1"
        ChildConst:
            id: const2
            tag: "const2"
"""


class Root(BoxLayout):
    pass


class BaseBox(BoxLayout):
    tag = StringProperty("")

    # метод, который «аналогичен» алиасу: может учитывать size и что-то считать
    def compute_width(self, size_tuple=None):
        t = self.tag or self.__class__.__name__
        if size_tuple is None:
            # вариант A: зависимость скрыта от kv (пересчёт 1 раз)
            w = int(self.size[0])
            log.info(
                f"⚡ compute_width() → {self.__class__.__name__}<{t}> size={tuple(self.size)} → {w}"
            )
            return w
        else:
            # вариант B: зависимость видима kv через аргумент
            w = int(size_tuple[0])
            log.info(
                f"⚡ compute_width(size) → {self.__class__.__name__}<{t}> size={tuple(size_tuple)} → {w}"
            )
            return w


class DemoApp(App):
    def build(self):
        Builder.load_string(KV)
        root = Root()
        Clock.schedule_once(lambda dt: self._after_build(root), 0)
        return root

    def _after_build(self, root):
        log.info("\n=== 1) Меняем size у ChildUses (метод используется) ===")
        root.ids.uses1.size = (300, 80)
        root.ids.uses2.size = (350, 80)

        log.info("\n=== 2) Меняем size у ChildConst (метод заменён константой) ===")
        root.ids.const1.size = (400, 80)
        root.ids.const2.size = (450, 80)

        log.info("\n=== Готово ===")


if __name__ == "__main__":
    DemoApp().run()
