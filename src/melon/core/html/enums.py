from enum import Enum

class Align(Enum):
	"""Content align."""

	Right = "right"
	Center = "center"

class TagCategory(Enum):
	"""Tag category."""

	Alignable = "alignable"
	Footnotable = "footnotable"
	Styling = "styling"
	SupportData = "support_data"
