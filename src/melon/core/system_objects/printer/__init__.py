import sys
from typing import TYPE_CHECKING, Literal, NoReturn, overload

import orjson

from dublib.cli.messages.generator import MessageType, generate_message
from dublib.cli.progress_indicator import ProgressIndicator
from dublib.cli.text_styler import TextStyler

from .portals import Portals
from .templates import Templates

if TYPE_CHECKING:
	from rich.table import Table

	from ....core.system_objects import SystemObjects

class Printer:
	"""Output operator."""

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Output operator.

		Args:
			system_objects (SystemObjects): System objects collection.
		"""

		self.__system_objects: SystemObjects = system_objects

		self.__styler: TextStyler = TextStyler()
		self.__progress_indicator: ProgressIndicator = ProgressIndicator()
		self.__templates: Templates = Templates(self)

	@overload
	def critical(self, text: str, origin: str | None = None, end_work: Literal[True] = ...) -> NoReturn: ...
	@overload
	def critical(self, text: str, origin: str | None = None, end_work: Literal[False] = False): ...

	def critical(self, text: str, origin: str | None = None, end_work: bool = False):
		"""
		Emit critical error message.

		Args:
			text (str): Message text.
			origin (str | None): Message origin.
			end_work (bool): Condition: stop script work.
		"""

		self.emit(text, MessageType.Critical, origin)
		if end_work: sys.exit(1)

	def debug(self, text: str, origin: str | None = None):
		"""
		Emit debug message. If debug mode disabled will be ignored.

		Args:
			text (str): Message text..
			origin (str | None): Message origin.
		"""

		if self.system_objects.options.DEBUG:
			self.emit(text, MessageType.Debug, origin)

	def emit(
		self,
		text: str,
		message_type: MessageType | None = None,
		origin: str | None = None,
		end_line: bool = True,
		flush: bool = False,
		parse_mode: Literal["html", "rich"] | None = "rich",
		):
		"""
		Emit message in output stream.

		Args:
			text (str): Message text.
			message_type (MessageType | None): Message type.
			origin (str | None): Message origin.
			end_line (bool): Condition: add newline character at end.
			flush (bool): Condition: flush terminal buffer.
			parse_mode (Literal["html", "rich"] | None): Parse mode to create ANSI styles.
		"""

		match parse_mode:
			case "html": text = self.__styler.convert_from_html(text)
			case "rich": text = self.__styler.convert(text)

		message_text: str = generate_message(text, message_type, origin).lstrip()
		print(message_text, end = "\n" if end_line else "", flush = flush)

	def error(self, text: str, origin: str | None = None):
		"""
		Emit error message.

		Args:
			text (str): Message text..
			origin (str | None): Message origin.
		"""

		self.emit(text, MessageType.Error, origin)

	def get_parser_portals(self, parser_name: str) -> Portals:
		"""
		Create parser portals instance.

		Args:
			parser_name (str): Parser name.

		Returns:
			Portals: Portals instance.
		"""

		return Portals(self, parser_name)

	def json(self, data: dict):
		"""
		Serialize dictionary into JSON and emit it as message.

		Args:
			data (dict): Serializable data.
		"""

		self.emit(orjson.dumps(data).decode())

	def table(self, table: "Table"):
		"""
		Parse [Rich](https://github.com/textualize/rich) table end emit it as message.

		Args:
			table (Table): Rich table.
		"""

		text: str = self.styler.convert_table(table)
		self.emit(text, parse_mode = None)

	def warning(self, text: str, origin: str | None = None):
		"""
		Emit warning message.

		Args:
			text (str): Message text..
			origin (str | None): Message origin.
		"""

		self.emit(text, MessageType.Warning, origin)

	@property
	def progress_indicator(self) -> ProgressIndicator:
		"""**OSC 9;4** protocol progress indicator."""

		return self.__progress_indicator

	@property
	def system_objects(self) -> "SystemObjects":
		"""System objects collection."""

		return self.__system_objects

	@property
	def styler(self) -> TextStyler:
		"""Text styler."""

		return self.__styler

	@property
	def templates(self) -> Templates:
		"""Extended output templates."""

		return self.__templates
