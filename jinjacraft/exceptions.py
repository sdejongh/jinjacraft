"""Custom exceptions for JinjaCraft"""


class JinjaCraftError(Exception):
    """Base exception for JinjaCraft"""


class DataFileError(JinjaCraftError):
    """Error loading or parsing data file (YAML or JSON)"""


class TemplateFileError(JinjaCraftError):
    """Error loading template file"""


class TemplateRenderError(JinjaCraftError):
    """Error rendering Jinja2 template"""


class OutputFileError(JinjaCraftError):
    """Error writing output file"""


class ValidationError(JinjaCraftError):
    """Error validating data against template"""


class ModelGenerationError(JinjaCraftError):
    """Error generating model YAML from template"""
