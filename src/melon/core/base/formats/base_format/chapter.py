from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from dublib.functions.data import deep_copy, zerotify
from dublib.functions.data.dictionary import insert_dictionary_after_key
from dublib.functions.data.string import remove_recurring_substrings

if TYPE_CHECKING:
	from collections.abc import Sequence

	from pydantic import BaseModel

	from ....html.interpreter import HyperTextInterpreter
	from ...parser import BaseParser
	from ...source_operator import BaseSourceOperator
	from ...structs.image import ImageData
	from .controller import BaseTitleController

class ExtraData:
	"""Chapter extra data."""

	def __init__(self, base_keys: "Sequence[str]"):
		"""
		Chapter extra data.

		Args:
			base_keys (Sequence[str]): Base key which is reserved for main data.
		"""

		self.__base_keys: tuple[str, ...] = tuple(base_keys)

		self.__data: dict[str, Any] = {}

	def clear(self):
		"""Clear extra data."""

		self.__data.clear()

	def exists(self, key: str) -> bool:
		"""
		Check is extra data with key exists.

		Args:
			key (str): Extra data key.

		Returns:
			bool: `True` if key exists.

		Raises:
			KeyError: Key is reserved by important values.
		"""

		if key in self.__base_keys:
			raise KeyError(f"Key \"{key}\" is reserved by important values.")

		return key in self.__data

	def from_dict(self, data: dict):
		"""
		Fill extra data from chapter dictionary extra fields.

		Args:
			data (dict): Extra data.
		"""

		self.clear()

		for key in data.keys():
			if key not in self.__base_keys:
				self.set(key, data[key])

	def get(self, key: str) -> Any:
		"""Summary.

		Args:
			key (str): Description.

		Returns:
			Any: Description.

		Raises:
			KeyError: Extra data key missing.
		"""

		return self.__data[key]

	def remove(self, key: str):
		"""
		Remove extra data.

		Args:
			key (str): Extra data key.
		"""

		if key in self.__data:
			del self.__data[key]

	def set(self, key: str, value: Any):
		"""
		Set extra data.

		Args:
			key (str): Key.
			value (Any): Data.

		Raises:
			KeyError: Key is reserved by important values.
		"""

		if key in self.__base_keys:
			raise KeyError(f"Key \"{key}\" is reserved by important values.")

		self.__data[key] = value

	def to_dict(self) -> dict:
		"""
		Get dictionary representation of data (make deep copy of inner dictionary).

		Returns:
			dict: Dictionary representation of data.
		"""

		return deep_copy(self.__data)

class BaseChapter(ABC):
	"""Base chapter."""

	def __init__(self, parser: "BaseParser", chapter_id: int):
		"""
		Base chapter.

		Args:
			parser (BaseParser): Parser.
			chapter_id (int): Chapter ID.
		"""

		self._parser: BaseParser[BaseSourceOperator, BaseModel, BaseTitleController] = parser
		self._html_interpreter: HyperTextInterpreter = self._parser.title.html_interpreter

		self._data: dict[str, Any] = {
			"id": chapter_id,
			"slug": None,
			"volume": None,
			"number": None,
			"name": None,
			"is_paid": None,
			"workers": [],
		}
		self._extra_data = ExtraData(tuple(self._data.keys()))

		self._post_init()

	def add_worker(self, worker: str):
		"""
		Add chapter worker.

		Args:
			worker (str): Worker details.
		"""

		workers: list[str] = self._data["workers"]

		if worker not in workers:
			workers.append(worker)

	def clear(self):
		"""Clear chapter data."""

		self._clear_content()
		self.extra_data.clear()

	def from_dict(self, data: dict):
		"""
		Parse data from chapter dictionary.

		Args:
			data (dict): Chapter dictionary.
		"""

		self.clear()
		self._from_dict(data)
		self.extra_data.from_dict(data)

	def set_is_paid(self, is_paid: bool | None):
		"""
		Set condition: is chapter paid.

		Args:
			is_paid (bool | None): Condition: is chapter paid.
		"""

		self._data["is_paid"] = is_paid

	def set_name(self, name: str | None):
		"""
		Set chapter name.

		Args:
			name (str | None): Chapter name.
		"""

		name = zerotify(name)

		if name:
			if self._parser.settings.common.pretty:
				name = self._pretty_name(name)

			self._data["name"] = name

	def set_number(self, number: float | int | str | None):
		"""
		Set chapter number. Number should be in `x.y.z` format.

		Args:
			number (float | int | str | None): Chapter number.
		"""

		self._data["number"] = self._pretty_number(number)

	def set_workers(self, workers: "Sequence[str]"):
		"""
		Задаёт идентификаторы лиц, адаптировавших контент.

		:param workers: Набор идентификаторов.
		:type workers: Sequence[str]
		"""

		for Worker in workers:
			self.add_worker(Worker)

	def set_slug(self, slug: str | None):
		"""
		Задаёт алиас главы.

		:param slug: Алиас главы.
		:type slug: str | None
		"""

		self._data["slug"] = slug

	def set_volume(self, volume: float | int | str | None):
		"""
		Задаёт номер тома, к которому принадлежит глава.

		:param volume: Номер тома.
		:type volume: float | int | str | None
		"""

		self._data["volume"] = self._pretty_number(volume)

	def to_dict(self) -> dict:
		"""Возвращает копию словаря данных главы."""

		self._pre_formatter()

		return insert_dictionary_after_key(self._data.copy(), self.extra_data.to_dict(), "workers")

	@property
	def id(self) -> int:
		"""ID."""

		return self._data["id"]

	@property
	def images(self) -> tuple["ImageData", ...]:
		"""Images."""

		return tuple(self._get_chapter_images())

	@property
	def slug(self) -> str | None:
		"""Slug."""

		return self._data["slug"]

	@property
	def volume(self) -> str | None:
		"""Volume number."""

		return self._data["volume"]

	@property
	def number(self) -> str | None:
		"""Chapter number."""

		return self._data["number"]

	@property
	def name(self) -> str | None:
		"""Name."""

		return self._data["name"]

	@property
	def is_empty(self) -> bool:
		"""Condition: is chapter empty."""

		return self._is_empty()

	@property
	def is_paid(self) -> bool | None:
		"""Condition: is chapter paid."""

		return self._data["is_paid"]

	@property
	def workers(self) -> tuple[str, ...]:
		"""Workers."""

		return tuple(self._data["workers"])

	@property
	def extra_data(self) -> ExtraData:
		"""Extra data."""

		return self._extra_data

	@abstractmethod
	def _clear_content(self):
		"""Clear chapter content."""

		pass

	@abstractmethod
	def _from_dict(self, data: dict):
		"""
		Parse chapter dictionary from descriptive file and fill instance attributes.

		Args:
			data (dict): Chapter data.
		"""

		pass

	@abstractmethod
	def _get_chapter_images(self) -> "Sequence[ImageData]":
		"""
		Get chapter-associated images.

		Returns:
			Sequence[ImageData]: Chapter images.
		"""

		pass

	@abstractmethod
	def _is_empty(self) -> bool:
		"""
		Check is chapter empty.

		Returns:
			bool: Condition: is chapter empty.
		"""

		return False

	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	def _pre_formatter(self):
		"""Execute before chapter data conversion into dictionary."""

		pass

	def _pretty_name(self, name: str) -> str:
		"""
		Pretty chapter name.

		Args:
			name (str): Raw chapter name.

		Returns:
			str: Prettified chapter name.
		"""

		if name.endswith("..."):
			name = name.rstrip(".") + "…"
		else:
			name = name.rstrip(".–")

		name = name.replace("\u00A0", " ")
		name = remove_recurring_substrings(name, " ")

		return name.rstrip(":.")

	def _pretty_number(self, number: float | int | str | None) -> str | None:
		"""
		Convert raw chapter number into valid value.

		Args:
			number (float | int | str | None): Raw chapter number.

		Returns:
			str | None: Converted chapter number in `x.y.z` format.
		"""

		if number is None:
			return

		if isinstance(number, str):
			number = number.strip()
		else:
			number = str(number)

		if "-" in number:
			number = number.split("-")[0]

		number = number.strip("\t .\n")
		number = zerotify(number)

		return number
