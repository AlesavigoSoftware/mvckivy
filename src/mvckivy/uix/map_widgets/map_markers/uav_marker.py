from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy_garden.mapview import MapMarkerPopup
from kivymd.uix.behaviors import RotateBehavior
from kivymd.uix.button import MDButton, MDButtonText

from utility import ProjectPathManager


class RotatedButton(MDButton, RotateBehavior):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rotate_value_angle = 0


class UAVMapMarker(MapMarkerPopup, RotateBehavior):
    placeholder_pos_y = NumericProperty()

    def __init__(self, num: int, **kwargs):
        super().__init__(
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    'images',
                    'map',
                    'markers',
                    'drone_marker.png'
                )
            ),
            **kwargs)

        #  В Image отсутствует повторное задание режима сжатия (fit_mode) при перезагрузке source

        self.anchor_x = 0.5
        self.anchor_y = 0.5
        self.fit_mode = 'fill'
        self.is_open = True

        self.rotate_value_angle = 0

        self.num = num + 1
        self.placeholder = 0  # None is not allowed inside this property
        self._popup_container = RelativeLayout(
            y=self.top,
            center_x=self.center_x,
            size=self.popup_size,
        )
        self.bind(placeholder_pos_y=self._popup_container.setter('y'))
        self.bind(center_x=self._popup_container.setter('center_x'))

        self.popup_button = RotatedButton(
            MDButtonText(
                text=str(self.num),
                theme_font_size='Custom',
                font_size='14sp',
            ),
            style='outlined',
            theme_width='Custom',
            width = dp(48),
            height = dp(24),
            line_color=(0, 0, 0, .2),
            md_bg_color=[.9, .9, .9, .5],
            pos_hint={'center_x': .5, 'center_y': -1.8},
        )
        self._scaner_gif = Image(
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    'images',
                    'map',
                    'uav_direction.gif'
                )
            ),
            size=self.popup_size,
            anim_delay=0,
            anim_loop=0,
        )

        self.add_widget(self._popup_container)
        self.add_widget(self._scaner_gif)
        self.add_widget(self.popup_button)

    def on_top(self, instance, value):
        self.placeholder_pos_y = value

    def anim_move(
            self,
            new_lat: float,
            new_lon: float,
            angle: int,
            duration: float = .5
    ):
        anim_marker = Animation(
            lat=new_lat,
            lon=new_lon,
            rotate_value_angle=angle,
            duration=duration
        )
        anim_marker.start(self)
        anim_popup = Animation(
            rotate_value_angle=-angle, duration=duration
        )
        anim_popup.start(self.popup_button)
