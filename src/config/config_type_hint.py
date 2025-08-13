from __future__ import annotations

from typing import Literal, Optional, TypedDict

from typing_extensions import NotRequired


class SizeVariant(TypedDict):
    """
    Represents size rules for a specific variant of a category.

    :param name: Name of the size variant.
    :param min_size_mb: Minimum size in MB (None if not defined).
    :param max_size_mb: Maximum size in MB (None if not defined).
    """

    name: str
    min_size_mb: Optional[int]
    max_size_mb: Optional[int]


class Category(TypedDict, total=False):
    """
    Represents a file category configuration.

    :param name: Category name (e.g., Images, Videos).
    :param type: Logical type of the category (e.g., document, media).
    :param extensions: List of file extensions for this category.
    :param risk: Optional risk level.
    :param variants: Optional size-based subcategories.
    """

    name: str
    type: str
    extensions: NotRequired[list[str] | set[str]]
    risk: NotRequired[Literal["low", "medium", "high"]]
    variants: NotRequired[list[SizeVariant]]


class Defaults(TypedDict):
    """
    Represents default settings applied when not overridden by category-specific values.

    :param name: Defualt directory name.
    :param risk: Default risk level.
    :param min_size_mb: Default minimum file size in MB.
    :param max_size_mb: Default maximum file size in MB (None means no limit).
    """

    name: str
    risk: Literal["low", "medium", "high"]
    min_size_mb: int
    max_size_mb: Optional[int]


class DefaultPaths(TypedDict):
    """
    Represents default user folder paths for different operating systems.

    :param linux: Default folder paths for Linux systems.
    :param darwin: Default folder paths for macOS systems.
    :param windows: Default folder paths for Windows systems.
    """

    linux: list[str]
    darwin: list[str]
    windows: list[str]


class FileCategories(TypedDict):
    """
    Represents the entire configuration structure for the File Organizer (without default paths).

    :param version: Configuration version number.
    :param defaults: Default settings applied globally.
    :param categories: List of all defined categories.
    """

    version: float
    defaults: Defaults
    categories: list[Category]


class FileAndPathConfig(FileCategories):
    """
    Full configuration including both file categories and OS default paths.

    :param version: Configuration version number.
    :param defaults: Default settings applied globally.
    :param categories: List of all defined categories.
    :param default_paths: Predefined user folder paths for supported operating systems.
    """

    default_paths: DefaultPaths
