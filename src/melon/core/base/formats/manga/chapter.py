from typing import TYPE_CHECKING, override

from ...structs.image import ImageData, ImageType
from ..base_format.chapter import BaseChapter

if TYPE_CHECKING:
	from collections.abc import Sequence

class Chapter(BaseChapter):
	"""Manga chapter."""

	def add_slide(self, image: "ImageData") -> int | None:
		"""
		Add slide.

		If slide has resolution it will be checked by filters. In check failure slide doesn't adds.

		Args:
			image (ImageData): Slide.

		Returns:
			int | None: Slide index or `None` if not added
		"""

		if image.resolution and not self._parser.settings.filters.images.check_resolution(image.resolution):
			return None

		index = self.__get_new_slide_index()
		self.__slides[index] = image

		return index

	def set_slides(self, images: "Sequence[ImageData]"):
		"""
		Clear exists slides and set new.

		Args:
			images (Sequence[ImageData]): New slides.
		"""

		self._clear_content()

		for current_image in images:
			self.add_slide(current_image)

	@property
	def slides(self) -> "tuple[ImageData, ...]":
		"""Slides."""

		return tuple(self.__slides.values())

	@override
	def _clear_content(self):
		"""Clear chapter content."""

		self.__slides.clear()

	@override
	def _from_dict(self, data: dict):
		"""
		Parse chapter dictionary from descriptive file and fill instance attributes.

		Args:
			data (dict): Chapter data.
		"""

		self._data = self._data | data

		self.__slides = self.__parse_slides(self._data["slides"])

	@override
	def _get_chapter_images(self) -> "Sequence[ImageData]":
		"""
		Get chapter-associated images.

		Returns:
			Sequence[ImageData]: Chapter images.
		"""

		return tuple(self.__slides.values())

	@override
	def _is_empty(self) -> bool:
		"""
		Check is chapter empty.

		Returns:
			bool: Condition: is chapter empty.
		"""

		return not bool(self.slides)

	@override
	def _post_init(self):
		"""Execute after instance initialization."""

		self._data["slides"] = []

		self.__slides: dict[int, ImageData] = {}

	@override
	def _pre_formatter(self):
		"""Execute before chapter data conversion into dictionary."""

		slides_data: list[dict] = []

		for index, image in self.__slides.items():
			buffer: dict = {"index": index} | image.to_dict(sizing = self._parser.settings.common.sizing_images)
			slides_data.append(buffer)

		self._data["slides"] = tuple(slides_data)

	def __get_new_slide_index(self) -> int:
		"""
		Get new slide index.

		Returns:
			int: Slide index.
		"""

		START_INDEX: int = 1

		indexes: tuple[int, ...] = tuple(self.__slides.keys())

		if not indexes:
			return START_INDEX
		else:
			return max(indexes) + 1

	def __parse_slides(self, slides_data: list[dict]) -> dict[int, ImageData]:
		"""
		Parse slides from chapter content list.

		Args:
			slides_data (list[dict]): Chapter content list.

		Returns:
			dict[int, ImageData]: Indexed slides data.
		"""

		slides: dict[int, ImageData] = {}

		for slide_data in slides_data:
			index: int = slide_data["index"]
			image = ImageData(slide_data["link"], ImageType.Slide)

			width, height = slide_data.get("width"), slide_data.get("height")
			if width and height:
				image.create_resolution(width, height)

			file: str | None = slide_data.get("file")
			if file:
				image.set_file_path(file)

			slides[index] = image

		return slides
