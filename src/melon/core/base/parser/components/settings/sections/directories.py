from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ._base import BaseSettingsSection

if TYPE_CHECKING:
	from ......system_objects import SystemObjects
	from ..models import DirectoriesModel

class Directories(BaseSettingsSection["DirectoriesModel"]):
	"""Settings section: directories."""

	def __get_default_directory(self, directory_type: Literal["content", "images", "titles"]) -> Path:
		"""
		Get path to exists default directory.

		Args:
			directory_type (Literal["content", "images", "titles"]): Directory type.

		Returns:
			Path: Path to directory.
		"""

		directory: Path = self.__system_objects.options.DEFAULT_OUTPUT_DIR / self.__parser_name / directory_type
		directory.mkdir(exist_ok = True)

		return directory

	def __init__(self, data: "DirectoriesModel", system_objects: "SystemObjects", parser_name: str):
		"""
		Settings section: directories.

		Args:
			data (DirectoriesModel): Data model.
			system_objects (SystemObjects): System objects collection.
			parser_name (str): Parser name.
		"""

		super().__init__(data)

		self.__system_objects: SystemObjects = system_objects
		self.__parser_name: str = parser_name

	@property
	def content(self) -> Path:
		"""Path to content directory."""

		if self._data.content:
			return self._data.content

		return self.__get_default_directory("content")

	@property
	def images(self) -> Path:
		"""Path to images directory."""

		if self._data.images:
			return self._data.images

		return self.__get_default_directory("images")

	@property
	def titles(self) -> Path:
		"""Path to titles directory."""

		if self._data.titles:
			return self._data.titles

		return self.__get_default_directory("titles")
