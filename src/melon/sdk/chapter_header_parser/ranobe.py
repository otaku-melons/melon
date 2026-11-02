from ...core.base.formats.ranobe.enums import ChapterType
from .manga import MangaChapterHeaderParser

class RanobeChapterHeaderParser(MangaChapterHeaderParser):
	"""Парсер заголовка главы."""

	_Type: ChapterType | None

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def type(self) -> ChapterType | None:
		"""Тип главы."""

		return self._Type

	#==========================================================================================#
	# >>>>> PROTECTED METHODS <<<<< #
	#==========================================================================================#

	def _GetType(self):
		"""Получает тип главы из заголовка."""

		Determinations: dict = {
			ChapterType.prologue: self._WordsDictionary.prologue,
			ChapterType.epilogue: self._WordsDictionary.epilogue,
			ChapterType.art: self._WordsDictionary.art,
			ChapterType.afterword: self._WordsDictionary.afterword,
			ChapterType.glossary: self._WordsDictionary.glossary,
			ChapterType.extra: self._WordsDictionary.extra,
		}

		LowerHeader = self._Header.lower()

		for chapter_type, Word in Determinations.items():
			if LowerHeader.startswith(Word):
				self._Type = chapter_type
				break

		if not self._Type and self._Number: self._Type = ChapterType.chapter

	def _RemovePartTypers(self):
		"""Удаляет ключевые слова типизации."""

		if not self._Header: return
		Keywords = self._WordsDictionary.keywords
		KeywordsToSkip = (self._WordsDictionary.volume, self._WordsDictionary.chapter)
		Keywords = tuple(Value for Value in Keywords if Value not in KeywordsToSkip)
		LowerTitle = self._Header.lower()

		for Keyword in Keywords:
			if LowerTitle.startswith(Keyword):
				self._Header = self._Header[len(Keyword):]
				self._LstripTitle()
				break

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		self._Type: ChapterType | None = None

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЙ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __repr__(self) -> str:
		"""Реинтерпретирует экземпляр в строковое представление."""

		return f"ChapterData(volume={self.volume}, number={self.number}, type={self._Type}, name={self._Header})"

	def parse(self) -> "RanobeChapterHeaderParser":
		"""
		Парсит заголовок главы.

		:return: Парсер заголовка главы.
		:rtype: ChapterTitleParser
		"""

		self._ExtractVolume()
		if self._Volume: self._LeftCutTitle(self._Volume)
		self._LstripTitle()
		self._GetType()
		self._ExtractNumber()
		if self._Number: self._LeftCutTitle(self._Number)
		self._LstripTitle()
		self._RemovePartTypers()

		if self._Parser.settings.common.pretty: self._ExtractPart()

		return self
