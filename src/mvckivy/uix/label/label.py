from kivy.clock import Clock
from kivy.metrics import sp
from kivy.properties import NumericProperty
from kivymd.uix.label import MDLabel


class AutoResizeLabel(MDLabel):
    min_font_size = NumericProperty(sp(10))
    max_font_size = NumericProperty(sp(240))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._adjust_text_size, text=self._adjust_text_size)
        Clock.schedule_once(lambda dt: self._adjust_text_size())

    def _set_new_font_size(self, font_size: int):
        self.font_size = font_size
        self.texture_update()

    def _adjust_text_size(self, *_):
        if not self.text or not self.size:
            return

        min_size = self.min_font_size
        max_size = min(self.height, self.width, self.max_font_size)
        best_size = min_size

        while min_size <= max_size:
            mid_size = (min_size + max_size) // 2
            self._set_new_font_size(mid_size)
            if self.texture_size[0] <= self.width and self.texture_size[1] <= self.height:
                best_size = mid_size
                min_size = mid_size + 1
            else:
                max_size = mid_size - 1

        self._set_new_font_size(best_size)
