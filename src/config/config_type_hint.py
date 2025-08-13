from typing import TypedDict


# Define the structure for a file rule (e.g., Images-Small)
class FileRule(TypedDict, total=False):
    extensions: set[str]  # Use set for faster membership testing
    size_gt_mb: float
    date_gt: str


# Define the structure for all file categories
FileCategoriesConfig = dict[str, FileRule]
AllowedPathsConfig = dict[str, list[str]]


# Define the main config structure when both are loaded
class CombinedConfig(TypedDict):
    file_categories: FileCategoriesConfig
    allowed_paths: AllowedPathsConfig
