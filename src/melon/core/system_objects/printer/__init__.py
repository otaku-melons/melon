import sys
from typing import TYPE_CHECKING, Literal, NoReturn, overload

import orjson

from dublib.cli.messages.generator import MessageType, generate_message
from dublib.cli.progress_indicator import ProgressIndicator
from dublib.cli.text_styler import TextStyler

from .portals import Portals
from .templates import Templates

if TYPE_CHECKING:
	from ....core.system_objects import SystemObjects

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Printer:
	"""Оператор вывода."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def progress_indicator(self) -> ProgressIndicator:
		"""Терминальный индикатор прогресса на основе OSC 9;4."""

		return self.__ProgressIndicator

	@property
	def system_objects(self) -> "SystemObjects":
		"""Коллекция системных объектов."""

		return self.__SystemObjects

	@property
	def templates(self) -> Templates:
		"""Расширенные шаблоны вывода."""

		return self.__Templates

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Оператор вывода.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__SystemObjects = system_objects

		self.__styler: TextStyler = TextStyler()
		self.__ProgressIndicator = ProgressIndicator()
		self.__Templates = Templates(self)

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

		:param text: Message text.
		:type text: str
		:param message_type: Message type.
		:type message_type: MessageType | None
		:param origin: Message origin.
		:type origin: str | None
		:param end_line: Condition: addn ewline character at message end.
		:type end_line: bool
		:param flush: Condition: flush buffer.
		:type flush: bool
		:param parse_mode: Message styles parsing mode.
		:type parse_mode: Literal["html", "rich"] | None
		"""

		match parse_mode:
			case "html": text = self.__styler.convert_from_html(text)
			case "rich": text = self.__styler.convert(text)

		message_text: str = generate_message(text, message_type, origin)
		print(message_text, end = "\n" if end_line else "", flush = flush)

	def get_parser_portals(self, parser_name: str) -> Portals:
		"""
		Возвращает порталы вывода парсера.

		:param parser_name: Имя парсера.
		:type parser_name: str
		:return: Порталы вывода парсера.
		:rtype: Portals
		"""

		return Portals(self, parser_name)

	#==========================================================================================#
	# >>>>> ШАБЛОНЫ ВЫВОДА БАЗОВЫХ ТИПОВ СООБЩЕНИЙ <<<<< #
	#==========================================================================================#

	@overload
	def critical(self, text: str, origin: str | None = None, end_work: Literal[True] = ...) -> NoReturn: ...
	@overload
	def critical(self, text: str, origin: str | None = None, end_work: Literal[False] = False): ...

	def critical(self, text: str, origin: str | None = None, end_work: bool = False):
		"""
		Выводит в терминал критическую ошибку.

		:param text: Текст сообщения.
		:type text: str
		:param origin: Источник сообщения.
		:type origin: str | None
		:param end_work: Указывает, нужно ли завершить работу скрипта при обработке ошибки.
		:type end_work: bool
		"""

		self.emit(text, MessageType.Critical, origin)
		if end_work: sys.exit(1)

	def debug(self, text: str, origin: str | None = None):
		"""
		Выводит в терминал сообщение отладки.

		:param text: Текст сообщения.
		:type text: str
		:param origin: Источник сообщения.
		:type origin: str | None
		"""

		if self.__SystemObjects.options.DEBUG:
			self.emit(text, MessageType.Debug, origin)

	def error(self, text: str, origin: str | None = None):
		"""
		Выводит в терминал ошибку.

		:param text: Текст сообщения.
		:type text: str
		:param origin: Источник сообщения.
		:type origin: str | None
		"""

		self.emit(text, MessageType.Error, origin)

	def json(self, data: dict):
		"""
		Выводит в терминал JSON-строку.

		:param data: Словарь для преобразования в JSON-строку.
		:type data: dict
		"""

		self.emit(orjson.dumps(data).decode())

	def warning(self, text: str, origin: str | None = None):
		"""
		Выводит в терминал предупреждения.

		:param text: Текст сообщения.
		:type text: str
		:param origin: Источник сообщения.
		:type origin: str | None
		"""

		self.emit(text, MessageType.Warning, origin)
