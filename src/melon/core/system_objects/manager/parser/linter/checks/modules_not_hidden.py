import os
from pathlib import Path
from typing import TYPE_CHECKING, override

from ..base import BaseCheck
from ..enums import ChecksStatuses

if TYPE_CHECKING:
	from ...operator import ParserOperator

class Check(BaseCheck):
	"""Linter check."""	

	@override
	def _check(self, operator: "ParserOperator"):
		"""
		Process linter check. 

		Use `_emit()` or `_ok()` to interrupt checking. If no stop signal rised check considered successfully completed.

		:param operator: Parser operator.
		:type operator: ParserOperator
		"""

		allowed_scripts: tuple[str, ...] = ("__init__", "manga", "ranobe", "settings")

		for entry in os.scandir(operator.path):
			if entry.is_file() and entry.name.endswith(".py"):
				file_path = Path(entry.name)
				stem: str = file_path.stem

				if stem not in allowed_scripts:
					self._emit(ChecksStatuses.Warning, f"Script file <b>{stem}</b> should be in modules subdirectory.")
