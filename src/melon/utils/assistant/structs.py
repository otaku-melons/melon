from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Sequence

	from ...core.base.parsers.components.manifest import ContentTypes

@dataclass(frozen = True)
class ExtensionData:
	"""Extension initialization data."""

	parser_name: str
	name: str

@dataclass(frozen = True)
class ParserData:
	"""Parser initialization data."""

	name: str
	domain: str
	content_types: "Sequence[ContentTypes]"
