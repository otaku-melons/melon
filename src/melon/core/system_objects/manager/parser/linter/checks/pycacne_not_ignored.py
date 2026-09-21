from typing import TYPE_CHECKING, override

from dublib.functions.filesystem import text

from ..base import BaseCheck
from ..enums import ChecksStatuses

if TYPE_CHECKING:
	from pathlib import Path

	from ...operator import ParserOperator

class Check(BaseCheck):
	"""Linter check."""

	def __is_pycache_ignored(self, operator: "ParserOperator") -> bool:
		"""
		Check if *\\_\\_pycache\\_\\_* in `.gitignore`.

		:param operator: Parser operator.
		:type operator: ParserOperator
		:return: Return `True` if *\\_\\_pycache\\_\\_* in `.gitignore`.
		:rtype: bool
		"""

		gitignore_path: "Path" = operator.path / ".gitignore"

		if not gitignore_path.exists():
			return False

		lines: list[str] = text.read(gitignore_path, split = True, strip_level = 2)

		if "__pycache__" not in lines:
			return False

		return True			

	@override
	def _check(self, operator: "ParserOperator"):
		"""
		Process linter check. 

		Use `_emit()` or `_ok()` to interrupt checking. If no stop signal rised check considered successfully completed.

		:param operator: Parser operator.
		:type operator: ParserOperator
		"""

		git: "Path" = operator.path / ".git"

		if not git.exists():
			self._emit(ChecksStatuses.Skipped, "Git repository not found.")

		if not self.__is_pycache_ignored(operator):
			self._emit(ChecksStatuses.Warning, "<b>__pycache__</b> should be ignored.")