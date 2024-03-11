from pathlib import Path

# noinspection PyUnresolvedReferences
from picamera2 import Picamera2

from pulsecontrol.strategies.camera.strategy import to_image

camera = Picamera2()
camera_config = camera.create_still_configuration(main=dict(format="RGB888"), buffer_count=1)
camera.configure(camera_config)
camera.start(show_preview=False)

conf = camera.camera_config
lico = camera.libcamera_config

camera.set_controls(dict(AfMode=1))
focus = camera.autofocus_cycle()
print("REsult: ", focus)
i = camera.capture_array("main")

to_image(Path("manual.jpg"), i)
print(conf)
print(lico)
