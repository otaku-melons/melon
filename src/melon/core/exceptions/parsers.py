from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ..base.parser.enums import ContentType

class ManifestError(Exception):
	"""Исключение: неверное определение манифеста."""

	def __init__(self, message: str):
		"""
		Исключение: неверное определение манифеста.

		:param message: Сообщение об ошибке.
		:type message: str
		"""

		super().__init__(message)

class ParserAlreadyExistsError(Exception):
	"""Exception: parser already exists."""

	def __init__(self, parser_name: str, is_installed: bool):
		"""
		Exception: parser already exists..

		Args:
			parser_name (str): Parser name.
			is_installed (bool): Is parser installed or found in repositories.
		"""

		self.__parser_name: str = parser_name
		self.__is_installed: bool = is_installed

		super().__init__(f"{parser_name} (found in repositories)" if is_installed else parser_name)

	@property
	def is_installed(self) -> bool:
		"""Condition: is parser installed."""

		return self.__is_installed

	@property
	def parser_name(self) -> str:
		"""Parser name."""

		return self.__parser_name

class ParserNotFoundError(Exception):
	"""Исключение: парсер не найден."""

	def __init__(self, parser_name: str):
		"""
		Исключение: парсер не найден.

		:param parser_name: Имя парсера.
		:type parser_name: str
		"""

		super().__init__(parser_name)

class TitleNotSetError(Exception):
	"""Исключение: не задан тайтл."""

	def __init__(self):
		"""Исключение: не задан тайтл."""

		super().__init__("Open title before using methods, that it requires.")

class RepositoryError(Exception):
	"""Исключение: ошибка работы с репозиториями."""

	def __init__(self, message: str):
		"""
		Исключение: ошибка работы с репозиториями.

		:param message: Сообщение об ошибке.
		:type message: str
		"""

		super().__init__(message)

class UnsupportedContentError(Exception):
	"""Исключение: неподдерживаемый тип контента."""

	def __init__(self, content_type: "ContentType"):
		"""
		Исключение: неподдерживаемый тип контента.

		:param content_type: Тип контента.
		:type content_type: ContentType
		"""

		super().__init__(content_type.value)

class UnsupportedFormatError(Exception):
	"""Exception: unsupported JSON format."""

	def __init__(self, message: str):
		"""
		Exception: unsupported JSON format.

		:param message: Error message or format name.
		:type message: str
		"""

		super().__init__(message)
