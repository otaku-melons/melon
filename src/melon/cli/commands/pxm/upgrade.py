from typing import TYPE_CHECKING, override

from ...base import BaseCommandProcessor
from ...base.templates import BaseParameters

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

class CommandProcessor(BaseCommandProcessor[BaseParameters]):
	"""Command processor."""

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Build commands model.

		Args:
			model (CommandModel): Commands model.

		Returns:
			CommandModel: Commands model.
		"""

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Upgrade Melon."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> BaseParameters:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: BaseParameters
		"""

		return BaseParameters()

	@override
	def _process(self, parameters: BaseParameters) -> bool | None:
		"""
		Process command.

		Args:
			parameters (BaseParameters): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		self.printer.emit(f"Repository: [i]{self.system_objects.options.REPOS}[/i]")
		self.system_objects.manager.upgrade()
