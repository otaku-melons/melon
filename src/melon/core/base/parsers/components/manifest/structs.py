from typing import Literal

from pydantic.dataclasses import dataclass

from .enums import ContentTypes, Directives

@dataclass
class ManifestStruct:
	"""Base manifest struct."""

	domain: str
	content_types: ContentTypes | tuple[ContentTypes, ...]
	parent: str | None = None
	version: str | Directives | None = None
	melon_required_version: str | Literal[Directives.from_parent] | None = None

@dataclass(frozen = True)
class StoragedManifestStruct:
	"""Storaged manifest struct."""

	domain: str
	content_types: tuple[ContentTypes, ...]
	parent: str | None = None
	version: str | None = None
	melon_required_version: str | None = None