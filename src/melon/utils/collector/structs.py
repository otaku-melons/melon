
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ...core.base.structs.title import TitleDescriptor

@dataclass(frozen = True)
class CollectingResult:
	"""
	Titles slugs collecting result

	- **slugs** – collected slugs;
	- **added** – unique added slugs count;
	- **descriptors** – titles descriptors from whuch collected slugs.
	"""

	slugs: tuple[str, ...]
	added: int
	descriptors: tuple["TitleDescriptor", ...]
