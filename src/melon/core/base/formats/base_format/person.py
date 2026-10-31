from typing import TYPE_CHECKING

from dublib.functions.data import to_sequence

if TYPE_CHECKING:
	from collections.abc import Sequence

	from ....html.elements import Paragraph
	from ...structs.image import ImageData

class Person:
	"""Person data."""

	@property
	def name(self) -> str:
		"""Name."""

		return self.__data["name"]

	@property
	def another_names(self) -> tuple[str, ...]:
		"""Alternative names"""

		return self.__data["another_names"]

	@property
	def images(self) -> tuple["ImageData", ...]:
		"""Images."""

		return tuple(self.__images)

	@property
	def description(self) -> tuple["Paragraph", ...]:
		"""Description."""

		return self.__description

	def __init__(self, name: str):
		"""
		Person data.

		Args:
			name (str): Name.
		"""

		self.__data: dict = {
			"name": name,
			"another_names": [],
			"images": [],
			"description": None,
		}

		self.__description: tuple[Paragraph, ...] = ()
		self.__images: list[ImageData] = []

	def add_another_name(self, another_name: str):
		"""
		Add another name.

		Args:
			another_name (str): Another name.
		"""

		another_name = another_name.strip()

		if another_name and another_name != self.name and another_name not in self.another_names:
			names: list[str] = self.__data["another_names"]
			names.append(another_name)

	def add_image(self, image: "ImageData"):
		"""
		Add image.

		Args:
			image (ImageData): Image data.
		"""

		self.__images.append(image)

	def find_image(self, link: str) -> "ImageData | None":
		"""
		Find image by link.

		Args:
			link (str): Image link.

		Returns:
			ImageData | None: Image data.
		"""

		for image in self.__images:
			if image.link == link:
				return image

	def remove_image(self, link: str) -> bool:
		"""
		Remove image by link.

		Args:
			link (str): Image link.

		Returns:
			bool: `True` if image removed.
		"""

		image = self.find_image(link)

		if image:
			self.__images.remove(image)
			return True

		return False

	def set_description(self, description: "Paragraph | Sequence[Paragraph] | None"):
		"""
		Set person description.

		Args:
			description (Paragraph | Sequence[Paragraph] | None): Person description elements.
		"""

		if not description:
			self.__description = ()

		self.__description = to_sequence(description)

	def to_dict(self, sizing: bool = True) -> dict:
		"""
		Generate dictionary representation of data.

		Args:
			sizing (bool): Condition: save images resolutions.

		Returns:
			dict: Dictionary representation of data.
		"""

		buffer: dict = self.__data.copy()
		buffer["description"] = [element.to_html() for element in self.__description]

		for index in range(len(self.__images)):
			image: ImageData = self.__images[index]
			images_list: list[dict] = buffer["images"]
			images_list.append(image.to_dict(sizing))

		return buffer
