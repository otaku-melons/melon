from typing import TYPE_CHECKING, Literal, NoReturn, overload

from dublib.web_requestor import WebResponse

from ... import exceptions
from ...base.structs.image import ImageType

if TYPE_CHECKING:
	from ...base.formats.base_format.chapter import BaseChapter
	from ...base.formats.base_format.controller import BaseTitleController
	from ...base.formats.base_format.data import BaseTitleData
	from . import Printer

class Portals:
	"""Output portals."""

	def __init__(self, printer: "Printer", package_identifier: str):
		"""
		Output portals.

		Args:
			printer (Printer): Output operator.
			package_identifier (str): Package identifier.
		"""

		self.__printer: Printer = printer
		self.__identifier: str = package_identifier

	@overload
	def authorization_required(self, text: str | None = None, raise_error: Literal[True] = True) -> NoReturn: ...
	@overload
	def authorization_required(self, text: str | None = None, raise_error: Literal[False] = ...): ...

	def authorization_required(self, text: str | None = None, raise_error: bool = True):
		"""
		Error portal: authorization required.

		Args:
			text (str | None): Error message.
			raise_error (bool): Condition: raise exception.

		Raises:
			AuthorizationRequiredError: Parser authorization method should be used.
		"""

		if not text:
			text = "Parser authorization method should be used."

		self.printer.critical(text)

		if raise_error:
			raise exceptions.parsing.AuthorizationRequiredError(text)

	def chapter_not_found(self, chapter: "BaseChapter", raise_error: bool = True):
		"""
		Warning: chapter not found.

		Args:
			chapter (BaseChapter): Chapter.
			raise_error (bool): Condition: raise exception.

		Raises:
			ChapterNotFoundError: Chapter not found.
		"""

		text: str = f"Chapter {chapter.id} not found."
		self.printer.error(text)

		if raise_error:
			raise exceptions.parsing.ChapterNotFoundError(chapter.id, chapter.slug)

	def chapter_skipped(self, chapter: "BaseChapter", comment: str | None = None):
		"""
		Message: chapter skipped.

		Args:
			chapter (BaseChapter): Chapter.
			comment (str | None): Comment text. Will be added as sentence at message end.
		"""

		chapter_type_note: str = "Paid chapter " if chapter.is_paid else "Chapter "
		chapter_identifier: str = ""

		if chapter.id:
			chapter_identifier = str(chapter.id)
		elif chapter.slug:
			chapter_identifier = f"\"{chapter.slug}\""

		comment = f" {comment}" if comment else ""
		text: str = f"{chapter_type_note}{chapter_identifier} skipped.{comment}"
		self.printer.emit(text)

	def collect_progress_by_page(self, page: int):
		"""
		Message: slugs collecting progress by page.

		Args:
			page (int): Processed catalog page.
		"""

		self.printer.emit(f"Titles on catalog page {page} collected.")

	def covers_unstubbed(self, title: "BaseTitleController[BaseTitleData]"):
		"""
		Message: covers unstubbed.

		Args:
			title (BaseTitleController[BaseTitleData]): Title controller.
		"""

		title.data.clear_covers()
		title.remove_images_type_directory(ImageType.Cover)

		self.printer.emit("Stubs detected. Covers data cleared.")

	def title_not_found(self, title_data: "BaseTitleData", raise_error: bool = True):
		"""
		Warning: title not found.

		Args:
			title_data (BaseTitleData): Title data.
			raise_error (bool): Condition: raise exception.

		Raises:
			TitleNotFoundError: Title not found.
		"""

		note_id: str = f" (ID: {title_data.id})" if title_data.id else ""
		text: str = f"Title: \"{title_data.slug}\"{note_id}. Not found."
		self.printer.warning(text)

		if raise_error:
			raise exceptions.parsing.TitleNotFoundError(title_data)

	@overload
	def request_error(self, response: WebResponse, text: str | None = None, raise_error: Literal[True] = True) -> NoReturn: ...
	@overload
	def request_error(self, response: WebResponse, text: str | None = None, raise_error: Literal[False] = ...): ...

	def request_error(self, response: WebResponse, text: str | None = None, raise_error: bool = True):
		"""
		Error: bad response.

		Args:
			response (WebResponse): Response.
			text (str | None): Error message.
			raise_error (bool): Condition: raise exception.

		Raises:
			ParsingError: Request error.
		"""

		if text:
			text = text.rstrip() + " "
		else:
			text = ""

		text = f"{text}Response code: {response.status_code}."
		self.printer.error(text)

		if self.printer.system_objects.options.DEBUG and response.json:
			self.printer.debug(str(response.json))

		if raise_error:
			raise exceptions.parsing.ParsingError(text)

	def unsupported_format(self, message: str, raise_error: bool = True):
		"""
		Error: unsupported format.

		Args:
			message (str): Message error or format name.
			raise_error (bool): Condition: raise exception.

		Raises:
			UnsupportedFormatError: Unsupported format.
		"""

		self.printer.error(message)

		if raise_error:
			raise exceptions.parsers.UnsupportedFormatError(message)

	@property
	def printer(self) -> "Printer":
		"""Output operator."""

		return self.__printer
