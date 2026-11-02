from enum import Enum

from .manga.controller import Manga
from .ranobe.controller import Ranobe

__all__ = ["ContentType", "Manga", "Ranobe"]

class ContentType(Enum):
	"""Перечисление типов контента."""

	manga = Manga
	ranobe = Ranobe
