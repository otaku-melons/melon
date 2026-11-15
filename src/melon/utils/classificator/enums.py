from dataclasses import dataclass
from enum import Enum

class Case(Enum):
	"""Letters case."""

	low = "low"
	up = "up"
	title = "title"

class ClassificatorType(Enum):
	"""Classificator type."""

	franchise = "franchises"
	genre = "genres"
	person = "persons"
	tag = "tags"

@dataclass(frozen = True)
class _DirectiveValidationData:
	"""
	Directive validation data

	- **values** – allowed values sequence or `None` for any value;
	* **allow_list** – condition: is multiple values allowed
	* **allow_empty** – condition: is directive without value allowed.
	"""

	values: tuple[str, ...] | None
	allow_list: bool
	allow_empty: bool

class Directive(Enum):
	"""Classification script directive."""

	delete = _DirectiveValidationData(values = None, allow_list = False, allow_empty = True)
	drop = _DirectiveValidationData(values = ("case", "delete", "type"), allow_list = True, allow_empty = True)
	case = _DirectiveValidationData(values = ("low", "title", "up"), allow_list = False, allow_empty = True)
	include = _DirectiveValidationData(values = None, allow_list = False, allow_empty = False)
	type = _DirectiveValidationData(values = ("franchises", "genres", "persons", "tags"), allow_list = False, allow_empty = False)
