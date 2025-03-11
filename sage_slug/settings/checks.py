from typing import Any, List

from django.core.checks import Error, register

from .conf import sageslug_config  # Adjust import based on your project structure


@register()
def check_sageslug_settings(app_configs: Any, **kwargs: Any) -> List[Error]:
    """Validate SageSlug configuration settings in the Django configuration.

    This function checks the settings defined in `SageSlugConfig`, such as the slug type mapping,
    to ensure they are correctly formatted and valid. It returns a list of errors if any issues
    are detected.

    Args:
        app_configs: Configuration passed by Django (not used here).
        **kwargs: Additional keyword arguments for flexibility.

    Returns:
        List[Error]: A list of `Error` objects for any configuration issues found.
    """
    errors: List[Error] = []
    
    # Validate the slug_type_mapping
    errors.extend(
        validate_type_mapping(
            sageslug_config.slug_type_mapping,
            f"{sageslug_config.CONFIG_PREFIX}TYPE_MAPPING",
        )
    )

    return errors


def validate_type_mapping(mapping: dict, config_name: str) -> List[Error]:
    """Validate that the slug type mapping is a dictionary with string keys and values.

    Args:
        mapping: The type mapping dictionary to validate.
        config_name: The name of the setting being validated (for error reporting).

    Returns:
        List[Error]: A list of errors if the mapping is invalid, otherwise an empty list.
    """
    errors: List[Error] = []

    if not isinstance(mapping, dict):
        errors.append(
            Error(
                f"{config_name} must be a dictionary.",
                hint=f"Ensure {config_name} is a dictionary mapping slug field names to types (e.g., {{'post_slug': 'post'}}).",
                id="sageslug.E001",
            )
        )
        return errors

    # Check each key-value pair
    for key, value in mapping.items():
        if not isinstance(key, str):
            errors.append(
                Error(
                    f"Invalid key type in {config_name}: '{key}' is not a string.",
                    hint="All keys must be strings representing slug field names.",
                    id="sageslug.E002",
                )
            )
        if not isinstance(value, str):
            errors.append(
                Error(
                    f"Invalid value type in {config_name}: '{value}' for key '{key}' is not a string.",
                    hint="All values must be strings representing slug types.",
                    id="sageslug.E003",
                )
            )

    return errors