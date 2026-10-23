from enum import Enum

class SignatureVersion(Enum):
	"""Версии сигнатур фильтрации."""

	v1 = "{width}x{height}.{sha256}"
	v2 = "{similarity}.{phash}"
