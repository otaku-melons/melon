import importlib
import pkgutil
from typing import TYPE_CHECKING

from . import checks
from .base import BaseCheck
from .base.structs import CheckResult

if TYPE_CHECKING:
	from ..operator import ParserOperator
	
class Linter:
	"""Parser linter."""

	def __load_checks(self) -> tuple[BaseCheck, ...]:
		"""
		Load checks.

		:return: Checks types.
		:rtype: tuple[BaseCheck, ...]
		:raises TypeError: Check has incorrect type.
		"""

		checks_list: list[BaseCheck] = []
		
		for module_info in pkgutil.iter_modules(checks.__path__, checks.__name__ + "."):
			module = importlib.import_module(module_info.name)
			check_type: type = module.Check

			if issubclass(check_type, BaseCheck):
				checks_list.append(check_type())
			else:
				raise TypeError("Check has incorrect type.")

		return tuple(checks_list)

	def check(self, parser_operator: "ParserOperator") -> tuple[CheckResult, ...]:
		"""
		Run checks for parser.

		:param parser_operator: Parser operator.
		:type parser_operator: ParserOperator
		:return: Checks results.
		:rtype: tuple[CheckResult, ...]
		"""

		checks_order: tuple[BaseCheck, ...] = self.__load_checks()
		results: list[CheckResult] = []

		for check in checks_order:
			result: CheckResult = check.check(parser_operator)
			results.append(result)

		return tuple(results)
