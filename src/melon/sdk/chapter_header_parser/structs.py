from dataclasses import dataclass

from ...core.base.formats.ranobe.enums import ChapterType

@dataclass(frozen = True)
class HeaderData:
	"""Chapter header data."""

	volume: str | None
	number: str | None
	name: str | None
	chapter_type: ChapterType | None
