from enum import Enum

class ContentTypes(Enum):
	"""Content types enumeration."""

	Manga = "manga"
	Ranobe = "ranobe"

class Directives(Enum):
	"""Manifest directives enumeration."""

	from_parent = "$from_parent"
	last_git_tag = "$last_git_tag"
