from typing import Any, Optional
import yaml
import jinja2

from jinjacraft.exceptions import (
    DataFileError,
    TemplateFileError,
    TemplateRenderError,
    OutputFileError,
)
from jinjacraft.validator import validate


class TemplateRenderer:
    """Jinja2 template renderer using Yaml data file"""

    @classmethod
    def __load_data(cls, data_file: str) -> Any:
        """Loads data from YAML file

        Args:
            data_file (str):    Yaml data file path

        Returns: Parsed yaml data

        Raises:
            DataFileError: If file not found, permission denied, or YAML parsing fails
        """
        try:
            with open(data_file) as file:
                return yaml.load(file, Loader=yaml.Loader)
        except FileNotFoundError:
            raise DataFileError(f"Data file not found: {data_file}")
        except PermissionError:
            raise DataFileError(f"Permission denied: {data_file}")
        except yaml.YAMLError as err:
            raise DataFileError(f"Invalid YAML in {data_file}: {err}")

    @classmethod
    def __load_template(cls, template_file: str) -> str:
        """Loads Jinja2 template file

        Args:
            template_file (str): Jinja2 template file path

        Returns: Jinja2 template

        Raises:
            TemplateFileError: If file not found or permission denied
        """
        try:
            with open(template_file) as file:
                return file.read()
        except FileNotFoundError:
            raise TemplateFileError(f"Template file not found: {template_file}")
        except PermissionError:
            raise TemplateFileError(f"Permission denied: {template_file}")

    @classmethod
    def __write_output(cls, content: str, output_file: str) -> None:
        """Writes rendered template to file

        Args:
            content (str):  rendered templated
            output_file (str): output file path

        Raises:
            OutputFileError: If permission denied or directory not found
        """
        try:
            with open(output_file, "w") as file:
                file.write(content)
        except PermissionError:
            raise OutputFileError(f"Permission denied: {output_file}")
        except FileNotFoundError:
            raise OutputFileError(f"Directory not found for: {output_file}")

    @classmethod
    def __display(cls, content: str) -> None:
        """Display rendered template to the terminal

        Args:
            content (str):  rendered templated
        """
        print(content)

    @classmethod
    def render(cls, data_file: str, template_file: str, output_file: Optional[str] = None):
        """Render the Jinja2 template using the YAML data file
        If output_file is None, prints the result to the terminal, otherwise write to the output file.

        Args:
            data_file (str):            Yaml data file path
            template_file (str):        Jinja2 template file path
            output_file (Optional[str]): Output file path

        Raises:
            DataFileError: If data file cannot be loaded
            TemplateFileError: If template file cannot be loaded
            ValidationError: If required variables are missing from data
            TemplateRenderError: If template rendering fails
            OutputFileError: If output file cannot be written
        """
        data = cls.__load_data(data_file)
        template = cls.__load_template(template_file)

        # Validate data against template before rendering
        validate(template, data)

        environment = jinja2.Environment()
        try:
            jinja2_template = environment.from_string(template)
            result = jinja2_template.render(data)
            if output_file is None:
                cls.__display(result)
            else:
                cls.__write_output(content=result, output_file=output_file)
        except jinja2.exceptions.TemplateError as err:
            raise TemplateRenderError(f"Template rendering failed: {err}")
