from typing import Any
import yaml
import jinja2


class TemplateRenderer:
    """Jinja2 template renderer using Yaml data file"""

    @classmethod
    def __load_data(cls, data_file: str) -> Any:
        """Loads data from YAML file

        Args:
            data_file (str):    Yaml data file path

        Returns: Parsed yaml data
        """
        try:
            with open(data_file) as file:
                return yaml.load(file, Loader=yaml.Loader)
        except PermissionError as err:
            exit(err)
        except FileNotFoundError as err:
            exit(err)

    @classmethod
    def __load_template(cls, template_file: str) -> str:
        """Loads Jinja2 template file

        Args:
            template_file (str): Jinja2 template file path

        Returns: Jinja2 template
        """
        try:
            with open(template_file) as file:
                return file.read()
        except FileNotFoundError as err:
            exit(err)
        except PermissionError as err:
            exit(err)

    @classmethod
    def __write_output(cls, content: str, output_file: str) -> None:
        """Writes rendered template to file

        Args:
            content (str):  rendered templated
            output_file (str): output file path
        """
        try:
            with open(output_file, "w") as file:
                file.write(content)
        except PermissionError as err:
            exit(err)

    @classmethod
    def __display(cls, content: str) -> None:
        """Display rendered template to the terminal

        Args:
            content (str):  rendered templated
        """
        print(content)

    @classmethod
    def render(cls, data_file: str, template_file: str, output_file: str or None = None):
        """Render the Jinja2 template using the YAML data file
        If output_file is None, prints the result to the terminal, otherwise write to the output file.

        Args:
            data_file (str):            Yaml data file path
            template_file (str):        Jinja2 template file path
            output_file (str or None):  Output file path
        """
        data = cls.__load_data(data_file)
        template = cls.__load_template(template_file)
        environment = jinja2.Environment()
        try:
            jinja2_template = environment.from_string(template)
            result = jinja2_template.render(data)
            if output_file is None:
                cls.__display(result)
            else:
                cls.__write_output(content=result, output_file=output_file)
        except jinja2.exceptions.TemplateError as err:
            exit(err)
