import re
from typing import TYPE_CHECKING

from ._base import BaseSettingsSection

if TYPE_CHECKING:
	from .....structs.image import ImageResolution
	from ..models import FiltersModel, ImagesFiltersModel, TextFiltersModel  # noqa: F401

class ImagesFilters(BaseSettingsSection["ImagesFiltersModel"]):
	"""Filters section: images."""

	def check_resolution(self, resolution: "ImageResolution") -> bool:
		"""
		check is image has valid resolution.

		Args:
			resolution (ImageResolution): Image resolution.

		Returns:
			bool: `True` if resolution is valid.
		"""

		if self.min_width and resolution.width < self.min_width: return False
		if self.min_height and resolution.height < self.min_height: return False
		if self.max_width and resolution.height > self.max_width: return False
		if self.max_height and resolution.height > self.max_height: return False

		return True

	@property
	def max_height(self) -> int | None:
		"""Maximal image height."""

		return self._data.max_height

	@property
	def max_width(self) -> int | None:
		"""Maximal image width."""

		return self._data.max_width

	@property
	def min_height(self) -> int | None:
		"""Minimal image height."""

		return self._data.min_height

	@property
	def min_width(self) -> int | None:
		"""Minimal image width."""

		return self._data.min_width

	@property
	def min_size(self) -> int | None:
		"""Minimal image size in bytes."""

		return self._data.min_size

	@property
	def signatures(self) -> tuple[str, ...]:
		"""Images signatires."""

		return self._data.signatures

class TextFilters(BaseSettingsSection["TextFiltersModel"]):
	"""Filters section: text."""

	def clear(self, text: str) -> str:
		"""
		Clear text by filters.

		Args:
			text (str): Text to cleaning.

		Returns:
			str: Cleaned text.
		"""

		for regex in self.regexs:
			text = re.sub(regex, "", text)

		for string in self.strings:
			text = text.replace(string, "")

		return text

	@property
	def regexs(self) -> tuple[str, ...]:
		"""Regular expressions."""

		return self._data.regexs

	@property
	def strings(self) -> tuple[str, ...]:
		"""Unresolved strings."""

		return self._data.strings

class Filters(BaseSettingsSection["FiltersModel"]):
	"""Settings section: filters."""

	@property
	def images(self) -> ImagesFilters:
		"""Filters section: images."""

		return self.__images

	@property
	def text(self) -> TextFilters:
		"""Filters section: text."""

		return self.__text

	def _post_init(self):
		"""Execute after instance initialization."""

		self.__images: ImagesFilters = ImagesFilters(self._data.images)
		self.__text: TextFilters = TextFilters(self._data.text)
