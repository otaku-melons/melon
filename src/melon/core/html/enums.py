from enum import Enum

class Align(Enum):
	"""Content align."""

	Left = "left"
	Right = "right"
	Center = "center"

class TagCategory(Enum):
	"""Tag category."""

	Styling = "styling"
	Wrapper = "wrapper"
