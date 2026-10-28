from pathlib import Path
from typing import TYPE_CHECKING, override

from ... import exceptions
from ...base.formats.base_format.enums import ImageType
from ..base_elements import BaseElement

if TYPE_CHECKING:
	from pydantic import BaseModel

	from ...base.parsers.base_parser import BaseParser
	from ...base.parsers.components.images_downloader import (
		ImageDownloadingResult,
		ImageResolution,
	)
	from ...base.source_operator import BaseSourceOperator

class Image(BaseElement):
	"""Image."""

	#==========================================================================================#
	# >>>>> OVERRIDDEN METHODS <<<<< #
	#==========================================================================================#

	@override
	def _export_element_tag(self) -> str:
		"""
		Export element main tag name.

		Returns:
			str: Element main tag name.
		"""

		return "img"

	@override
	def _to_html(self) -> str:
		"""
		Convert element to HTML representation.

		Returns:
			str: HTML representation of element.
		"""

		if not self._mount_path:
			raise exceptions.html.CompositingError("Missing mount path for image.")

		soup = self._parse("")
		wrapper = soup.new_tag("p")
		soup.append(wrapper)

		tag = wrapper.new_tag(self.element_tag)

		source: Path = self._mount_path / self._filename
		tag["src"] = source.as_posix()

		if self._resolution:
			tag["width"] = str(self._resolution.width)
			tag["height"] = str(self._resolution.height)

		soup.append(tag)

		return str(soup)

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, url: str):
		"""
		Image.

		Args:
			url (str): Image link.
		"""

		self._link: str = url

		self._filename: str = Path(self._link).stem

		self._resolution: ImageResolution | None = None
		self._mount_path: Path | None = None

	def download(self, parser: "BaseParser[BaseSourceOperator, BaseModel]", chapter_id: int) -> "ImageDownloadingResult":
		"""
		Download image.

		Args:
			parser (BaseParser[BaseSourceOperator, BaseModel]): Parser.
			chapter_id (int): Chapter ID.

		Raises:
			exceptions.parsers.TitleNotSetError: Title not set.

		Returns:
			ImageDownloadingResult: Downloading result.
		"""

		if not parser.title:
			raise exceptions.parsers.TitleNotSetError()

		source_operator: BaseSourceOperator = parser.source_operator
		mount_path: Path = Path(parser.title.used_filename) / str(chapter_id)

		future = parser.portals.printer.templates.images.start_downloading(self._filename, ImageType.Illustration)

		result = source_operator.download_image(
			url = self._link,
			directory = source_operator.settings.directories.images / mount_path,
			filename = self._filename,
		)

		future.result(result)

		if result.resolution:
			self._resolution = result.resolution

		self._mount_path = mount_path

		return result

	def rename(self, filename: str):
		"""
		Change image filename.

		Args:
			filename (str): New image filename.
		"""

		self._filename = Path(filename).stem
