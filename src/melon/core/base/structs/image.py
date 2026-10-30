from dataclasses import dataclass
from enum import Enum
from os import PathLike
from pathlib import Path

@dataclass(frozen = True)
class ImageResolution:
	"""Разрешение изображения в пикселях."""

	width: int
	height: int

class ImageType(Enum):
	"""Title image type."""

	Cover = "covers"
	Person = "persons"
	Slide = "slides"
	Illustration = "illustrations"

class ImageData:
	"""Image data."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def file(self) -> Path | None:
		"""Path to image file in parser's images directory."""

		return self._file

	@property
	def filename(self) -> str:
		"""Image file name (from source)."""

		return self._filename

	@property
	def image_type(self) -> ImageType | None:
		"""Image type."""

		return self._type

	@property
	def link(self) -> str:
		"""Image link."""

		return self._link

	@property
	def resolution(self) -> ImageResolution | None:
		"""Image resolution."""

		return self._resolution

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, link: str, image_type: ImageType | None = None):
		"""
		Image data.

		Args:
			link (str): Image link.
			image_type (ImageType | None): Image type.
		"""

		self._link: str = link
		self._type: ImageType | None = image_type

		self._file: Path | None = None
		self._filename: str = Path(self._link.split("?", maxsplit = 1)[0]).name
		self._resolution: ImageResolution | None = None

	def create_resolution(self, width: int | None, height: int | None, autoset: bool = True) -> ImageResolution | None:
		"""
		Create image resolution.

		Args:
			width (int | None): Image width.
			height (int | None): Image height.
			autoset (bool): Set resolution to image data if valid.

		Returns:
			ImageResolution | None: Image resolution or `None` if data invalid.
		"""

		if not width or not height:
			return

		resolution = ImageResolution(width, height)

		if autoset:
			self.set_resolution(resolution)

		return resolution

	def set_file_path(self, file: PathLike[str] | str):
		"""
		Set file path in images directory of title.

		Args:
			file (PathLike[str] | str): Image file path in parser's images directory.
		"""

		self._file = Path(file)

	def set_resolution(self, resolution: ImageResolution | None):
		"""
		Set image resolution.

		Args:
			resolution (ImageResolution | None): Image resolution.
		"""

		self._resolution = resolution

	def to_dict(self, sizing: bool = True) -> dict:
		"""
		Generate dictionary representation of image data.

		Args:
			sizing (bool): Add image resolution.

		Returns:
			dict: Dictionary representation of image data.
		"""

		buffer: dict = {
			"link": self._link,
			"file": self._file.as_posix() if self._file else None,
		}

		if self._file:
			buffer["file"] = self._file.as_posix()

		if sizing:
			buffer["width"] = self._resolution.width if self._resolution else None
			buffer["height"] = self._resolution.height if self._resolution else None

		return buffer

	def to_html(self, sizing: bool = True) -> str:
		"""
		Generate HTML representation of image data.

		Args:
			sizing (bool): Add image resolution.

		Returns:
			str: HTML representation of image data.
		"""

		attributes: dict[str, str] = {
			"src": self._link,
		}

		if sizing and self._resolution:
			attributes["width"] = str(self._resolution.width)
			attributes["height"] = str(self._resolution.width)

		if self._file:
			attributes["data-file"] = self._file.as_posix()

		attributes_string: str = " ".join(f"name=\"{value}\"" for name, value in attributes.items())

		return f"<img{attributes_string}>"
