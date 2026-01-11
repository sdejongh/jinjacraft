"""Unit tests for JinjaCraft."""

import os
import tempfile
import warnings
import pytest

from jinjacraft.renderer import TemplateRenderer
from jinjacraft.validator import get_template_variables, get_data_keys, validate
from jinjacraft.model_generator import (
    generate_model,
    generate_model_file,
    TemplateAnalyzer,
)
from jinjacraft.exceptions import ValidationError, ModelGenerationError


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


class TestTemplateAnalyzer:
    """Tests for the TemplateAnalyzer class."""

    def test_simple_variable(self):
        """Verify extraction of a simple variable."""
        analyzer = TemplateAnalyzer("Hello {{ name }}!")
        result = analyzer.analyze()
        assert result == {"name": "<name>"}

    def test_multiple_variables(self):
        """Verify extraction of multiple variables."""
        analyzer = TemplateAnalyzer("{{ greeting }}, {{ name }}!")
        result = analyzer.analyze()
        assert result == {"greeting": "<greeting>", "name": "<name>"}

    def test_nested_variable(self):
        """Verify extraction of nested object access."""
        analyzer = TemplateAnalyzer("{{ user.name }}")
        result = analyzer.analyze()
        assert result == {"user": {"name": "<name>"}}

    def test_deeply_nested_variable(self):
        """Verify extraction of deeply nested object access."""
        analyzer = TemplateAnalyzer("{{ user.address.city }}")
        result = analyzer.analyze()
        assert result == {"user": {"address": {"city": "<city>"}}}

    def test_loop_with_item_attributes(self):
        """Verify extraction of list with item attributes from a for loop."""
        template = "{% for item in items %}{{ item.name }}{% endfor %}"
        analyzer = TemplateAnalyzer(template)
        result = analyzer.analyze()
        assert result == {"items": [{"name": "<name>"}]}

    def test_loop_with_multiple_attributes(self):
        """Verify extraction of multiple attributes from loop items."""
        template = "{% for task in tasks %}{{ task.name }} - {{ task.done }}{% endfor %}"
        analyzer = TemplateAnalyzer(template)
        result = analyzer.analyze()
        assert "tasks" in result
        assert isinstance(result["tasks"], list)
        assert "name" in result["tasks"][0]
        assert "done" in result["tasks"][0]

    def test_conditional_variable(self):
        """Verify extraction of variables in conditional statements."""
        template = "{% if show %}{{ message }}{% endif %}"
        analyzer = TemplateAnalyzer(template)
        result = analyzer.analyze()
        assert "show" in result
        assert "message" in result

    def test_conditional_variable_is_marked(self):
        """Verify that variables used in conditions are marked as truthy values."""
        template = "{% if active %}{{ message }}{% endif %}"
        analyzer = TemplateAnalyzer(template)
        result = analyzer.analyze()
        assert result["active"]["__condition__"] is True
        assert result["active"]["value"] == "<active>"
        assert result["message"] == "<message>"

    def test_loop_conditional_is_marked(self):
        """Verify that loop item attributes in conditions are marked as truthy values."""
        template = "{% for task in tasks %}{% if task.done %}{{ task.name }}{% endif %}{% endfor %}"
        analyzer = TemplateAnalyzer(template)
        result = analyzer.analyze()
        assert result["tasks"][0]["done"]["__condition__"] is True
        assert result["tasks"][0]["done"]["value"] == "<done>"
        assert result["tasks"][0]["name"] == "<name>"

    def test_no_variables(self):
        """Verify empty result for template without variables."""
        analyzer = TemplateAnalyzer("Hello world!")
        result = analyzer.analyze()
        assert result == {}

    def test_invalid_template_raises_error(self):
        """Verify that invalid template syntax raises ModelGenerationError."""
        analyzer = TemplateAnalyzer("{% for item in %}")
        with pytest.raises(ModelGenerationError):
            analyzer.analyze()


class TestGenerateModel:
    """Tests for the generate_model function."""

    def test_generates_yaml_with_placeholders(self):
        """Verify that generated YAML contains placeholders."""
        template = "Hello {{ name }}!"
        result = generate_model(template)
        assert "<name>" in result
        assert "# string" in result

    def test_generates_yaml_with_list(self):
        """Verify that generated YAML contains list structure."""
        template = "{% for item in items %}{{ item.value }}{% endfor %}"
        result = generate_model(template)
        assert "items:" in result
        assert "# list" in result

    def test_empty_template_returns_comment(self):
        """Verify that template without variables returns a comment."""
        result = generate_model("Hello world!")
        assert "No variables found" in result


class TestGenerateModelFile:
    """Tests for the generate_model_file function."""

    def test_generates_file_with_default_name(self):
        """Verify that output file uses template name with .yaml extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, "test.jinja2")
            with open(template_path, "w") as f:
                f.write("{{ name }}")

            output_path = generate_model_file(template_path)

            assert output_path == os.path.join(tmpdir, "test.yaml")
            assert os.path.exists(output_path)

    def test_generates_file_with_custom_name(self):
        """Verify that custom output file path is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, "test.jinja2")
            output_path = os.path.join(tmpdir, "custom.yaml")
            with open(template_path, "w") as f:
                f.write("{{ name }}")

            result = generate_model_file(template_path, output_file=output_path)

            assert result == output_path
            assert os.path.exists(output_path)

    def test_error_if_file_exists(self):
        """Verify that error is raised if output file exists without force."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, "test.jinja2")
            output_path = os.path.join(tmpdir, "test.yaml")
            with open(template_path, "w") as f:
                f.write("{{ name }}")
            with open(output_path, "w") as f:
                f.write("existing content")

            with pytest.raises(ModelGenerationError) as exc_info:
                generate_model_file(template_path)
            assert "already exists" in str(exc_info.value)

    def test_force_overwrites_existing_file(self):
        """Verify that force=True overwrites existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, "test.jinja2")
            output_path = os.path.join(tmpdir, "test.yaml")
            with open(template_path, "w") as f:
                f.write("{{ name }}")
            with open(output_path, "w") as f:
                f.write("existing content")

            generate_model_file(template_path, force=True)

            with open(output_path) as f:
                content = f.read()
            assert "<name>" in content

    def test_error_if_template_not_found(self):
        """Verify that error is raised if template file does not exist."""
        with pytest.raises(ModelGenerationError) as exc_info:
            generate_model_file("/nonexistent/template.jinja2")
        assert "not found" in str(exc_info.value)
