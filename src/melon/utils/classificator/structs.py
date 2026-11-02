from dataclasses import dataclass
from pathlib import Path

from .enums import Case, ClassificatorType, Directive

@dataclass
class WorkData:
	"""Данные процесса обработки скрипта."""

	current_type: ClassificatorType | None = None
	current_case: Case | None = None
	is_delete: bool = False

@dataclass(frozen = True)
class ClassificationResult:
	"""Результат обработки классификатора."""

	is_operation_found: bool = False
	name: str | None = None
	type: ClassificatorType | None = None
	delete: bool | None = None
	is_renamed: bool | None = None

	def to_dict(self) -> dict:
		"""
		Возвращает словарное представление объекта.

		:return: Словарное представление объекта.
		:rtype: dict
		"""

		return {
			"is_operation_found": self.is_operation_found,
			"name": self.name,
			"type": self.type.name.lower() if self.type else None,
			"delete": self.delete,
			"is_renamed": self.is_renamed,
		}

@dataclass(frozen = True)
class ExecutableLine:
	"""Исполняемая строка скрипта."""

	file: Path
	number: int
	value: str

	@property
	def is_operation(self) -> bool:
		"""Состояние: представляет ли строка операцию."""

		return self.value.startswith("*")

	def is_directive(self, directive: Directive | None = None) -> bool:
		"""
		Проверяет, представляет ли исполняемая строка скрипта директиву.

		:param directive: Тип директивы для конкретизации проверки. По умолчанию любая директива.
		:type directive: Directive | None
		:return: Возвращает `True`, если строка представляет соответствующую директиву.
		:rtype: bool
		"""

		if directive:
			return self.value.startswith(f"@{directive.name}")

		return self.value.startswith("@")

@dataclass(frozen = True)
class Operation:
	"""Представление операции над классификатором."""

	name: str
	type: ClassificatorType | None
	delete: bool | None
	rename: str | None
	case: Case | None

	def process(self, value: str) -> str | None:
		"""
		Обрабатывает значение.

		:param value: Обрабатываемое значение.
		:type value: str
		:return: Результат обработки.
		:rtype: str | None
		"""

		if self.delete:
			return None

		if self.rename:
			return self.rename

		match self.case:
			case Case.Low: return value.lower()
			case Case.Title: return value.title()
			case Case.Up: return value.upper()

		return value

@dataclass(frozen = True)
class ScriptValidationError:
	"""Данные ошибки валидации скрипта."""

	line: ExecutableLine
	message: str
