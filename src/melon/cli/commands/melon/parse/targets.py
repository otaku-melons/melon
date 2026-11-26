from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, override
from uuid import uuid4

from .....utils.collector import Collector

if TYPE_CHECKING:
	from collections.abc import Sequence

	from dublib.cli.terminalyzer import CommandEntity

	from .....core.base.source_operator import BaseSourceOperator
	from .....core.system_objects.printer import Printer

class BaseParsingTarget(ABC):
	"""Base parsing target."""

	def __init__(self, source_operator: "BaseSourceOperator", entity: "CommandEntity"):
		"""
		Base parsing target.

		Args:
			source_operator (BaseSourceOperator): Source operator.
			entity (CommandEntity): Command entity.
		"""

		self._source_operator: BaseSourceOperator = source_operator
		self._entity: CommandEntity = entity

		self._collection: Collector = Collector(self._source_operator, filename = str(uuid4()), sync = False)

		if self.is_used:
			if slugs := self._get_slugs():
				self.collection.add(slugs)

	@property
	def collection(self) -> Collector:
		"""Slugs collection."""

		return self._collection

	@property
	def entity(self) -> "CommandEntity":
		"""Command entity."""

		return self._entity

	@property
	def is_used(self) -> bool:
		"""Condition: is this target used."""

		return self._is_used()

	@property
	def printer(self) -> "Printer":
		"""Output operator."""

		return self._source_operator.portals.printer

	@property
	def source_operator(self) -> "BaseSourceOperator":
		"""Source operator."""

		return self._source_operator

	@abstractmethod
	def _get_slugs(self) -> "Sequence[str] | None":
		"""
		Get parser targeted slugs.

		Returns:
			Sequence[str] | None: Slugs for parsing.
		"""

		pass

	@abstractmethod
	def _is_used(self) -> bool:
		"""
		Check is this type of parser target used.

		Returns:
			bool: `True` if this type of parser target used.
		"""

		pass

class PassingTarget_Collection(BaseParsingTarget):
	"""Parsing target: collection."""

	@override
	def _get_slugs(self) -> "Sequence[str] | None":
		"""
		Get parser targeted slugs.

		Returns:
			Sequence[str] | None: Slugs for parsing.
		"""

		filename: str | None = self.entity.get_key_value("--collection", expected_type = str)

		if filename == ".":
			filename = "collection"

		self._collection = Collector(self.source_operator, filename, sync = True)
		self.collection.load()

		self.printer.emit(f"Titles in collection: {self.collection.count}.")

	@override
	def _is_used(self) -> bool:
		"""
		Check is this type of parser target used.

		Returns:
			bool: `True` if this type of parser target used.
		"""

		return self.entity.check_key("--collection")

class PassingTarget_ID(BaseParsingTarget):
	"""Parsing target: title by ID."""

	@override
	def _get_slugs(self) -> "Sequence[str] | None":
		"""
		Get parser targeted slugs.

		Returns:
			Sequence[str] | None: Slugs for parsing.
		"""

		title_id: int | None = self.entity.get_key_value("--id", expected_type = int)

		if not title_id:
			return

		slug: str | None = self.source_operator.shared_data.journal.get_slug_by_id(title_id)

		if slug:
			return (slug,)

		self.printer.warning(f"Title with ID {title_id} uncached.")

	@override
	def _is_used(self) -> bool:
		"""
		Check is this type of parser target used.

		Returns:
			bool: `True` if this type of parser target used.
		"""

		return self.entity.check_key("--id")

class PassingTarget_Last(BaseParsingTarget):
	"""Parsing target: last parsed title."""

	@override
	def _get_slugs(self) -> "Sequence[str] | None":
		"""
		Get parser targeted slugs.

		Returns:
			Sequence[str] | None: Slugs for parsing.
		"""

		if slug := self.source_operator.shared_data.last_parsed_slug:
			return (slug,)
		else:
			self.printer.warning("Last slug undefined. Parse anything firstly.")

	@override
	def _is_used(self) -> bool:
		"""
		Check is this type of parser target used.

		Returns:
			bool: `True` if this type of parser target used.
		"""

		return self.entity.check_flag("-last")

class PassingTarget_Local(BaseParsingTarget):
	"""Parsing target: local titles."""

	@override
	def _get_slugs(self) -> "Sequence[str] | None":
		"""
		Get parser targeted slugs.

		Returns:
			Sequence[str] | None: Slugs for parsing.
		"""

		self.source_operator.portals.printer.templates.collector.start()
		result = self.collection.collect_local()
		self.printer.templates.collector.collected(result.added)

	@override
	def _is_used(self) -> bool:
		"""
		Check is this type of parser target used.

		Returns:
			bool: `True` if this type of parser target used.
		"""

		return self.entity.check_flag("-local")

class PassingTarget_Slug(BaseParsingTarget):
	"""Parsing target: title by slug."""

	@override
	def _get_slugs(self) -> "Sequence[str] | None":
		"""
		Get parser targeted slugs.

		Returns:
			Sequence[str] | None: Slugs for parsing.
		"""

		string: str = self.entity.get_position_value("TARGET", expected_type = str, important = True)
		slug: str | None = self.source_operator.extract_slug_from_string(string)

		if not slug:
			self.printer.warning("Unable to parse title slug from target.")
			return

		return (slug,)

	@override
	def _is_used(self) -> bool:
		"""
		Check is this type of parser target used.

		Returns:
			bool: `True` if this type of parser target used.
		"""

		return not any((
			self.entity.check_flag("-last"),
			self.entity.check_flag("-local"),

			self.entity.check_key("--collection"),
			self.entity.check_key("--id"),
			self.entity.check_key("--updates"),
		))

class PassingTarget_Updates(BaseParsingTarget):
	"""Parsing target: updates."""

	@override
	def _get_slugs(self) -> "Sequence[str] | None":
		"""
		Get parser targeted slugs.

		Returns:
			Sequence[str] | None: Slugs for parsing.
		"""

		period: int = self.entity.get_key_value("--period", expected_type = int) or 24
		self.printer.emit("Collecting updates…")
		slugs: tuple[str, ...] = self.source_operator.collect_slugs(period)
		self.printer.emit(f"Updates collected: {len(slugs)}.")

		return slugs

	@override
	def _is_used(self) -> bool:
		"""
		Check is this type of parser target used.

		Returns:
			bool: `True` if this type of parser target used.
		"""

		return self.entity.check_key("--updates")
