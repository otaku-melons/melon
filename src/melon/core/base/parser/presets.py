from typing import TYPE_CHECKING, override

from ..formats.manga.controller import Manga
from ..formats.ranobe.controller import Ranobe
from . import BaseParser
from .enums import ContentType

if TYPE_CHECKING:
	from pydantic import BaseModel

	from ..source_operator import BaseSourceOperator

class BaseMangaParser[SO: "BaseSourceOperator", CSM: "BaseModel"](BaseParser[SO, CSM, Manga]):
	"""Base manga parser.."""

	@override
	def _export_content_type(self) -> ContentType:
		"""
		Export content type.

		Returns:
			ContentType: Content type.
		"""

		return ContentType.Manga

	@override
	def _export_controller_type(self) -> type[Manga]:
		"""
		Export chapter controller type.

		Returns:
			type[Manga]: Chapter controller type.
		"""

		return Manga

class BaseRanobeParser[SO: "BaseSourceOperator", CSM: "BaseModel"](BaseParser[SO, CSM, Ranobe]):
	"""Base ranobe parser."""

	@override
	def _export_content_type(self) -> ContentType:
		"""
		Export content type.

		Returns:
			ContentType: Content type.
		"""

		return ContentType.Ranobe

	@override
	def _export_controller_type(self) -> type[Ranobe]:
		"""
		Export chapter controller type.

		Returns:
			type[Ranobe]: Chapter controller type.
		"""

		return Ranobe
