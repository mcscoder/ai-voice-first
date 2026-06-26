from __future__ import annotations

from typing import Literal, TypeAlias, cast


MemoryCategoryKey: TypeAlias = Literal[
    "about_me",
    "preferences",
    "work",
    "relationships",
    "goals",
    "custom_notes",
]

MEMORY_CATEGORY_KEYS = (
    "about_me",
    "preferences",
    "work",
    "relationships",
    "goals",
    "custom_notes",
)

DEFAULT_MEMORY_CATEGORY: MemoryCategoryKey = "custom_notes"

_CATEGORY_ALIAS_MAP: dict[str, MemoryCategoryKey] = {
    "about_me": "about_me",
    "personal_info": "about_me",
    "preferences": "preferences",
    "work": "work",
    "relationships": "relationships",
    "goals": "goals",
    "custom_notes": "custom_notes",
    "notes": "custom_notes",
}


def parse_memory_category(value: object) -> MemoryCategoryKey | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized not in MEMORY_CATEGORY_KEYS:
        return None
    return cast(MemoryCategoryKey, normalized)


def normalize_memory_category(item: dict[str, object]) -> MemoryCategoryKey:
    metadata = item.get("metadata")
    metadata_dict = metadata if isinstance(metadata, dict) else {}

    metadata_category = parse_memory_category(metadata_dict.get("category"))
    if metadata_category is not None:
        return metadata_category

    for source in (item.get("categories"), metadata_dict.get("categories")):
        category = _category_from_alias_source(source)
        if category is not None:
            return category

    return DEFAULT_MEMORY_CATEGORY


def _category_from_alias_source(source: object) -> MemoryCategoryKey | None:
    if isinstance(source, str):
        values = [source]
    elif isinstance(source, list):
        values = [value for value in source if isinstance(value, str)]
    else:
        return None

    for value in values:
        normalized = value.strip().lower()
        mapped = _CATEGORY_ALIAS_MAP.get(normalized)
        if mapped is not None:
            return mapped

    if values:
        return DEFAULT_MEMORY_CATEGORY
    return None
