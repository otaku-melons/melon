from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ...core.system_objects.manager.parser_operator import ParserOperator

@dataclass(frozen = True)
class BaseParameters:
	"""Base parameters."""

	pass

@dataclass(frozen = True)
class T_ForceModeRequired(BaseParameters):
	"""Template: force mode available."""

	force_mode: bool

@dataclass(frozen = True)
class T_MultipleParsersRequired(BaseParameters):
	"""Template: multiple parsers selection available."""

	required_parsers: tuple["ParserOperator", ...]

@dataclass(frozen = True)
class T_OptionalSingleParser(BaseParameters):
	"""Template: single optional parser required."""

	required_parser: "ParserOperator | None"

@dataclass(frozen = True)
class T_SingleParserRequired(BaseParameters):
	"""Template: single parser required."""

	required_parser: "ParserOperator"
