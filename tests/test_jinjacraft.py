"""Unit tests for JinjaCraft."""

import warnings
import pytest

from jinjacraft.renderer import TemplateRenderer
from jinjacraft.validator import get_template_variables, get_data_keys, validate
from jinjacraft.exceptions import ValidationError


class TestRenderer:
    """Tests for the TemplateRenderer class."""

    def test_render_to_file(self):
        """Verify that a template is correctly rendered to a file.

        Renders a template with test data and compares the output
        to a reference file to ensure correctness.
        """
        data_file = "tests/data.yaml"
        template_file = "tests/template.jinja2"
        output_file = "tests/output.txt"
        reference_output_file = "tests/reference_output.txt"
        TemplateRenderer.render(data_file, template_file, output_file)

        with open(output_file) as output:
            result = output.read()

        with open(reference_output_file) as reference:
            awaited_result = reference.read()

        assert result == awaited_result


class TestGetTemplateVariables:
    """Tests for the get_template_variables function."""

    def test_simple_variables(self):
        """Verify extraction of simple variables from a template."""
        template = "Hello {{ name }}, you have {{ count }} messages."
        variables = get_template_variables(template)
        assert variables == {"name", "count"}

    def test_no_variables(self):
        """Verify that an empty set is returned when no variables are present."""
        template = "Hello world!"
        variables = get_template_variables(template)
        assert variables == set()

    def test_variables_in_loop(self):
        """Verify extraction of the iterable variable from a for loop."""
        template = "{% for item in items %}{{ item.name }}{% endfor %}"
        variables = get_template_variables(template)
        assert variables == {"items"}

    def test_variables_in_condition(self):
        """Verify extraction of variables used in conditional statements."""
        template = "{% if show %}{{ message }}{% endif %}"
        variables = get_template_variables(template)
        assert variables == {"show", "message"}


class TestGetDataKeys:
    """Tests for the get_data_keys function."""

    def test_dict_keys(self):
        """Verify extraction of keys from a dictionary."""
        data = {"name": "John", "age": 30}
        keys = get_data_keys(data)
        assert keys == {"name", "age"}

    def test_empty_dict(self):
        """Verify that an empty set is returned for an empty dictionary."""
        data = {}
        keys = get_data_keys(data)
        assert keys == set()

    def test_non_dict_data(self):
        """Verify that an empty set is returned for non-dict data types."""
        data = ["item1", "item2"]
        keys = get_data_keys(data)
        assert keys == set()

    def test_none_data(self):
        """Verify that an empty set is returned for None data."""
        keys = get_data_keys(None)
        assert keys == set()


class TestValidate:
    """Tests for the validate function."""

    def test_valid_data(self):
        """Verify that validation passes when all required variables are present."""
        template = "Hello {{ name }}!"
        data = {"name": "World"}
        validate(template, data)

    def test_missing_variable_raises_error(self):
        """Verify that ValidationError is raised when a variable is missing."""
        template = "Hello {{ name }}, {{ greeting }}!"
        data = {"name": "World"}
        with pytest.raises(ValidationError) as exc_info:
            validate(template, data)
        assert "greeting" in str(exc_info.value)

    def test_multiple_missing_variables(self):
        """Verify that all missing variables are reported in the error message."""
        template = "{{ a }} {{ b }} {{ c }}"
        data = {"a": 1}
        with pytest.raises(ValidationError) as exc_info:
            validate(template, data)
        error_message = str(exc_info.value)
        assert "b" in error_message
        assert "c" in error_message

    def test_unused_variable_emits_warning(self):
        """Verify that a warning is emitted for unused variables in data."""
        template = "Hello {{ name }}!"
        data = {"name": "World", "unused": "value"}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate(template, data)
            assert len(w) == 1
            assert "unused" in str(w[0].message)

    def test_multiple_unused_variables_emit_warnings(self):
        """Verify that one warning is emitted per unused variable."""
        template = "Hello {{ name }}!"
        data = {"name": "World", "extra1": "a", "extra2": "b"}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate(template, data)
            assert len(w) == 2

    def test_missing_takes_priority_over_unused(self):
        """Verify that missing variables raise an error even if unused variables exist."""
        template = "{{ required }}"
        data = {"unused": "value"}
        with pytest.raises(ValidationError):
            validate(template, data)
