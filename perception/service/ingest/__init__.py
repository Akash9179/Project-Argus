from service.ingest.manager import SourceManager, detect_source_type
from service.ingest.base import SourceAdapter
from service.ingest.webcam import WebcamAdapter
from service.ingest.file import FileAdapter
from service.ingest.rtsp import RTSPAdapter
from service.ingest.mjpeg import MJPEGAdapter

__all__ = [
    "SourceManager",
    "SourceAdapter",
    "WebcamAdapter",
    "FileAdapter",
    "RTSPAdapter",
    "MJPEGAdapter",
    "detect_source_type",
]
