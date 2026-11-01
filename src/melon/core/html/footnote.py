from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from ..base.structs.image import ImageData

if TYPE_CHECKING:
	from .elements import Paragraph

@dataclass(frozen = True)
class Footnote:
	"""
	Footnote data.

	Field `id` generated automatically as UUID4.
	"""

	elements: tuple["Paragraph | ImageData", ...]
	id: str = str(uuid4())

	@property
	def images(self) -> tuple["ImageData", ...]:
		"""Images data."""

		return tuple(element for element in self.elements if isinstance(element, ImageData))
