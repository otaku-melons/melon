from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from prettytable import PrettyTable

from dublib.cli.text_styler import FastStyler
from dublib.functions.data import stringify_float

from ....core.system_objects.manager.parser.linter.base.structs import CheckResult
from ....core.system_objects.manager.parser.linter.enums import ChecksStatuses
from ...base import BaseCommandProcessor
from ...base.templates import T_SingleParserRequired

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass
class Statistics:
	"""Linting statistics."""

	total: int
	skipped: int = 0
	errors: int = 0
	warnings: int = 0

	@property
	def passed(self) -> int:
		"""Passed checks count."""

		return self.total - self.skipped - self.errors - self.warnings

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	pass

class CommandProcessor(BaseCommandProcessor[Parameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> PRIVATE METHODS <<<<< #
	#==========================================================================================#

	def __colorize_text(self, status: ChecksStatuses, text: str) -> str:
		"""
		Colorize text according check status.

		:param status: Checks statuses enumeration.
		:type status: ChecksStatuses
		:param text: Text for colorization.
		:type text: str
		:return: Colorized text.
		:rtype: str
		"""

		match status:
			case ChecksStatuses.OK: return FastStyler(text).colorize.green
			case ChecksStatuses.Skipped: return FastStyler(text).colorize.bright_cyan
			case ChecksStatuses.Error: return FastStyler(text).colorize.red
			case ChecksStatuses.Warning: return FastStyler(text).colorize.yellow

		return text

	def __print_results(self, results: tuple[CheckResult, ...]):
		"""
		Print results.

		:param results: Checks results.
		:type results: tuple[CheckResult, ...]
		"""

		results_count: int = len(results)

		headers: tuple[str, ...] = ("Progress", "Status", "Name", "Message")
		headers = tuple(FastStyler(string).decorate.bold for string in headers)

		table = PrettyTable(headers)
		table.border = False
		# table.header = False
		table.align = "l"
		table.left_padding_width = 0
		table.right_padding_width = 4

		for index in range(results_count):
			result = results[index]
			number: int = index + 1
			progress: float = number / results_count * 100.0

			progress_string: str = stringify_float(progress, round_factor = 1) + "%"
			progress_string = progress_string.rjust(5)
			progress_string = f"[{number}/{results_count} {progress_string}]"
			status: str = "passed" if result.status is ChecksStatuses.OK else result.status.name.lower()
			name: str = result.name
			message: str = result.message or ""

			row: list[str] = [progress_string, status, name, message]
			row = [self.__colorize_text(result.status, string) for string in row]

			table.add_row(row)

		self.printer.emit(table.get_string())

	def __print_statistics(self, statistics: Statistics):
		"""
		Print statisctics.

		:param statistics: Linting statistics.
		:type statistics: Statistics
		"""

		passed: str = FastStyler(str(statistics.passed)).colorize.green

		if statistics.errors:
			passed = FastStyler(str(statistics.passed)).colorize.red
		elif statistics.warnings:
			passed = FastStyler(str(statistics.passed)).colorize.yellow

		errors: str = FastStyler(str(statistics.errors)).colorize.red if statistics.errors else FastStyler("0").colorize.green
		warnings: str = FastStyler(str(statistics.warnings)).colorize.yellow if statistics.warnings else FastStyler("0").colorize.green
		skipped: str = FastStyler(str(statistics.skipped)).colorize.bright_cyan if statistics.skipped else "0"

		self.printer.emit(f"Total <b>{statistics.total}</b>. Passed {passed}. Skipped: {skipped}. Errors: {errors}. Warnings: {warnings}.")

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Генерирует модель команды.
		
		:param model: Шаблон модели команды.
		:type model: Command
		:return: Модель команды.
		:rtype: CommandModel
		"""

		self._add_parser_position()

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Lint parser."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> Parameters:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: Parameters
		"""

		return Parameters(
			required_parser =  prepared_data.required_parsers[0]
		)

	@override
	def _process(self, parameters: Parameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Параметры, требуемые обработчиком.
		:type parameters: Parameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		linting_results = parameters.required_parser.lint()

		statistics = Statistics(len(linting_results))

		for result in linting_results:
			match result.status:
				case ChecksStatuses.Skipped: statistics.skipped += 1
				case ChecksStatuses.Error: statistics.errors += 1
				case ChecksStatuses.Warning: statistics.warnings += 1

		self.__print_results(linting_results)
		self.__print_statistics(statistics)

		return not bool(statistics.errors)

