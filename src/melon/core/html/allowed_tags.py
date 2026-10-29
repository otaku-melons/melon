from dataclasses import dataclass

from .enums import TagCategory

__all__ = ["ALLOWED_TAGS"]

@dataclass(frozen = True)
class TagData:
	"""Tag data."""

	name: str
	categories: tuple[TagCategory, ...] = ()
	attributes: tuple[str, ...] = ()
	styles: tuple[str, ...] = ()
	is_support_data: bool = False

class AllowedTags:
	"""Allowed tags."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def names(self) -> tuple[str, ...]:
		"""Allowed tags names."""

		return self.__allowed_tags_names

	#==========================================================================================#
	# >>>>> PRIVATE METHODS <<<<< #
	#==========================================================================================#

	def __build_categories(self) -> dict[TagCategory, tuple[TagData, ...]]:
		"""
		Build tags categories.

		Returns:
			dict[TagCategory, tuple[TagData, ...]]: Tags categories dictionary.
		"""

		categories: dict[TagCategory, list[TagData]] = {category: [] for category in TagCategory}

		for tag in self.__data.values():

			for category in tag.categories:
				categories[category].append(tag)

		return {category: tuple(tags) for category, tags in categories.items()}

	def __build_data(self) -> dict[str, TagData]:
		"""
		Build tags data.

		Returns:
			dict[str, TagData]: Tags data.
		"""

		data: list[TagData] = []

		paragraph = TagData("p", styles = ("text-align",))
		data.append(paragraph)

		blockquote = TagData("blockquote", is_support_data = True)
		data.append(blockquote)

		for level in (3, 4, 5, 6):
			header = TagData(f"h{level}")
			data.append(header)

		for name in ("b", "strong", "i", "em", "s", "del", "u", "ins", "sup", "sub"):
			styling_tag = TagData(name, categories = (TagCategory.Styling,))
			data.append(styling_tag)

		anchor = TagData("a", attributes = ("href",))
		data.append(anchor)

		image = TagData("img", attributes = ("src", "width", "height"))
		data.append(image)

		return {tag.name: tag for tag in data}

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self):
		"""Allowed tags."""

		self.__data: dict[str, TagData] = self.__build_data()

		self.__categories: dict[TagCategory, tuple[TagData, ...]] = self.__build_categories()
		self.__allowed_tags_names: tuple[str, ...] = tuple(tag.name for tag in self.__data.values())

	def get_category_tags(self, category: TagCategory) -> tuple[TagData, ...]:
		"""
		Get category tags.

		Args:
			category (TagCategory): Tags category.

		Returns:
			tuple[TagData, ...]: Category tags.
		"""

		return self.__categories[category]

	def get_category_tags_names(self, category: TagCategory) -> tuple[str, ...]:
		"""
		Get category tags names.

		Args:
			category (TagCategory): Tags category.

		Returns:
			tuple[TagData, ...]: Category tags names.
		"""

		return tuple(tag.name for tag in self.get_category_tags(category))

	def get_tag(self, name: str) -> TagData | None:
		"""
		Get tag data.

		Args:
			name (str): Tag name.

		Returns:
			TagData | None: Tag data or `None` if tag not allowed.
		"""

		return self.__data.get(name)

ALLOWED_TAGS = AllowedTags()
