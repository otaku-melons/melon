from enum import Enum

class By(Enum):
	"""Descriptive file identifier."""

	Filename = None
	Slug = "slug"
	ID = "id"

class Status(Enum):
	"""Title status type."""

	announced = "announced"
	ongoing = "ongoing"
	completed = "completed"
	dropped = "dropped"
