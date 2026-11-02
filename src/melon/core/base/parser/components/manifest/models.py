from typing import Annotated

from packaging.specifiers import SpecifierSet
from pydantic import BaseModel

from dublib.validators.types import Domain, VersionsRange

class ManifestModel(BaseModel):
	"""Manifest model."""

	domain: Annotated[str, Domain]
	parent: str | None = None
	platform: Annotated[SpecifierSet, VersionsRange] | None = None
