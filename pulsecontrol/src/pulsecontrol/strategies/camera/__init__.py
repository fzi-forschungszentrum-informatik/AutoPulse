from .spc_pcb_camera import SpcPcbCamera
from .generic_pcb_camera import GenericPcbCamera
from .nxp_pcb_camera import NxpPcbCamera
from .rectangle_camera import RectangleCamera
from .simple_pcb_camera import SimplePcbCamera

CameraStrategies = RectangleCamera | NxpPcbCamera | GenericPcbCamera | SimplePcbCamera | SpcPcbCamera
