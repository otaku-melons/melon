import traceback
from dataclasses import dataclass
from json import JSONDecodeError
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableType

from .....core import exceptions
from .....core.base.parser.enums import ContentType, ImagesLevel
from .....core.system_objects.printer.templates.parsing import ParsingStatistics
from .....utils.classificator import AttributesClassificator
from ....base.templates import T_ForceModeRequired, T_SingleParserRequired
from .._base import CommandProcessorTemplate
from . import targets
from .enums import ParsingSignal

if TYPE_CHECKING:
	from pathlib import Path

	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from .....core.base.formats.base_format.controller import BaseTitleController
	from .....core.base.formats.base_format.data import BaseTitleData
	from .....core.base.parser import BaseParser
	from .....core.base.source_operator import BaseSourceOperator
	from ....base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_ForceModeRequired, T_SingleParserRequired):
	"""Required by command processor parameters."""

	target: targets.BaseParsingTarget
	parse_from: str | None

	is_sorting_enabled: bool
	is_amending_enabled: bool
	images_level: ImagesLevel
	is_classificator_enabled: bool
	is_cold_saving: bool

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Command processor."""

	@property
	def classificator(self) -> AttributesClassificator | None:
		"""Attributes classificator."""

		return self.__classificator

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Build commands model.

		Args:
			model (CommandModel): Commands model.

		Returns:
			CommandModel: Commands model.
		"""

		position = model.create_position("TARGET", "Target for parsing.", important = True)
		position.set_argument(description = "Title slug.")
		position.add_flag("-local", description = "Parse all locally saved titles.")
		position.add_flag("-last", description = "Parse last parsed title.")
		position.add_key("--collection", description = "Name of collection file. Put . to default [i]collection[/i].")
		position.add_key("--id", value_type = ValidableType.UnsignedInteger, description = "Title ID.")
		position.add_key("--updates", value_type = ValidableType.UnsignedInteger, description = "Parse updates for period in hours.")

		self._add_parser_position(key = "--use")
		self._add_force_mode_flag()

		model.base.add_flag("-no-amend", description = "Disable chapters content amending.")
		model.base.add_flag("-no-classificator", description = "Disable title attributes classificator.")
		model.base.add_flag("-no-cold-save", description = "Disable saving if local file does't exists.")
		model.base.add_flag("-sort", description = "Enable chapters sorting after parsing.")

		self._add_mirror_key()

		model.base.add_key("--from", description = "Skip titles before this slug.")
		model.base.add_key("--images-level", value_type = ValidableType.UnsignedInteger, description = "Images downloadnig level: 0 – no downloads, 1 – only for metainfo, 3 – all.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Parse titles."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> Parameters:
		"""
		Parse command parameters.

		Args:
			entity (CommandEntity): Command entity.
			prepared_data (PreparedData): Prepared from templates data.

		Returns:
			PARAMS: Command parameters.
		"""

		image_level_value: int | None = entity.get_key_value("--images-level", expected_type = int, not_found_error = False)
		image_level: ImagesLevel = ImagesLevel(image_level_value) if image_level_value else ImagesLevel.METAINFO

		return Parameters(
			required_parser = prepared_data.required_parsers[0],
			target = self.__get_parsing_targets(entity, prepared_data),
			parse_from = entity.get_key_value("--from", expected_type = str),

			force_mode = prepared_data.force_mode,
			is_sorting_enabled = entity.check_flag("-sort"),
			is_amending_enabled = not entity.check_flag("-no-amend"),
			images_level = image_level,
			is_classificator_enabled = not entity.check_flag("-no-classificator"),
			is_cold_saving = not entity.check_flag("-no-cold-save"),
		)

	@override
	def _post_init(self):
		"""Execute after instance initialization."""

		self.__classificator: AttributesClassificator | None = None

	@override
	def _process(self, parameters: Parameters) -> bool | None:
		"""
		Process command.

		Args:
			parameters (Parameters): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		start_index: int = 0

		if parameters.parse_from:
			target_start_index: int = self.__skip_slugs_before(parameters.target.collection.slugs, parameters.parse_from)
			if target_start_index: start_index = target_start_index

		if not parameters.target.collection.slugs:
			self.printer.error("No slugs for parsing.")
			return False

		self.__initialize_classificator(parameters)
		source_operator = self._launch_source_operator(parameters.required_parser)
		statistics = self.__parse_slugs(parameters, source_operator, start_index)
		self.printer.templates.parsing.summary(statistics)

	def __get_parsing_targets(self, data: "CommandEntity", prepared_data: "PreparedData") -> targets.BaseParsingTarget:
		"""
		Определяет цель для парсинга.

		:param data: Данные обработанной команды.
		:type data: CommandEntity
		:param prepared_data: Предподготолвенные данные.
		:type prepared_data: PreparedData
		:return: Цель для парсинга.
		:rtype: _BaseParserTarget
		"""

		source_operator = self._launch_source_operator(prepared_data.required_parsers[0])
		targets_types: tuple[type[targets.BaseParsingTarget], ...] = (
			targets.PassingTarget_Collection,
			targets.PassingTarget_ID,
			targets.PassingTarget_Last,
			targets.PassingTarget_Local,
			targets.PassingTarget_Slug,
			targets.PassingTarget_Updates,
		)

		for target_type in targets_types:
			target = target_type(source_operator, data)
			if target.is_used: return target

		raise exceptions.parsing.ParsingError("Unable determine parsing target.")

	def __initialize_classificator(self, parameters: Parameters):
		"""
		Initialize attributes classificator.

		Args:
			parameters (Parameters): Required by command parameters.
		"""

		if not parameters.is_classificator_enabled:
			return

		script_entry_point: Path = self.system_objects.options.CONFIGS_DIR / parameters.required_parser.name / "classificator" / "main.mcs"

		if not script_entry_point.exists():
			self.printer.debug("No classification script found.")
			return

		self.__classificator = AttributesClassificator(script_entry_point)
		self.__classificator.load()

	def __parse_slugs(self, parameters: Parameters, source_operator: "BaseSourceOperator", start_index: int) -> ParsingStatistics:
		"""
		Парсит набор алиасов тайтлов.

		:param parameters: Required by command processor parameters.
		:type parameters: Parameters
		:param source_operator: Оператор источника.
		:type source_operator: BaseSourceOperator
		:param slugs: Последовательность алиасов.
		:type slugs: Sequence[str]
		:param start_index: Индекс алиаса для старта парсинга.
		:type start_index: int
		:return: Статистика парсинга.
		:rtype: ParsingStatistics
		"""

		statistics: ParsingStatistics = ParsingStatistics(parameters.target.collection.count)
		slugs: tuple[str, ...] = parameters.target.collection.slugs
		parser: BaseParser | None = None

		for index in range(start_index, statistics.total):
			slug: str = slugs[index]
			source_operator.shared_data.set_last_parsed_slug(slug)

			current_content_type: ContentType = source_operator.get_content_type_by_slug(slug)

			if not parser or parser.content_type is not current_content_type:
				parser = source_operator.launch_parser(current_content_type, parameters.force_mode, parameters.images_level)

			title = parser.init_empty_title(slug)
			self.printer.templates.parsing.start(title.data, index, statistics.total)

			match self.__parse_safely(parameters, parser, title):

				case ParsingSignal.Break:
					break

				case ParsingSignal.NotFound:
					statistics.not_found += 1
					continue

				case ParsingSignal.Error:
					statistics.errors += 1
					continue

			if parameters.images_level is ImagesLevel.NO:
				self.printer.emit("Metainfo images downloading skipped.")
			else:
				parser.download_metainfo_images()

			if not title.is_local_file_loaded and not parameters.is_cold_saving:
				self.printer.emit("Cold saving disabled by flag. Skipped.")
			else:
				result = parser.save(parameters.is_sorting_enabled)
				self.printer.templates.parsing.saving_result(result)

				# Replace slug in collection if changed.
				if new_slug := result.is_slug_changed:
					parameters.target.collection.replace(slug, new_slug)
					self.printer.debug("Slug in collection updated.")

			statistics.parsed += 1

		return statistics

	def __parse_safely(self, parameters: Parameters, parser: "BaseParser", title: "BaseTitleController[BaseTitleData]") -> ParsingSignal:  # noqa: C901
		"""
		Выполняет парсинг тайта, отлавливая общие исключения.

		:param parameters: Required by command processor parameters.
		:type parameters: Parameters
		:param parser: Парсер.
		:type parser: BaseParser
		:param title: Контроллер тайтла.
		:type title: BaseTitleController
		:return: Сигнал парсинга.
		:rtype: ParsingSignal
		"""

		try:
			parser.parse()
			self.printer.emit(f"Title ID: [b]{title.data.id}[/b].")

			if self.classificator:
				self.classificator.process_title(title.data)
				self.printer.emit("Attributes classified.")

			if not parameters.force_mode:
				MergedChaptersCount = title.merge()
				if MergedChaptersCount: self.printer.emit(f"Merged {MergedChaptersCount} chapters.")

			if parameters.is_amending_enabled:
				if title.empty_chapters_count: parser.amend()
				else: self.printer.emit("No empty chapters. Amending skipped.")
			else:
				self.printer.emit("Amending skipped by flag.")

		except exceptions.parsing.AuthorizationRequiredError:
			return ParsingSignal.Break

		except exceptions.parsing.ParsingError:
			return ParsingSignal.Error

		except exceptions.parsing.TitleNotFoundError:
			return ParsingSignal.NotFound

		except (JSONDecodeError, exceptions.parsers.UnsupportedFormatError):
			self.printer.error("Unsupported JSON format or decoding error.")
			return ParsingSignal.Error

		except exceptions.utils.classificator.ClassificationError as exception:
			self.printer.error(str(exception), origin = "classificator")
			return ParsingSignal.Error

		except Exception:
			Traceback = traceback.format_exc().rstrip()
			self.printer.error("Current title skipped due to exception:")
			self.printer.emit(Traceback)
			return ParsingSignal.Error

		return ParsingSignal.OK

	def __skip_slugs_before(self, slugs: tuple[str, ...], starting_slug: str) -> int:
		"""
		Определяет стартовый индекс последовательности для парсинга.

		:param slugs: Алиасы тайтлов для парсинга.
		:type slugs: tuple[str, ...]
		:param starting_slug: Алиас, с которого необходимо начать парсинг.
		:type starting_slug: str
		:return: Индекс стартового алиаса или `-1`, если алиас не удалось найти.
		:rtype: int
		"""

		if starting_slug not in slugs:
			self.printer.warning("Starting slug not found in targets. Ignored.")
			return -1

		self.printer.emit(f"Parsing started from title: \"{starting_slug}\".")

		return slugs.index(starting_slug)
