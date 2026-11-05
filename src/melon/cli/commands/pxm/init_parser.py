from typing import TYPE_CHECKING, override

import questionary

from dublib.validators import types

from ....core.base.parser.enums import ContentType
from ....utils.assistant import Assistant
from ....utils.assistant.structs import ParserData
from ...base.structs import PreparedData, ProcessorOptions
from ...base.templates import BaseParameters
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

class CommandProcessor(CommandProcessorTemplate[BaseParameters]):
	"""Command processor."""

	#==========================================================================================#
	# >>>>> PRIVATE METHODS <<<<< #
	#==========================================================================================#

	def __ask_content_types(self) -> tuple[ContentType, ...] | None:
		"""
		Ask content types and parse it.

		:return: Content types.
		:rtype: tuple[ContentType, ...] | None
		"""

		choice: str | None = questionary.select("Content types:", choices = ("manga", "ranobe", "all")).ask(kbi_msg = self.__kbi_msg)

		if choice is None:
			return
		elif choice == "all":
			return (ContentType.Manga, ContentType.Ranobe)

		return (ContentType(choice),)

	def __ask_domain(self) -> str | None:
		"""
		Ask source domain while not valid.

		:return: Source domain.
		:rtype: str | None
		"""

		while True:
			domain: str | None = questionary.text("Source domain:").ask(kbi_msg = self.__kbi_msg)

			if not domain:
				return
			elif types.Domain.validate(domain):
				return domain
			else:
				self.printer.error("Incorrect domain format.")

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

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

		return "Initialize new parser."

	@override
	def _export_options(self) -> ProcessorOptions:
		"""
		Возвращает настройки обработчика.

		:return: Настройки обработчика.
		:rtype: ProcessorOptions
		"""

		return ProcessorOptions(use_timer = False)

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
	def _post_init(self):
		"""Execute after instance initialization."""

		self.__kbi_msg: str = "[red]Cancelled.[/]"

	@override
	def _process(self, parameters: BaseParameters) -> bool | None:
		"""
		Process command.

		Args:
			parameters (BaseParameters): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		self.printer.emit("[i]Press [Ctrl + C] to cancel initialization.[/]")
		name: str | None = questionary.text("Parser name:").ask(kbi_msg = self.__kbi_msg)
		if name is None: return False
		domain: str | None = self.__ask_domain()
		if domain is None: return False
		content_types: tuple[ContentType, ...] | None = self.__ask_content_types()
		if content_types is None: return False

		data = ParserData(name, domain, content_types)
		assistant = Assistant(self._system_objects)

		assistant.initialize_parser(data)
