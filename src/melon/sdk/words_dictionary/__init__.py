from types import MappingProxyType
from typing import TYPE_CHECKING

from .presets.eng import ENGLISH
from .presets.rus import RUSSIAN

if TYPE_CHECKING:
    from .template import WordsDictionaryTemplate

PRESETS: MappingProxyType[str, "WordsDictionaryTemplate"] = MappingProxyType({
    "eng": ENGLISH,
    "rus": RUSSIAN,
})
