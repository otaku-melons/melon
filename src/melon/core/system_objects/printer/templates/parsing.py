from dataclasses import dataclass
from typing import TYPE_CHECKING

from dublib.functions.data import stringify_float

from ._base import _BaseTemplatesSection

if TYPE_CHECKING:
	from .....core.base.formats.base_format.chapter import BaseChapter
	from .....core.base.formats.base_format.data import BaseTitleData
	from .....core.base.formats.base_format.structs import SavingResult

@dataclass
class ParsingStatistics:
	"""Parsing statistics."""

	total: int
	parsed: int = 0
	not_found: int = 0
	errors: int = 0

class ParsingTemplates(_BaseTemplatesSection):
	"""Extended output templates: parsing."""

	def amending_end(self, count: int):
		"""
		Emit message: chapters amending end.

		Args:
			count (int): Amended chapters count.
		"""

		self.printer.emit(f"Amended chapters count: {count}.")

	def chapter_amended(self, chapter: "BaseChapter", progress: tuple[int, int], message: str | None = None):
		"""
		Emit message: chapter amended (warning if chapter empty).

		Args:
			chapter (BaseChapter): Chapter.
			progress (tuple[int, int]): Progress tuple: processed chapter index (numeration from 1) and total empty chapters count.
			message (str | None): Optional message about chapter amending.
		"""

		progress_string: str = f"[{progress[0]}/{progress[1]}]"
		chapter_note: str = "Paid chapter" if chapter.is_paid else "Chapter"
		result: str = "empty after amending" if chapter.is_empty else "amended"
		message = message.strip() if message else ""

		text = f"{progress_string} {chapter_note} {chapter.id} {result}.{message}"

		if chapter.is_empty: self.printer.warning(text)
		else: self.printer.emit(text)

	def chapter_repaired(self, chapter: "BaseChapter"):
		"""
		Emit message: chapter repaired.

		Args:
			chapter (BaseChapter): Chapter..
		"""

		note: str = "Paid chapter" if chapter.is_paid else "Chapter"
		self.printer.emit(f"{note} {chapter.id} repaired.")

	def progress(self, index: int, count: int):
		"""
		Emit message: parsing progress.

		Args:
			index (int): Processed title index.
			count (int): All titles count.
		"""

		number: int = index + 1
		progress: float = round(number / count * 100, 2)
		number_string: str = f"[magenta]{number}[/magenta]"
		progress_string: str = stringify_float(progress)
		progress_styled_string = f"[cyan]{progress_string}%[/cyan]"

		self.printer.progress_indicator.set_progress(progress)
		self.printer.emit(f"[{number_string} / {count} | {progress_styled_string}] ", end_line = False, flush = True)

	def saving_result(self, result: "SavingResult"):
		"""
		Emit message: title saving result.

		Args:
			result (SavingResult): Title saving result.
		"""

		if result.is_slug_changed:
			self.printer.emit("Title slug changed.")

		if result.is_saved: self.printer.emit("Saved.")
		else: self.printer.emit("No changes. Saving skipped.")

		if result.is_local_file_renamed:
			self.printer.emit("File renamed by new slug.")

		if result.unused_images_removed:
			self.printer.emit(f"Removed {result.unused_images_removed} unused images.")

	def start(self, title_data: "BaseTitleData", index: int, titles_count: int):
		"""
		Emit message: parsing started.

		Args:
			title_data (BaseTitleData): Title data.
			index (int): Title index.
			titles_count (int): All titles count.
		"""

		note_id: str = f" (ID: {title_data.id})" if title_data.id else ""

		if titles_count > 1:
			self.progress(index, titles_count)

		self.printer.emit(f"Parsing [b]{title_data.slug}[/b]{note_id}…")

	def summary(self, statistics: ParsingStatistics):
		"""
		Emit message: parsing ummary.

		Args:
			statistics (ParsingStatistics): Parsing statistics.
		"""

		self.printer.emit("===== SUMMARY =====")
		Parsed = f"[green]{statistics.parsed}[/green]" if statistics.parsed else f"[red]{statistics.parsed}[/red]"
		NotFound = f"[yellow]{statistics.not_found}[/yellow]" if statistics.not_found else f"[green]{statistics.not_found}[/green]"
		Errors = f"[red]{statistics.errors}[/red]" if statistics.errors else f"[green]{statistics.errors}[/green]"

		self.printer.progress_indicator.end()
		self.printer.emit(f"Parsed: {Parsed}. Not found: {NotFound}. Errors: {Errors}.")
