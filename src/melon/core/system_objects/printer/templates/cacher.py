from typing import TYPE_CHECKING

from ._base import _BaseTemplatesSection

if TYPE_CHECKING:
	from .....utils.cacher import CachingResult

class CacherTemplates(_BaseTemplatesSection):
	"""Расширенные шаблоны вывода: оператор кэширования пар ID-алиас."""

	def result(self, result: "CachingResult"):
		"""
		Шаблон вывода: оператор кэширования пар ID-алиас.

		:param result: Результат кэширования.
		:type result: CachingResult
		"""

		self.printer.emit(f"Total: {result.total_files}. Found in cache: {result.found_in_cache}. Cached: {result.cached}. Updated: {result.updated}.")

		if result.errors:
			self.printer.emit("[bold]Errors:[/]")
			for Error in result.errors:
				self.printer.emit(f" - [red]{Error}.json[/]")

