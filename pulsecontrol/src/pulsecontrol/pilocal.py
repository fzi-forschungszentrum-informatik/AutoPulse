from picamera2 import Picamera2
from time import sleep
import cv2

picam2 = Picamera2()
camera_config = picam2.create_still_configuration(
    main=dict(size=(4608, 2592), format="RGB888"), buffer_count=1
)
# camera_config = picam2.create_still_configuration(main=dict(size=(4608, 2592), format="RGB888"), buffer_count=1)
picam2.configure(camera_config)
picam2.start(show_preview=False)

picam2.set_controls(dict(AfMode=0, LensPosition=99999))

sleep(1)

RGB888 = picam2.capture_array("main")
cv2.imwrite("test.png", RGB888)
