from prettytable import PLAIN_COLUMNS, PrettyTable

from ...manager.parser.enums import ExportResult
from ._base import _BaseTemplatesSection

class ManagerTemplates(_BaseTemplatesSection):
	"""Расширенные шаблоны вывода: системный менеджер."""

	def exported(self, result: ExportResult):
		"""
		Шаблон вывода: результат экспорта настроек.

		:param result: Результат экспорта настроек.
		:type result: ExportResult
		"""

		match result:
			case ExportResult.Missing: self.printer.emit("Preset missing. Skipped.")
			case ExportResult.Installed: self.printer.emit("Config installed.")
			case ExportResult.AlreadyExists: self.printer.emit("Config already exists. Skipped.")
			case ExportResult.Overwtitten: self.printer.emit("Config overwritten.")
			case ExportResult.Merged: self.printer.emit("Config merged with preset.")

	def parsers_table(self, columns: dict[str, list[str]]):
		"""
		Шаблон вывода: таблица парсеров.

		:param columns: Словарь данных для вывода.
		:type columns: dict[str, list[str]]
		"""

		TableObject = PrettyTable()
		TableObject.set_style(PLAIN_COLUMNS)
		Implementations = ("collect",)
		ImplementationStatuses = {
			"True": "[green]true[/]",
			"False": "[yellow]false[/]",
			"None": "[red]error[/]",
		}

		for DomainIndex in range(len(columns["DOMAIN"])):
			columns["DOMAIN"][DomainIndex] = f"[i]{columns["DOMAIN"][DomainIndex]}[/]"

		for ColumnName in Implementations:

			for StatusIndex in range(len(columns[ColumnName])):
				columns[ColumnName][StatusIndex] = ImplementationStatuses[columns[ColumnName][StatusIndex]]

		for ColumnName in columns.keys():
			Buffer = f"[b]{ColumnName}[/]"
			TableObject.add_column(Buffer, columns[ColumnName])

		TableObject.align = "l"
		TableObject.sortby = "[b]{NAME}[/]"
		TableString = str(TableObject).strip()
		self.printer.emit(TableString if TableString else "Parsers not installed.")

