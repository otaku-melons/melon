from enum import Enum

class ContentType(Enum):
	"""Content types enumeration."""

	Manga = "manga"
	Ranobe = "ranobe"

class ImagesLevel(Enum):
	"""Images downloading level."""

	NO = 0
	METAINFO = 1
	ALL = 2
