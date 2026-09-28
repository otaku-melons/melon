from typing import TYPE_CHECKING, override

import questionary

from dublib.cli.text_styler import FastStyler

from ....utils.assistant import Assistant
from ....utils.assistant.structs import ExtensionData
from ...base.structs import PreparedData, ProcessorOptions
from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

class CommandProcessor(CommandProcessorTemplate[T_SingleParserRequired]):
	"""Обработчик команды."""

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

		return "Initialize new parser extension."

	@override
	def _export_options(self) -> ProcessorOptions:
		"""
		Возвращает настройки обработчика.

		:return: Настройки обработчика.
		:rtype: ProcessorOptions
		"""

		return ProcessorOptions(use_timer = False)
		
	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> T_SingleParserRequired:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: T_SingleParserRequired
		"""

		return T_SingleParserRequired(
			required_parser = prepared_data.required_parsers[0],
		)

	@override
	def _post_init(self):
		"""Execute after instance initialization."""

		self.__kbi_msg: str = FastStyler("Cancelled.").colorize.red

	@override
	def _process(self, parameters: T_SingleParserRequired) -> bool:
		"""
		Выполняет команду.

		:param parameters: Required by command processor parameters.
		:type parameters: T_SingleParserRequired
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		self.printer.emit("<i>Press [Ctrl + C] to cancel initialization.</i>")
		name: str | None = questionary.text("Extension name:").ask(kbi_msg = self.__kbi_msg)
		if name is None: return False
		class_name: str | None = questionary.text("Class name (if empty will be used default):").ask(kbi_msg = self.__kbi_msg)
		
		if class_name is None:
			return False
		elif class_name == "":
			class_name = None
			self.printer.emit("Used default class name <i>Extension.</i>")

		is_enable: bool | None = questionary.confirm("Enable extension?").ask(kbi_msg = self.__kbi_msg)
		if is_enable is None: return False

		data = ExtensionData(parameters.required_parser.name, name, class_name, is_enable)
		assistant = Assistant(self._system_objects)
		assistant.initialize_extension(data)

		return True
