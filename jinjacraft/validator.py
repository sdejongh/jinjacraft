"""Template and data validation for JinjaCraft"""

import warnings
from typing import Any, Set

import jinja2
from jinja2 import meta

from jinjacraft.exceptions import ValidationError


def get_template_variables(template_source: str) -> Set[str]:
    """Extract all variable names used in a Jinja2 template.

    Args:
        template_source: The Jinja2 template source code

    Returns:
        Set of variable names used in the template
    """
    env = jinja2.Environment()
    ast = env.parse(template_source)
    return meta.find_undeclared_variables(ast)


def get_data_keys(data: Any) -> Set[str]:
    """Extract all top-level keys from the data.

    Args:
        data: The parsed YAML data

    Returns:
        Set of top-level keys in the data
    """
    if isinstance(data, dict):
        return set(data.keys())
    return set()


def validate(template_source: str, data: Any) -> None:
    """Validate that the data contains all variables required by the template.

    Raises ValidationError if required variables are missing.
    Emits warnings for unused variables in the data.

    Args:
        template_source: The Jinja2 template source code
        data: The parsed YAML data

    Raises:
        ValidationError: If required variables are missing from the data
    """
    template_vars = get_template_variables(template_source)
    data_keys = get_data_keys(data)

    # Check for missing variables (in template but not in data)
    missing_vars = template_vars - data_keys
    if missing_vars:
        missing_list = ", ".join(sorted(missing_vars))
        raise ValidationError(f"Missing variables in data file: {missing_list}")

    # Check for unused variables (in data but not in template)
    unused_vars = data_keys - template_vars
    for var in sorted(unused_vars):
        warnings.warn(f"Unused variable in data file: {var}", UserWarning)
