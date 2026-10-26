from typing import Annotated, Any

from pydantic.dataclasses import dataclass

from dublib.validators import types

@dataclass(frozen = True)
class WordsDictionaryTemplate:
	"""Template for key content words dictionary."""

	language_code: Annotated[str, types.LanguageCode]
	extra_data: dict[str, Any] | None = None

	chapter: str = "chapter"
	part: str = "part"
	volume: str = "volume"

	afterword: str = "afterword"
	art: str = "art"
	epilogue: str = "epilogue"
	extra: str = "extra"
	glossary: str = "glossary"
	prologue: str = "prologue"

	@property
	def keywords(self) -> tuple[str, ...]:
		"""Dictionary keywords."""

		return (
			self.chapter,
			self.part,
			self.volume,

			self.afterword,
			self.art,
			self.epilogue,
			self.extra,
			self.glossary,
			self.prologue,
		)
