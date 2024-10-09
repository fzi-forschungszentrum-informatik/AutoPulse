from .spc_pcb_camera import SpcPcbCamera
from .generic_pcb_camera import GenericPcbCamera
from .nxp_pcb_camera import NxpPcbCamera
from .rectangle_camera import RectangleCamera
from .simple_pcb_camera import SimplePcbCamera
from .esp_32_camera import ESPPcbCamera

CameraStrategies = (
    RectangleCamera
    | NxpPcbCamera
    | GenericPcbCamera
    | SimplePcbCamera
    | SpcPcbCamera
    | ESPPcbCamera
)
