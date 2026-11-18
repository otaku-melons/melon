from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Literal

from dublib.functions.data import to_sequence, zerotify
from dublib.functions.data.dictionary import insert_item
from dublib.validators import types

from ....html.elements import Paragraph
from ...structs.image import ImageData, ImageType
from .branch import Branch
from .enums import Status
from .person import Person
from .structs import ChapterSearchResult, ExtraField

if TYPE_CHECKING:
	from collections.abc import Sequence

	from .chapter import BaseChapter
	from .controller import BaseTitleController

class BaseTitleData[C: "BaseChapter"](ABC):
	"""Base title data."""

	def __init__(self, title_controller: "BaseTitleController[BaseTitleData]", title_format: str):
		"""
		Базовые данные тайтла.

		:param title_controller: Контроллер тайтла.
		:type title_controller: BaseTitleController
		:param title_format: Формат тайтла.
		:type title_format: str
		"""

		self._title_controller = title_controller

		self._data: dict[str, Any] = self._generate_data_struct()
		self._data["format"] = title_format
		self._chapter_type: type[C] = self._export_chapter_type()

		self._description: tuple[Paragraph, ...] = ()
		self._covers: list[ImageData] = []
		self._persons: list[Person] = []
		self._branches: dict[int, Branch] = {}

		self._post_init()

	def add_another_name(self, another_name: str):
		"""
		Add another name.

		Args:
			another_name (str): Another name.
		"""

		another_name = another_name.strip()

		if another_name == self.localized_name or another_name == self.eng_name:
			return

		self._add_root_list_item("another_names", another_name)

	def add_cover(self, cover: ImageData):
		"""
		Add cover.

		Args:
			cover (ImageData): Cover image data.
		"""

		if self.find_cover(cover.link):
			return

		self._covers.append(cover)

	def add_author(self, author: str):
		"""
		Add author.

		Args:
			author (str): Author.
		"""

		self._add_root_list_item("authors", author)

	def add_genre(self, genre: str):
		"""
		Add genre.

		Args:
			genre (str): Genre.
		"""

		self._add_root_list_item("genres", genre)

	def add_tag(self, tag: str):
		"""
		Add tag.

		Args:
			tag (str): Tag.
		"""

		self._add_root_list_item("tags", tag)

	def add_franchise(self, franchise: str):
		"""
		Add franchise.

		Args:
			franchise (str): Franchise.
		"""

		self._add_root_list_item("franchises", franchise)

	def add_person(self, person: Person, unique: bool = True):
		"""
		Add person.

		Args:
			person (Person): Person.
			unique (bool): Condition: is person name must be unique.
		"""

		if unique and self.find_person(person.name):
			return

		self._persons.append(person)

	def add_branch(self, branch: Branch) -> int:
		"""
		Add branch.

		Args:
			branch (Branch): Branch.

		Returns:
			int: Added chapters count.
		"""

		if branch.id in self._branches:
			return self._merge_branch(branch)

		self._branches[branch.id] = branch
		self._branches = {
			element.id: element
			for element in sorted(
				self._branches.values(),
				key = lambda Value: Value.chapters_count, reverse = True,
			)
		}

		return branch.chapters_count

	def clear_covers(self):
		"""Clear covers."""

		self._covers.clear()

	def find_branch(self, branch_id: int) -> Branch | None:
		"""
		Ищет ветвь по её ID.

		:param branch_id: ID dtndb.
		:type branch_id: int
		:return: Результат поиска.
		:rtype: Branch | None
		"""

		return self._branches.get(branch_id)

	def find_cover(self, link: str) -> ImageData | None:
		"""
		Производит поиск обложки по ссылке.

		:param link: Ссылка на обложку.
		:type link: str
		:return: Обложка или `None` при отсутствии оной.
		:rtype: ImageData | None
		"""

		for CurrentCover in self._covers:
			if CurrentCover.link == link:
				return CurrentCover

		return None

	def find_chapter(self, chapter_id: int) -> ChapterSearchResult | None:
		"""
		Ищет главу по её ID.

		:param chapter_id: ID главы.
		:type chapter_id: int
		:return: Результат поиска.
		:rtype: ChapterSearchResult | None
		"""

		BranchResult = None
		ChapterResult = None

		for CurrentBranch in self._branches.values():
			for CurrentChapter in CurrentBranch.chapters:
				if CurrentChapter.id == chapter_id:
					BranchResult = CurrentBranch
					ChapterResult = CurrentChapter
					break

		if BranchResult and ChapterResult:
			return ChapterSearchResult(BranchResult, ChapterResult) if ChapterResult else None

		return None

	def find_person(self, name: str) -> Person | None:
		"""
		Производит поиск персонажа по имени.

		:param name: Имя персонажа.
		:type name: str
		:return: Обложка или `None` при отсутствии оной.
		:rtype: ImageData | None
		"""

		for CurrentPerson in self._persons:
			if CurrentPerson.name == name:
				return CurrentPerson

		return None

	def from_dict(self, data: dict):
		"""
		Parse chapter dictionary from descriptive file and fill instance attributes.

		Args:
			data (dict): Chapter data.
		"""

		self._data = self._data | data

		self._description = self._title_controller.html_interpreter.interpret_lines(self._data["description"], allowed_types = (Paragraph,))
		self._parse_covers()
		self._parse_persons()
		self._parse_content()

	def remove_cover(self, link: str) -> bool:
		"""
		Удаляет обложку.

		:param link: Ссылка на обложку.
		:type link: str
		:return: Возвращает `True`, если обложка найдена и удалена.
		:rtype: bool
		"""

		cover = self.find_cover(link)

		if cover:
			self._covers.remove(cover)
			return True

		return False

	def set_another_names(self, another_names: "Sequence[str]"):
		"""
		Set another names.

		Args:
			another_names (Sequence[str]): Another names.
		"""

		self._clear_root_list("another_names")

		for name in another_names:
			self.add_another_name(name)

	def set_covers(self, covers: "Sequence[ImageData]"):
		"""
		Set covers.

		Args:
			covers (Sequence[ImageData]): Covers.
		"""

		self._clear_root_list("covers")

		for cover in covers:
			self.add_cover(cover)

	def set_authors(self, authors: "Sequence[str]"):
		"""
		Set authors.

		Args:
			authors (Sequence[str]): Authors.
		"""

		self._clear_root_list("authors")

		for author in authors:
			self.add_author(author)

	def set_genres(self, genres: "Sequence[str]"):
		"""
		Set genres.

		Args:
			genres (Sequence[str]): Genres.
		"""

		self._clear_root_list("genres")

		for genre in genres:
			self.add_genre(genre)

	def set_tags(self, tags: "Sequence[str]"):
		"""
		Set tags.

		Args:
			tags (Sequence[str]): Tags.
		"""

		self._clear_root_list("tags")

		for tag in tags:
			self.add_tag(tag)

	def set_franchises(self, franchises: "Sequence[str]"):
		"""
		Set franchises.

		Args:
			franchises (Sequence[str]): Franchises.
		"""

		self._clear_root_list("franchises")

		for franchise in franchises:
			self.add_franchise(franchise)

	def set_persons(self, persons: "Sequence[Person]"):
		"""
		Set persons.

		Args:
			persons (Sequence[Person]): Persons.
		"""

		self._clear_root_list("persons")

		for person in persons:
			self.add_person(person)

	def set_extra_data(self, key: str, data: Any, target_key: str | None = None):
		"""
		Set extra data dictionary after key.

		:param key: Data key.
		:type key: str
		:param data: Extra-data.
		:type data: Any
		:param target_key: After it key extra-data will be placed in dictionary.
		:type target_key: str | None
		:raises KeyError: Key reserved for important fields.
		"""

		if target_key:
			self._data = insert_item(self._data, target_key, (key, data))
		elif key in self._generate_data_struct():
			raise KeyError(key)
		else:
			self._data[key] = data

	def set_branches(self, branches: "Sequence[Branch]"):
		"""
		Set branches.

		Args:
			branches (Sequence[Branch]): Branches.
		"""

		self._branches.clear()

		for branch in branches:
			self.add_branch(branch)

	def set_domain(self, domain: str):
		"""
		Set source domain.

		Args:
			domain (str): Source domain.

		Raises:
			ValidationError: Incorrect domain.
		"""

		self._data["domain"] = types.Domain.parse(domain)

	def set_id(self, title_id: int):
		"""
		Set ID.

		Args:
			title_id (int): Title ID.
		"""

		self._data["id"] = title_id

	def set_content_language(self, language_code: str | None):
		"""
		Set content language ISO 639-3 code.

		Args:
			language_code (str | None): Language ISO 639-3 code.
		"""

		if language_code:
			types.LanguageCode.parse(language_code)

		self._data["content_language"] = language_code

	def set_localized_name(self, localized_name: str | None):
		"""
		Set localized name.

		Args:
			localized_name (str | None): Localized name.
		"""

		if localized_name:
			localized_name = zerotify(localized_name.strip())

		self._data["localized_name"] = localized_name

	def set_eng_name(self, eng_name: str | None):
		"""
		Set english name.

		Args:
			eng_name (str | None): English name.
		"""

		if eng_name:
			eng_name = zerotify(eng_name.strip())

		self._data["eng_name"] = eng_name

	def set_publication_year(self, publication_year: int | None):
		"""
		Set publication year.

		Args:
			publication_year (int | None): Publication year.
		"""

		self._data["publication_year"] = publication_year

	def set_description(self, description: "Paragraph | Sequence[Paragraph] | None"):
		"""
		Set title description.

		Args:
			description (Paragraph | Sequence[Paragraph] | None): Title description elements.
		"""

		if not description:
			self._description = ()

		self._description = to_sequence(description)

	def set_age_limit(self, age_limit: int | None):
		"""
		Set age limit.

		Args:
			age_limit (int | None): Age limit.

		Raises:
			ValueError: Age limit must be 21 or less.
		"""

		if age_limit and age_limit > 21:
			raise ValueError("Age limit must be 21 or less.")

		self._data["age_limit"] = age_limit

	def set_slug(self, slug: str):
		"""
		Set slug.

		Args:
			slug (str): Slug.
		"""

		self._data["slug"] = slug

	def set_status(self, status: Status | None):
		"""
		Set status.

		Args:
			status (Status | None): Title status.
		"""

		self._data["status"] = status.value if status else None

	def set_is_licensed(self, is_licensed: bool | None):
		"""
		Set is licensed status.

		Args:
			is_licensed (bool | None): Condition: is title licensed.
		"""

		self._data["is_licensed"] = is_licensed

	def to_dict(self, sorting: bool) -> dict[str, Any]:
		"""
		Get dictionary representation of data.

		Args:
			sorting (bool): Condition: is chapters sorting bu numeration required.

		Returns:
			dict[str, Any]: Dictionary representation of data.
		"""

		self._build_description()
		self._build_covers()
		self._build_persons()
		self._update_branches_info()
		self._build_content(sorting)

		return self._data.copy()

	@property
	def format(self) -> Literal["melon-manga", "melon-ranobe"]:
		"""JSON format."""

		return self._data["format"]

	@property
	def domain(self) -> str | None:
		"""Source domain."""

		return self._data["domain"]

	@property
	def id(self) -> int | None:
		"""Unique ID."""

		return self._data["id"]

	@property
	def slug(self) -> str:
		"""Slug."""

		return self._data["slug"]

	@property
	def content_language(self) -> str | None:
		"""Content language code by ISO 639-3."""

		return self._data["content_language"]

	@property
	def localized_name(self) -> str | None:
		"""Localized name."""

		return self._data["localized_name"]

	@property
	def eng_name(self) -> str | None:
		"""English name."""

		return self._data["eng_name"]

	@property
	def another_names(self) -> tuple[str, ...]:
		"""Another names."""

		return tuple(self._data["another_names"])

	@property
	def covers(self) -> tuple[ImageData, ...]:
		"""Covers images data."""

		return tuple(self._covers)

	@property
	def authors(self) -> tuple[str, ...]:
		"""Authors."""

		return tuple(self._data["authors"])

	@property
	def publication_year(self) -> int | None:
		"""Publication year."""

		return self._data["publication_year"]

	@property
	def description(self) -> tuple["Paragraph", ...]:
		"""Description paragraphs."""

		return self._description

	@property
	def age_limit(self) -> int | None:
		"""Age limit."""

		return self._data["age_limit"]

	@property
	def genres(self) -> tuple[str, ...]:
		"""Genres."""

		return tuple(self._data["genres"])

	@property
	def tags(self) -> tuple[str, ...]:
		"""Tags."""

		return tuple(self._data["tags"])

	@property
	def franchises(self) -> tuple[str, ...]:
		"""Franchises."""

		return tuple(self._data["franchises"])

	@property
	def perons(self) -> tuple[Person, ...]:
		"""Persons."""

		return tuple(self._persons)

	@property
	def status(self) -> Status | None:
		"""Status."""

		return self._data["status"]

	@property
	def is_licensed(self) -> bool | None:
		"""Cindition: is title licensed on source."""

		return self._data["is_licensed"]

	@property
	def branches(self) -> tuple[Branch, ...]:
		"""Branches."""

		return tuple(self._branches.values())

	def _add_root_list_item(self, key: str, item: str):
		"""
		Add root list item.

		Args:
			key (str): List key.
			item (str): Item.

		Raises:
			TypeError: Required root non-list value.
		"""

		item = item.strip()

		if not item:
			return

		root_list: Any = self._data.get(key)

		if not isinstance(root_list, list):
			raise TypeError("Required root non-list value.")

		if item in root_list:
			return

		root_list.append(item)

	def _build_content(self, branch_id: int | None = None, sorting: bool = True):
		"""
		Обновляет контент во внутреннем словарном хранилище данных тайтла.

		:param branch_id: Если указать ID ветви, будет обновлена только одна ветвь.
		:type branch_id: int | None
		:param sorting: Указывает, нужно ли провести сортировку глав на основе их нумерации.
		:type sorting: bool
		"""

		for branch in self._branches.values():
			if branch_id and branch_id == branch.id or not branch_id:
				if sorting: branch.sort()
				self._data["content"][str(branch.id)] = branch.to_list()
				if branch_id: break

	def _build_covers(self):
		"""Build covers data in inner title dictionary."""

		self._data["covers"] = []

		for cover in self._covers:
			self._data["covers"].append(cover.to_dict(self._title_controller.parser.settings.common.sizing_images))

	def _build_description(self):
		"""Build title description from elements."""

		self._data["description"] = [element.to_html() for element in self._description]

	def _build_persons(self):
		"""Build persons data in inner title dictionary."""

		self._data["persons"] = []

		for person in self._persons:
			self._data["persons"].append(person.to_dict(self._title_controller.parser.settings.common.sizing_images))

	def _clear_root_list(self, key: str):
		"""
		Clear root list elements.

		Args:
			key (str): Description.

		Raises:
			TypeError: Required clearing of non-list value.
		"""

		root_list: Any = self._data.get(key)

		if not isinstance(root_list, list):
			raise TypeError("Required clearing of non-list value.")

		root_list.clear()

	@abstractmethod
	def _export_chapter_type(self) -> type[C]:
		"""
		Экспортирует тип главы.

		:return: Тип главы.
		:rtype: type[BaseChapter]
		"""

		pass

	def _export_extra_fields(self) -> "Sequence[ExtraField]":
		"""
		Экспортирует последовательность дополнительных корневых полей данных.

		:return: Последовательность дополнительных корневых полей данных.
		:rtype: Sequence[ExtraField]
		"""

		return ()

	def _generate_data_struct(self) -> dict[str, Any]:
		"""
		Генерирует базовое словарное представление тайтла.

		:return: Базовое словарное представление тайтла.
		:rtype: dict[str, Any]
		"""

		data: dict[str, Any] = {
			"format": None,
			"domain": None,
			"id": None,
			"slug": None,
			"content_language": None,

			"localized_name": None,
			"eng_name": None,
			"another_names": [],
			"covers": [],

			"authors": [],
			"publication_year": None,
			"description": [],
			"age_limit": None,
			"status": None,
			"is_licensed": None,

			"genres": [],
			"tags": [],
			"franchises": [],
			"persons": [],

			"branches": [],
			"content": {},
		}

		for extra_field in self._export_extra_fields():
			data = insert_item(data, extra_field.after_key, (extra_field.name, extra_field.value))

		return data

	def _merge_branch(self, branch: Branch) -> int:
		"""
		Выполняет слияние переданной ветви с ветвью, имеющей такой же ID.

		:param branch: Ветвь.
		:type branch: Branch
		:return: Количество добавленных глав.
		:rtype: int
		"""

		CurrentBranch = self._branches[branch.id]
		AddedCount = 0

		for NewChapter in branch.chapters:
			if not CurrentBranch.has_chapter(NewChapter.id):
				CurrentBranch.add_chapter(NewChapter)
				AddedCount += 1

		return AddedCount

	def _parse_content(self):
		"""Парсит контент в объектные представления."""

		content: dict[str, list] = self._data["content"]

		for branch_id_string in content.keys():
			branch_data: list[dict] = content[branch_id_string]
			branch_id: int = int(branch_id_string)
			branch_buffer = Branch(branch_id)

			for chapter_data in branch_data:
				chapter_id: int = chapter_data["id"]
				chapter_buffer = self._chapter_type(self._title_controller.parser, chapter_id)
				chapter_buffer.from_dict(chapter_data)
				branch_buffer.add_chapter(chapter_buffer)

			self.add_branch(branch_buffer)

	def _parse_covers(self):
		"""Парсит обложки в объектные представления."""

		self._covers.clear()

		for cover_data in self._data["covers"]:
			cover_data: dict
			buffer = ImageData(cover_data["link"], ImageType.Cover)
			buffer.create_resolution(cover_data.get("width"), cover_data.get("height"))
			self._covers.append(buffer)

	def _parse_persons(self):
		"""Parse persons data from dictionaries."""

		self._persons.clear()

		for person_data in self._data["persons"]:
			person_data: dict
			buffer = Person(person_data["name"])

			another_names: list[str] = person_data.get("another_names") or []
			images: list[dict] = person_data.get("images") or []
			description: list[str] = person_data.get("description") or []

			for another_name in another_names:
				buffer.add_another_name(another_name)

			for image_data in images:
				image_data: dict
				image = ImageData(image_data["link"], ImageType.Person)
				image.create_resolution(image_data.get("width"), image_data.get("height"))
				buffer.add_image(image)

			if description:
				elements: tuple[Paragraph, ...] = self._title_controller.html_interpreter.interpret_lines(description, allowed_types = (Paragraph,))
				buffer.set_description(elements)

			self._persons.append(buffer)

	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	def _remove_cover(self, link: str):
		"""
		Удаляет обложку по ссылке.

		:param link: Ссылка.
		:type link: str
		"""

		result = self.find_cover(link)

		if result:
			self._covers.remove(result)

	def _update_branches_info(self):
		"""Обновляет информацию о ветвях во внутреннем словарном хранилище тайтла."""

		Branches = []

		for CurrentBranch in self._branches.values():
			Branches.append({"id": CurrentBranch.id, "chapters_count": CurrentBranch.chapters_count})

		self._data["branches"] = sorted(Branches, key = lambda Value: Value["chapters_count"], reverse = True)
