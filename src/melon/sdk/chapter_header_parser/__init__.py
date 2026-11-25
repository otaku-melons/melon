import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from dublib.functions.data import zerotify

from ...core.base.formats.ranobe.enums import ChapterType
from .structs import HeaderData
from .words_dictionary import PRESETS

if TYPE_CHECKING:
	from .words_dictionary.template import WordsDictionaryTemplate

class ChapterHeaderParser:
	"""Chapter header parser."""

	def __init__(self):
		"""Chapter header parser."""

		self.__keywords: WordsDictionaryTemplate = PRESETS["eng"]

	def load_keywords_presets(self, language_code: str) -> bool:
		"""
		Load keywords preset if exists.

		Args:
			language_code (str): Language code by ISO 639-3.

		Returns:
			bool: `True` if preset loaded.
		"""

		preset: WordsDictionaryTemplate | None = PRESETS.get(language_code)

		if preset:
			self.__keywords = preset

		return bool(preset)

	def set_keywords(self, keywords: "WordsDictionaryTemplate"):
		"""
		Set keywords.

		Args:
			keywords (WordsDictionaryTemplate): Key content words dictionary.
		"""

		self.__keywords = keywords

	def parse(self, header: str) -> HeaderData:
		"""
		Parse chapter header.

		Args:
			header (str): Chapter header.

		Returns:
			HeaderData: Chapter header data.
		"""

		volume: str | None = self.__extract_chapter_volume(header)
		number: str | None = self.__extract_chapter_number(header)
		chapter_type: ChapterType | None = self.__get_chapter_type(header, number)
		name: str | None = self.__extract_chapter_name(header, volume, number, chapter_type)

		return HeaderData(
			volume = volume,
			number = number,
			name = name,
			chapter_type = chapter_type,
		)

	@property
	def keywords(self) -> "WordsDictionaryTemplate":
		"""Key content words dictionary."""

		return self.__keywords

	@property
	def chapter_types_keywords(self) -> MappingProxyType[ChapterType, str]:
		"""Chapter types keywords."""

		return MappingProxyType({
			ChapterType.chapter: self.keywords.chapter,
			ChapterType.prologue: self.keywords.prologue,
			ChapterType.epilogue: self.keywords.epilogue,
			ChapterType.art: self.keywords.art,
			ChapterType.asfterword: self.keywords.afterword,
			ChapterType.glossary: self.keywords.glossary,
			ChapterType.extra: self.keywords.extra,
		})

	def __get_chapter_type(self, header: str, number: str | None) -> ChapterType | None:
		"""
		Get chapter type.

		Args:
			header (str): Chapter header.
			number (str | None): Chapter number.

		Returns:
			ChapterType | None: Chapter type or `None` if unknown.
		"""

		header = header.lower()

		for chapter_type, word in self.chapter_types_keywords.items():
			if header.startswith(word):
				return chapter_type

		if number:
			return ChapterType.chapter

	def __extract_chapter_name(self, header: str, volume: str | None, number: str | None, chapter_type: ChapterType | None) -> str | None:
		"""
		Extract number from chapter header.

		Args:
			header (str): Chapter header.

		Returns:
			str | None: Chapter number or `None` if not found.
		"""

		if volume:
			header = header.split(volume, maxsplit = 1)[-1]

		if number:
			header = header.split(number, maxsplit = 1)[-1]

		header = self.__lstrip_header(header)

		if chapter_type and chapter_type is not ChapterType.chapter:
			keyword: str = self.chapter_types_keywords[chapter_type]
			header = header[len(keyword):]

		return zerotify(self.__lstrip_header(header))

	def __extract_chapter_number(self, header: str) -> str | None:
		"""
		Extract number from chapter header.

		Args:
			header (str): Chapter header.

		Returns:
			str | None: Chapter number or `None` if not found.
		"""

		chapter_number: str | None = self.__extract_number_after_word(header, self.keywords.chapter)

		if chapter_number:
			chapter_number = chapter_number.lstrip("0")

		return chapter_number

	def __extract_chapter_volume(self, header: str) -> str | None:
		"""
		Extract volume number from chapter header.

		Args:
			header (str): Chapter header.

		Returns:
			str | None: Volume number or `None` if not found.
		"""

		return self.__extract_number_after_word(header, self.keywords.volume)

	def __extract_number_after_word(self, string: str, word: str) -> str | None:
		"""
		Extract number after word from string.

		Args:
			string (str): String.
			word (str): Key word.

		Returns:
			str | None: Number in `x.y.z` format or `None` if not found.
		"""

		match: re.Match[str] | None = re.search(f"\\b{word}\\s*([\\d\\.]+)", string, re.IGNORECASE)

		if match:
			return match.group(1).rstrip(".")

	def __lstrip_header(self, header: str) -> str:
		"""
		Strip non-alpha characters from chapter header start.

		Args:
			header (str): Chapter header.

		Returns:
			str: Processed string.
		"""

		header_start: str = ""

		for symbol in header:
			if not symbol.isalpha(): header_start += symbol
			else: break

		header = header[len(header_start):]

		if header_start.count(".") >= 3 or "…" in header_start:
			header = f"…{header}"

		return header
