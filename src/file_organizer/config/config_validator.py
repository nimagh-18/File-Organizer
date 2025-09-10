"""
File Categories Configuration Validator.

=======================================

A module for validating the structure of file categories YAML configuration files.

.. module:: file_categories_validation
   :synopsis: Validate file organization categories configuration.

.. moduleauthor:: Your Name <your.email@example.com>
"""

from pathlib import Path

import typer
import yaml

from file_organizer.config.config_type_hint import Category, FileCategories, SizeVariant
from file_organizer.config.file_allowed_logs_config_path import file_categories_path
from file_organizer.config.read_config import read_config


def validate_file_categories(
    config_path: Path = file_categories_path,
) -> bool:
    """
    Main validation function that orchestrates the validation process.

    :param config_path: Path to the YAML config file
    :type config_path: Path
    :return: True if configuration is valid, False otherwise
    :rtype: bool
    :raises: Does not raise but returns False on validation failure

    Example:
        >>> from pathlib import Path
        >>> is_valid = validate_file_categories(Path("config.yaml"))
        >>> if not is_valid:
        ...     print("Configuration is invalid")
    """
    try:
        config = read_config(config_path, optimization=False)
        errors: list[str] = []

        errors.extend(_validate_top_level(config))

        if "categories" in config:
            errors.extend(_validate_categories(config["categories"]))

        return _display_validation_result(errors)

    except FileNotFoundError:
        return _display_validation_result([f"Config file not found: {config_path}"])
    except yaml.YAMLError as e:
        return _display_validation_result([f"Invalid YAML: {str(e)}"])
    except Exception as e:
        return _display_validation_result([f"Unexpected error: {str(e)}"])


def _validate_top_level(config: FileCategories) -> list[str]:
    """
    Validate the top-level structure of the configuration.

    :param config: Loaded configuration dictionary
    :type config: Dict
    :return: List of error messages (empty if valid)
    :rtype: List[str]

    Checks:
        - Config is a dictionary
        - Contains required 'categories' key

    Example:
        >>> errors = _validate_top_level({"categories": []})
        >>> len(errors)
        0

    """
    errors: list[str] = []
    if not isinstance(config, dict):
        errors.append("Config must be a dictionary")
        return errors

    if "categories" not in config:
        errors.append("Missing required 'categories' key")

    return errors


def _validate_categories(categories: list[Category]) -> list[str]:
    """
    Validate the categories list and individual categories.

    :param categories: List of category dictionaries
    :type categories: List[Dict]
    :return: List of error messages
    :rtype: List[str]

    Checks:
        - categories is a list
        - Each category is valid (delegates to _validate_single_category)

    Example:
        >>> categories = [{"name": "Images", "extensions": [".jpg"]}]
        >>> errors = _validate_categories(categories)
        >>> len(errors)
        0

    """
    errors: list[str] = []

    if not isinstance(categories, list):
        errors.append("'categories' must be a list")
        return errors

    for idx, category in enumerate(categories, 1):
        errors.extend(_validate_single_category(category, idx))

    return errors


def _validate_single_category(category: Category, category_num: int) -> list[str]:
    """
    Validate a single category dictionary.

    :param category: Category dictionary to validate
    :type category: Dict
    :param category_num: Position of category in list (for error messages)
    :type category_num: int
    :return: List of error messages
    :rtype: List[str]

    Checks:
        - Required keys present (name, extensions, type)
        - Name is non-empty string
        - Extensions is list of strings
        - Extensions should be starts with '.'
        - Validates variants if present

    Example:
        >>> category = {"name": "Docs", "extensions": [".pdf"], "type": "document"}
        >>> errors = _validate_single_category(category, 1)
        >>> len(errors)
        0

    """
    errors: list[str] = []
    required_keys = {"name", "extensions", "type"}

    # Check required keys
    for key in required_keys:
        if key not in category:
            errors.append(f"Category #{category_num} missing '{key}'")

    # Validate name
    if "name" in category and not isinstance(category["name"], str):
        errors.append(f"Category #{category_num} name must be a string")
    elif "name" in category and not category["name"].strip():
        errors.append(f"Category #{category_num} name cannot be empty")

    category_name = category["name"]

    # Validate extensions
    if "extensions" in category:
        if not isinstance(category["extensions"], list):
            errors.append(f"Category {category_name} extensions must be a list")
        else:
            first_non_string = True
            first_not_starts_with = True

            for ext in category["extensions"]:
                if not isinstance(ext, str) and first_non_string:
                    errors.append(
                        f"Category {category_name} contains non-string extension: {ext}"
                    )
                    first_non_string = False
                    continue

                if not ext.startswith(".") and first_not_starts_with:
                    errors.append(
                        f"Category {category_name} extensions should be starts with '.': {ext}"
                    )
                    first_not_starts_with = False

    # Validate variants if present
    if "variants" in category:
        errors.extend(_validate_variants(category["variants"], category))

    return errors


def _validate_variants(variants: list[SizeVariant], category: Category) -> list[str]:
    """
    Validate variants within a category.

    :param variants: List of variant dictionaries
    :type variants: List[Dict]
    :param category_num: Parent category number (for error messages)
    :type category_num: int
    :return: List of error messages
    :rtype: List[str]

    Checks:
        - Variants is a list
        - Each variant has required 'name' field
        - Size constraints are numbers if present

    Example:
        >>> variants = [{"name": "Small", "max_size_mb": 1}]
        >>> errors = _validate_variants(variants, 1)
        >>> len(errors)
        0

    """
    errors: list[str] = []

    category_name = category["name"]

    if not isinstance(variants, list):
        errors.append(f"Category {category_name} variants must be a list")
        return errors

    for var_num, variant in enumerate(variants, 1):
        if not isinstance(variant, dict):
            errors.append(
                f"Category {category_name} variant #{var_num} must be a dictionary"
            )
            continue

        if "name" not in variant:
            errors.append(f"Category {category_name} variant #{var_num} missing 'name'")

        # Validate size constraints
        for size_key in ["min_size_mb", "max_size_mb"]:
            if size_key in variant and not isinstance(variant[size_key], (int, float)):
                errors.append(
                    f"Category {category_name} variant #{var_num} "
                    f"has invalid {size_key} value"
                )

    return errors


def _display_validation_result(errors: list[str]) -> bool:
    """
    Display validation results and return overall status.

    :param errors: List of error messages
    :type errors: List[str]
    :return: True if no errors, False otherwise
    :rtype: bool

    Displays:
        - Green success message if no errors
        - Red error list if validation failed

    Example:
        >>> _display_validation_result([])
        True
        >>> _display_validation_result(["Error 1"])
        False

    """
    if not errors:
        typer.echo(typer.style("✓ Configuration is valid!", fg=typer.colors.GREEN))
        return True

    typer.echo(typer.style("✗ Validation errors found:", fg=typer.colors.RED))
    for error in errors:
        typer.echo(f"  - {error}")

    return False
