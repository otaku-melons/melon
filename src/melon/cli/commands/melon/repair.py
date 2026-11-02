from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableType

from ....core import exceptions
from ....core.base.formats.base_format.enums import By
from ....core.base.parser.enums import ImagesLevel
from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Required by command processor parameters."""

	filename: str
	target_id: int
	images_level: ImagesLevel
	is_target_chapter: bool

class CommandProcessor(CommandProcessorTemplate[Parameters]):
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

		position = model.create_position("FILE", "Title filename with or without type.", important = True)
		position.set_argument()

		position = model.create_position("TARGET", "Target to repairing.", important = True)
		position.add_key("--branch", value_type = ValidableType.UnsignedInteger, description = "Branch ID.")
		position.add_key("--chapter", value_type = ValidableType.UnsignedInteger, description = "Chapter ID.")

		self._add_parser_position(key = "--use")
		self._add_mirror_key()

		model.base.add_key("--images-level", value_type = ValidableType.UnsignedInteger, description = "Images downloadnig level: 0 – no downloads, 1 – only for metainfo, 3 – all.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.

		:return: Описание команды.
		:rtype: str
		"""

		return "Refrersh chapter content from source."

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

		filename: str = entity.get_position_value("FILE", expected_type = str, important = True)

		if not filename.endswith(".json"):
			filename += ".json"

		image_level_value: int | None = entity.get_key_value("--images-level", expected_type = int, not_found_error = False)
		image_level: ImagesLevel = ImagesLevel(image_level_value) if image_level_value else ImagesLevel.METAINFO

		return Parameters(
			required_parser = prepared_data.required_parsers[0],
			filename = filename,
			target_id = entity.get_position_value("TARGET", expected_type = int, important = True),
			images_level = image_level,
			is_target_chapter = entity.check_key("--chapter"),
		)

	@override
	def _process(self, parameters: Parameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Required by command processor parameters.
		:type parameters: Parameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		source_operator = self._launch_source_operator(parameters.required_parser)

		if not parameters.is_target_chapter:
			self.printer.error("For now only chapters supported as target to repairing.")
			return False

		typing_result = source_operator.get_content_type_by_file(parameters.filename)

		if not typing_result.slug or not typing_result.content_type:
			raise exceptions.parsing.ParsingError("Unprocessable title.")

		# TODO: Support force mode.
		parser = source_operator.launch_parser(typing_result.content_type, images_level = parameters.images_level)
		title = parser.init_empty_title(typing_result.slug)

		if title.load(parameters.filename, By.Filename):
			self.printer.emit(f"Loaded file: [i]{parameters.filename}[/].")
		else:
			self.printer.error(f"Unable load file: [b]{parameters.filename}[/].")
			return False

		self.printer.emit(f"Repairing chapter [b]{parameters.target_id}[/]… ")

		if not parser.repair(parameters.target_id):
			self.printer.warning("Chapter is empty. Repairing failure?")

		saving_result = parser.save()
		self.printer.templates.parsing.saving_result(saving_result)

		return True
