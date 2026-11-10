from typing import Annotated

from pydantic import BaseModel

from dublib.validators.types import Domain

class ManifestModel(BaseModel):
	"""Manifest model."""

	domain: Annotated[str, Domain]
