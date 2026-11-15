from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .....utils.collector import Collector

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity

	from .....core.base.source_operator import BaseSourceOperator

class BaseParserTarget(ABC):
	"""Базовая цель для парсинга."""

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@property
	def is_used(self) -> bool:
		"""Состояние: используется ли этот тип цели."""

		return self._IsUsed()

	#==========================================================================================#
	# >>>>> PROTECTED METHODS <<<<< #
	#==========================================================================================#

	@abstractmethod
	def _GetSlugs(self) -> list[str]:
		"""
		Возвращает список алиасов для парсинга.

		:param data: Данные обработанной команды.
		:type data: CommandEntity
		:return: Список алиасов.
		:rtype: list[str]
		"""

		pass

	@abstractmethod
	def _IsUsed(self) -> bool:
		"""
		Проверяет, используется ли текущий тип цели.

		:return: Возвращает `True`, если используется ли текущий тип цели.
		:rtype: bool
		"""

		pass

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, source_operator: "BaseSourceOperator", data: "CommandEntity"):
		"""
		Базовая цель для парсинга.

		:param source_operator: Оператор источника.
		:type source_operator: BaseSourceOperator
		:param data: Данные обработанной команды.
		:type data: CommandEntity
		"""

		self._SourceOperator = source_operator
		self._Data = data

		self._Printer = self._SourceOperator.portals.printer

	def get_slugs(self) -> list[str]:
		"""
		Возвращает список алиасов для парсинга.

		:return: Список алиасов.
		:rtype: list[str]
		"""

		return self._GetSlugs()

class PassingTarget_Collection(BaseParserTarget):
	"""Цель для парсинга: коллекция."""

	def _GetSlugs(self) -> list[str]:
		"""
		Возвращает список алиасов для парсинга.

		:param data: Данные обработанной команды.
		:type data: CommandEntity
		:return: Список алиасов.
		:rtype: list[str]
		"""

		Filename: str | None = self._Data.get_key_value("--collection", expected_type = str)
		if Filename == ".": Filename = None
		collector = Collector(self._SourceOperator, Filename)
		collector.load()
		Slugs = list(collector.slugs)
		self._Printer.emit(f"Titles in collection: {len(Slugs)}.")

		return Slugs

	def _IsUsed(self) -> bool:
		"""
		Проверяет, используется ли текущий тип цели.

		:return: Возвращает `True`, если используется ли текущий тип цели.
		:rtype: bool
		"""

		return self._Data.check_key("--collection")

class PassingTarget_ID(BaseParserTarget):
	"""Цель для парсинга: тайтл по ID."""

	def _GetSlugs(self) -> list[str]:
		"""
		Возвращает список алиасов для парсинга.

		:return: Список алиасов.
		:rtype: list[str]
		"""

		ID: int | None = self._Data.get_key_value("--id", expected_type = int)
		if not ID: return []

		SlugByID = self._SourceOperator.shared_data.journal.get_slug_by_id(ID)
		if SlugByID: return [SlugByID]
		self._Printer.warning(f"Title with ID {SlugByID} uncached.")

		return []

	def _IsUsed(self) -> bool:
		"""
		Проверяет, используется ли текущий тип цели.

		:return: Возвращает `True`, если используется ли текущий тип цели.
		:rtype: bool
		"""

		return self._Data.check_key("--id")

class PassingTarget_Last(BaseParserTarget):
	"""Цель для парсинга: последний обработанный тайтл."""

	def _GetSlugs(self) -> list[str]:
		"""
		Возвращает список алиасов для парсинга.

		:return: Список алиасов.
		:rtype: list[str]
		"""

		Slugs: list[str] = []
		LastParsedSlug = self._SourceOperator.shared_data.last_parsed_slug

		if LastParsedSlug: Slugs.append(LastParsedSlug)
		else: self._Printer.warning("Last slug undefined. Parse anything firstly.")

		return Slugs

	def _IsUsed(self) -> bool:
		"""
		Проверяет, используется ли текущий тип цели.

		:return: Возвращает `True`, если используется ли текущий тип цели.
		:rtype: bool
		"""

		return self._Data.check_flag("-last")

class PassingTarget_Local(BaseParserTarget):
	"""Цель для парсинга: локальные тайтлы."""

	def _GetSlugs(self) -> list[str]:
		"""
		Возвращает список алиасов для парсинга.

		:return: Список алиасов.
		:rtype: list[str]
		"""

		collector = Collector(self._SourceOperator)
		self._SourceOperator.portals.printer.templates.collector.start()
		ScanningResult = collector.collect_local()
		self._Printer.templates.collector.collected(ScanningResult.added)

		return list(ScanningResult.slugs)

	def _IsUsed(self) -> bool:
		"""
		Проверяет, используется ли текущий тип цели.

		:return: Возвращает `True`, если используется ли текущий тип цели.
		:rtype: bool
		"""

		return self._Data.check_flag("-local")

class PassingTarget_Slug(BaseParserTarget):
	"""Цель для парсинга: тайтл по алиасу."""

	def _GetSlugs(self) -> list[str]:
		"""
		Возвращает список алиасов для парсинга.

		:return: Список алиасов.
		:rtype: list[str]
		"""

		Slug: str = self._Data.get_position_value("TARGET", expected_type = str, important = True)
		TargetSlug: str | None = self._SourceOperator.extract_slug_from_string(Slug)
		if TargetSlug: return [TargetSlug]
		else: self._Printer.warning("Unable to parse title slug from target.")

		return []

	def _IsUsed(self) -> bool:
		"""
		Проверяет, используется ли текущий тип цели.

		:return: Возвращает `True`, если используется ли текущий тип цели.
		:rtype: bool
		"""

		return not any((
			self._Data.check_flag("-last"),
			self._Data.check_flag("-local"),

			self._Data.check_key("--collection"),
			self._Data.check_key("--id"),
			self._Data.check_key("--updates"),
		))

class PassingTarget_Updates(BaseParserTarget):
	"""Цель для парсинга: обновления."""

	def _GetSlugs(self) -> list[str]:
		"""
		Возвращает список алиасов для парсинга.

		:return: Список алиасов.
		:rtype: list[str]
		"""

		Period: int = self._Data.get_key_value("--period", expected_type = int) or 24
		self._Printer.emit("Collecting updates…")
		Slugs = list(self._SourceOperator.collect_slugs(Period))
		self._Printer.emit(f"Updates collected: {len(Slugs)}.")

		return Slugs

	def _IsUsed(self) -> bool:
		"""
		Проверяет, используется ли текущий тип цели.

		:return: Возвращает `True`, если используется ли текущий тип цели.
		:rtype: bool
		"""

		return self._Data.check_key("--updates")
