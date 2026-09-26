from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from pick import Picker

from dublib.functions.data import to_sequence

from ...base import BaseCommandProcessor
from ...base.templates import T_SingleParserRequired

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ....core.system_objects.manager.parser.extensions import ExtensionsOperator
	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	operation: tuple[str, bool] | None

class CustomPicker(Picker):
	"""Custom items picker."""

	@override
	def get_option_lines(self) -> list[str]:
		"""
		Build items lines (override to change style).

		:return: Items lines.
		:rtype: list[str]
		"""
		
		lines: list[str] = []

		for index, option in enumerate(self.options):

			if index in self.selected_indexes:
				checkbox = "✅️ "
			else:
				checkbox = "❌ "

			if index == self.index:
				prefix = f"{self.indicator} {checkbox}"
			else:
				prefix = f"{" " * len(self.indicator)} {checkbox}"

			lines.append(f"{prefix}{option}")

		return lines

class CommandProcessor(BaseCommandProcessor[Parameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> PRIVATE METHODS <<<<< #
	#==========================================================================================#

	def __run_tui(self, extensions_operator: "ExtensionsOperator"):
		"""
		Run TUI for switching extensions activation states.

		:param extensions_operator: Extensions operator.
		:type extensions_operator: ExtensionsOperator
		"""

		names: tuple[str, ...] = extensions_operator.names
		enabled: tuple[str, ...] = extensions_operator.enabled
		activated_indexes: list[int] = []

		for index in range(len(names)):
			name: str = names[index]

			if name in enabled:
				activated_indexes.append(index)

		picker = CustomPicker(
			options = names,
			title = "Switch state by [Space], save by [Enter], to cancel [Ctrl + C].",
			indicator = "►",
			multiselect = True,
			min_selection_count = 0,
		)
		picker.selected_indexes = activated_indexes
		
		try:
			pick_value = picker.start()
		except KeyboardInterrupt:
			self.printer.emit("Cancelled.")
			return

		pick_data: tuple[tuple, ...] = to_sequence(pick_value)
		enabled_by_tui: list[str] = [name for name, _ in pick_data]

		enabled_count: int = 0
		disabled_count: int = 0

		for name in names:
			if name in enabled_by_tui:
				if extensions_operator.enable(name):
					enabled_count += 1
			else:
				if extensions_operator.disable(name):
					disabled_count += 1
		
		if any((enabled_count, disabled_count)):
			extensions_operator.save_states()
			self.printer.emit(f"Enabled: {enabled_count}. Disabled: {disabled_count}.")
		else:
			self.printer.emit("No changes.")

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

		position = model.create_position("OPERATION", "Switch extension activation status.")
		position.add_key("--enable", description = "Enable extension.")
		position.add_key("--disable", description = "Disable extension.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Manage parser extensions activation states. By default run TUI."

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

		operation: tuple[str, bool] | None = None

		value: str | None = entity.get_position_value("OPERATION", expected_type = str)
		if value:
			state: bool = entity.check_key("--enable")
			operation = (value, state)

		return Parameters(
			required_parser =  prepared_data.required_parsers[0],
			operation = operation,
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

		parameters.required_parser.extensions.load_states()
		operation: tuple[str, bool] | None = parameters.operation

		if operation:
			if parameters.required_parser.extensions.set_state(*operation):
				self.printer.emit("Enabled." if operation[1] else "Disabled.")
			else:
				self.printer.emit("No changes.")
		else:
			self.__run_tui(parameters.required_parser.extensions)

		return True
