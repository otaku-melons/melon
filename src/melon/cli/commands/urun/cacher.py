from typing import TYPE_CHECKING, override

from .... import utils
from ...base.templates import T_MultipleParsersRequired
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

class CommandProcessor(CommandProcessorTemplate[T_MultipleParsersRequired]):
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

		self._add_parser_position(key = "--use", multiple = True)

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Run ID-slug caching."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> T_MultipleParsersRequired:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: T_MultipleParsersRequired
		"""

		return T_MultipleParsersRequired(prepared_data.required_parsers)

	@override
	def _process(self, parameters: T_MultipleParsersRequired) -> bool:
		"""
		Выполняет команду.

		:param parameters: Required by command processor parameters.
		:type parameters: T_MultipleParsersRequired
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		for parser_operator in parameters.required_parsers:
			self.printer.emit(f"Caching titles for <b>{parser_operator.name}</b>…")
			Cacher = utils.Cacher(self._launch_source_operator(parser_operator))
	
			result = Cacher.cache_parser_output()
			self.printer.templates.cacher.result(result)

		return True
