from dataclasses import dataclass

@dataclass(frozen = True)
class SourceProperties:
	"""
	Source properties.

	- **one_cover**: Is source provides always only one cover or it's resized versions. If enabled all images will be removed if one of them filtered.
	"""

	one_cover: bool
