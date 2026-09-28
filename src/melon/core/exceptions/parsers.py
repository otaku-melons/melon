from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ..base.parsers.components.manifest import ContentTypes

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
	"""Исключение: парсер уже существует."""

	def __init__(self, parser_name: str):
		"""
		Исключение: парсер уже существует.

		:param parser_name: Имя парсера.
		:type parser_name: str
		"""

		super().__init__(parser_name) 

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

	def __init__(self, content_type: "ContentTypes"):
		"""
		Исключение: неподдерживаемый тип контента.

		:param content_type: Тип контента.
		:type content_type: ContentTypes
		"""

		super().__init__(content_type.value) 

class UnsupportedFormatError(Exception):
	"""Исключение: неподдерживаемый формат JSON."""

	def __init__(self, title_format: str | None = None):
		"""
		Исключение: неподдерживаемый формат JSON.

		:param title_format: Название формата.
		:type title_format: str | None
		"""

		title_format = f" \"{title_format}\"" if title_format else ""
		super().__init__(f"Unsupported format{title_format}.")
