import ast
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from dublib.functions.filesystem import text

from ..base import BaseCheck
from ..enums import ChecksStatuses

if TYPE_CHECKING:
	from pathlib import Path

	from ...operator import ParserOperator

@dataclass(frozen = True)
class ExportData:
	"""Extension name export data."""

	module_name: str
	class_name: str

class Check(BaseCheck):
	"""Linter check."""

	def __get_exported_classes_from_all(self, content: str) -> tuple[str, ...]:
		"""
		Get list of exported classes from `__all__` variable.

		:param content: Content of extensions export file: `__init__.py`.
		:type content: str
		:return: Exported classes names.
		:rtype: tuple[str, ...]
		"""
		
		tree = ast.parse(content)
		all_list: list[str] = []

		for node in tree.body:
			if isinstance(node, ast.Assign):
				for target in node.targets:
					if isinstance(target, ast.Name) and target.id == '__all__':
						if isinstance(node.value, (ast.List, ast.Tuple)):
							all_list = [ast.literal_eval(elt) for elt in node.value.elts]

		return tuple(all_list)

	def __get_exported_extensions_data(self, content: str) -> tuple[ExportData, ...]:
		"""
		Collect exported extensions data from imports.

		:param content: Content of extensions export file: `__init__.py`.
		:type content: str
		:return: Exported extensions data.
		:rtype: tuple[ExportData, ...]
		"""

		lines: tuple[str, ...] = tuple(line.strip() for line in content.split("\n"))
		imports: tuple[str, ...] = tuple(filter(lambda line: line.startswith("from "), lines))

		exported: list[ExportData] = []

		for import_line in imports:
			match = re.fullmatch(self.__pattern, import_line)

			if not match:
				self._emit(ChecksStatuses.Error, "Extension name export error.")

			module_name: str = match.group(1)
			class_name: str = match.group(2)

			exported.append(ExportData(module_name, class_name))

		return tuple(exported)

	@override
	def _check(self, operator: "ParserOperator"):
		"""
		Process linter check. 

		Use `_emit()` or `_ok()` to interrupt checking. If no stop signal rised check considered successfully completed.

		:param operator: Parser operator.
		:type operator: ParserOperator
		"""

		extensions_diresctory: "Path" = operator.path / "extensions"
		if not extensions_diresctory.exists():
			self._emit(ChecksStatuses.Skipped, "Extensions not found.")

		extensions_module: "Path" = operator.path / "extensions" / "__init__.py"
		if not extensions_module.exists():
			self._emit(ChecksStatuses.Error, "Extensions names not exported.")

		content: str = text.read(extensions_module)

		extensions_names: tuple[str, ...] = operator.extensions.names

		exported: tuple[ExportData, ...] = self.__get_exported_extensions_data(content)
		exported_names: tuple[str, ...] = tuple(element.module_name for element in exported)
		exported_classes: tuple[str, ...] = tuple(element.class_name for element in exported)

		all_names: tuple[str, ...] = self.__get_exported_classes_from_all(content)

		for name in extensions_names:
			if name not in exported_names:
				self._emit(ChecksStatuses.Error, f"Extension <b>{name}</b> not exported.")

		for name in exported_classes:
			if name not in all_names:
				self._emit(ChecksStatuses.Error, f"Extension class name <b>{name}</b> isn't present in <b>__all__</b> list.")

	def _post_init(self):
		"""This method will be executed after instance initialization."""

		self.__pattern: str = r"from \.(\w+) import Extension as (\w+)"
