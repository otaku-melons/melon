from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ...core.base.source_operator import BaseSourceOperator
	from ...core.system_objects.manager.parsers.operator import ParserOperator

@dataclass
class _InternalStorage:
	"""Command processor internal data."""

	mirror: str | None = None
	source_operators: dict[str, "BaseSourceOperator"] = field(default_factory = dict)

	is_json_output: bool = False
	is_force_mode: bool = False
	is_mirror_available: bool = False
	is_multiple_parsers_allowed: bool = False

@dataclass(frozen = True)
class PreparedData:
	"""Prepared from templates data."""

	required_parsers: tuple["ParserOperator", ...]
	force_mode: bool
	is_json_output: bool

@dataclass(frozen = True)
class ProcessorOptions:
	"""
	Processor options.

	If `require_installed_parsers` disabled, `check_parsers_dependencies` also will be disabled by default.
	"""

	use_timer: bool = True
	require_installed_parsers: bool = True
	check_parsers_dependencies: bool = True

	def __post_init__(self):
		"""Run after instance initialization."""

		if not self.require_installed_parsers:
			object.__setattr__(self, "check_parsers_dependencies", False)
