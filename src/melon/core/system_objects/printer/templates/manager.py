from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, NoReturn, overload

from packaging.version import Version
from rich.table import Table

from ....base.parser.enums import ContentType
from ...manager.parser.enums import ExportResult
from ._base import _BaseTemplatesSection

if TYPE_CHECKING:
	from collections.abc import Callable, Sequence

	from ...manager.parser.operator import DependencyError

@dataclass(frozen = True)
class ParsersTableRow:
	"""Parser table row."""

	name: str
	version: Version | None
	content_types: tuple[ContentType, ...]
	domain: str
	collect: bool

class ManagerTemplates(_BaseTemplatesSection):
	"""Extended output templates: manager."""

	@overload
	def dependency_error(self, dependency_error: "DependencyError", critical: Literal[True]) -> NoReturn: ...
	@overload
	def dependency_error(self, dependency_error: "DependencyError", critical: Literal[False] = False): ...

	def dependency_error(self, dependency_error: "DependencyError", critical: bool = False) -> NoReturn | None:
		"""
		Emit message: dependency error.

		Args:
			dependency_error (DependencyError): Dependency error.
			critical (bool): Condition: is error critical and Melon must be stopped.
		"""

		printers: dict[bool, Callable] = {
			True: self.printer.critical,
			False: self.printer.emit,
		}

		if not dependency_error.is_installed:
			printers[critical](
				text = f"Dependency [b]{dependency_error.required_literal}[/b] isn't installed.",
				origin = dependency_error.parser_name,
			)
			return

		if not dependency_error.installed_version:
			printers[critical](
				text = f"Undetermined version of [b]{dependency_error.required_name}[/b], required [b]{dependency_error.required_version}[/b].",
				origin = dependency_error.parser_name,
			)
			return

		printers[critical](
			text = f"Unsolvable dependency: required [b]{dependency_error.required_literal}[/b], installed [b]{dependency_error.installed_literal}[/b].",
			origin = dependency_error.parser_name,
		)

	def exported(self, result: ExportResult):
		"""
		Emit message: config exported.

		Args:
			result (ExportResult): Config export result.
		"""

		match result:
			case ExportResult.Missing: self.printer.emit("Preset missing. Skipped.")
			case ExportResult.Installed: self.printer.emit("Config installed.")
			case ExportResult.AlreadyExists: self.printer.emit("Config already exists. Skipped.")
			case ExportResult.Overwtitten: self.printer.emit("Config overwritten.")
			case ExportResult.Merged: self.printer.emit("Config merged with preset.")

	def parsers_table(self, rows: "Sequence[ParsersTableRow]"):
		"""
		Emit message: parsers table.

		Args:
			rows (Sequence[ParsersTableRow]): Parsers table rows.
		"""

		table = Table(box = None, header_style = "bold")

		for column in ("Name", "Version", "Content", "Source", "collect"):
			table.add_column(column)

		for row in rows:
			version: str | None = str(row.version) if row.version else None
			content: str = ", ".join(content_type.value[0] for content_type in row.content_types)
			source: str = f"https://{row.domain}"
			collect: str = "[green]true[/green]" if row.collect else "[red]false[/red]"

			table.add_row(row.name, version, content, source, collect)

		self.printer.table(table)
