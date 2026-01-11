"""Model generator from Jinja2 templates (YAML or JSON output)."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Set

import yaml
import jinja2
from jinja2 import nodes

from jinjacraft.exceptions import ModelGenerationError


def _merge_nested_dict(base: Dict, update: Dict) -> Dict:
    """Recursively merge update into base dictionary.

    Args:
        base: Base dictionary to merge into
        update: Dictionary with values to merge

    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_nested_dict(result[key], value)
        else:
            result[key] = value
    return result


def _build_nested_structure(path: list, is_list: bool = False) -> Dict:
    """Build a nested dictionary structure from a path.

    Args:
        path: List of keys representing the path (e.g., ['user', 'address', 'city'])
        is_list: Whether the root should be a list

    Returns:
        Nested dictionary structure
    """
    if not path:
        return {}

    if len(path) == 1:
        value = f"<{path[0]}>"
        if is_list:
            return {path[0]: []}
        return {path[0]: value}

    key = path[0]
    nested = _build_nested_structure(path[1:], is_list=False)

    if is_list:
        return {key: [nested]}
    return {key: nested}


class TemplateAnalyzer:
    """Analyzes Jinja2 templates to extract variable structures."""

    def __init__(self, template_source: str):
        """Initialize the analyzer with template source.

        Args:
            template_source: The Jinja2 template source code
        """
        self.template_source = template_source
        self.env = jinja2.Environment()
        self.variables: Dict[str, Any] = {}
        self.loop_variables: Set[str] = set()
        self.condition_paths: Set[tuple] = set()  # Track variables used in conditions

    def _mark_condition_variable(self, node: nodes.Node, loop_vars: Set[str]) -> None:
        """Mark variables used in conditions.

        Args:
            node: The condition node to analyze
            loop_vars: Set of loop variable names to exclude
        """
        if isinstance(node, (nodes.Name, nodes.Getattr)):
            path = self._get_attribute_path(node)
            if path and path[0] not in loop_vars:
                self.condition_paths.add(tuple(path))
        # Handle nested conditions (and, or, not)
        for attr in ('node', 'expr', 'left', 'right'):
            child = getattr(node, attr, None)
            if child is not None and isinstance(child, nodes.Node):
                self._mark_condition_variable(child, loop_vars)

    def _get_attribute_path(self, node: nodes.Node) -> list:
        """Extract the full attribute path from a node.

        Args:
            node: AST node to analyze

        Returns:
            List of attribute names forming the path
        """
        if isinstance(node, nodes.Name):
            return [node.name]
        elif isinstance(node, nodes.Getattr):
            parent_path = self._get_attribute_path(node.node)
            return parent_path + [node.attr]
        elif isinstance(node, nodes.Getitem):
            return self._get_attribute_path(node.node)
        return []

    def _analyze_node(self, node: nodes.Node, loop_vars: Set[str] = None) -> None:
        """Recursively analyze an AST node.

        Args:
            node: AST node to analyze
            loop_vars: Set of variable names defined in current loop scope
        """
        if loop_vars is None:
            loop_vars = set()

        if isinstance(node, nodes.For):
            # Track loop variable
            loop_var = node.target.name if isinstance(node.target, nodes.Name) else None
            iter_path = self._get_attribute_path(node.iter)

            if iter_path and iter_path[0] not in loop_vars:
                # This is a top-level iterable
                self.loop_variables.add(iter_path[0])

            # Analyze loop body with loop variable in scope
            new_loop_vars = loop_vars | {loop_var} if loop_var else loop_vars
            for child in node.body:
                self._analyze_for_body(child, iter_path, loop_var, new_loop_vars)

            # Analyze else block if present
            for child in node.else_:
                self._analyze_node(child, loop_vars)

        elif isinstance(node, nodes.Getattr):
            # Handle nested attribute access (e.g., user.address.city)
            path = self._get_attribute_path(node)
            if path and path[0] not in loop_vars:
                structure = _build_nested_structure(path)
                self.variables = _merge_nested_dict(self.variables, structure)
            # Don't continue traversing into child nodes - we've handled the whole path
            return

        elif isinstance(node, nodes.Name):
            if node.name not in loop_vars:
                structure = {node.name: f"<{node.name}>"}
                self.variables = _merge_nested_dict(self.variables, structure)

        elif isinstance(node, nodes.Output):
            for child in node.nodes:
                self._analyze_node(child, loop_vars)

        elif isinstance(node, nodes.If):
            # Mark variables used in conditions
            self._mark_condition_variable(node.test, loop_vars)
            self._analyze_node(node.test, loop_vars)
            for child in node.body:
                self._analyze_node(child, loop_vars)
            for child in node.elif_:
                self._analyze_node(child, loop_vars)
            for child in node.else_:
                self._analyze_node(child, loop_vars)

        elif hasattr(node, 'body'):
            for child in node.body if isinstance(node.body, list) else [node.body]:
                self._analyze_node(child, loop_vars)

        # Handle other node types with children
        for attr in ('node', 'expr', 'test', 'left', 'right', 'args', 'kwargs'):
            child = getattr(node, attr, None)
            if child is not None:
                if isinstance(child, list):
                    for item in child:
                        if isinstance(item, nodes.Node):
                            self._analyze_node(item, loop_vars)
                elif isinstance(child, nodes.Node):
                    self._analyze_node(child, loop_vars)

    def _analyze_for_body(
        self,
        node: nodes.Node,
        iter_path: list,
        loop_var: str,
        loop_vars: Set[str]
    ) -> None:
        """Analyze nodes inside a for loop body.

        Args:
            node: AST node to analyze
            iter_path: Path to the iterable variable
            loop_var: Name of the loop variable
            loop_vars: Set of all loop variables in scope
        """
        if isinstance(node, nodes.Getattr) and hasattr(node, 'node'):
            if isinstance(node.node, nodes.Name) and node.node.name == loop_var:
                # This is accessing an attribute of the loop variable
                # e.g., item.name in {% for item in items %}
                if iter_path:
                    self._add_loop_item_attribute(iter_path[0], node.attr)
                return

        if isinstance(node, nodes.Output):
            for child in node.nodes:
                self._analyze_for_body(child, iter_path, loop_var, loop_vars)
        elif isinstance(node, nodes.For):
            self._analyze_node(node, loop_vars)
        elif isinstance(node, nodes.If):
            # Mark loop item attributes used in conditions
            self._mark_loop_condition_variable(node.test, iter_path, loop_var)
            self._analyze_for_body(node.test, iter_path, loop_var, loop_vars)
            for child in node.body:
                self._analyze_for_body(child, iter_path, loop_var, loop_vars)
            for child in node.else_:
                self._analyze_for_body(child, iter_path, loop_var, loop_vars)
        else:
            self._analyze_node(node, loop_vars)

    def _mark_loop_condition_variable(
        self,
        node: nodes.Node,
        iter_path: list,
        loop_var: str
    ) -> None:
        """Mark loop item attributes used in conditions.

        Args:
            node: The condition node to analyze
            iter_path: Path to the iterable variable
            loop_var: Name of the loop variable
        """
        if isinstance(node, nodes.Getattr) and hasattr(node, 'node'):
            if isinstance(node.node, nodes.Name) and node.node.name == loop_var:
                if iter_path:
                    # Mark this as a condition attribute
                    self.condition_paths.add((iter_path[0], "__item__", node.attr))
        # Handle nested conditions
        for attr in ('node', 'expr', 'left', 'right'):
            child = getattr(node, attr, None)
            if child is not None and isinstance(child, nodes.Node):
                self._mark_loop_condition_variable(child, iter_path, loop_var)

    def _add_loop_item_attribute(self, list_name: str, attr: str) -> None:
        """Add an attribute to a loop item structure.

        Args:
            list_name: Name of the list variable
            attr: Attribute name to add
        """
        if list_name not in self.variables:
            self.variables[list_name] = [{}]
        elif not isinstance(self.variables[list_name], list):
            self.variables[list_name] = [{}]
        elif not self.variables[list_name]:
            self.variables[list_name] = [{}]

        # Check if this attribute is used in a condition
        is_condition = (list_name, "__item__", attr) in self.condition_paths

        # Add attribute to the first (template) item
        if isinstance(self.variables[list_name][0], dict):
            if is_condition:
                self.variables[list_name][0][attr] = {"__condition__": True, "value": f"<{attr}>"}
            else:
                self.variables[list_name][0][attr] = f"<{attr}>"

    def analyze(self) -> Dict[str, Any]:
        """Analyze the template and extract variable structure.

        Returns:
            Dictionary representing the variable structure

        Raises:
            ModelGenerationError: If the template is invalid
        """
        try:
            ast = self.env.parse(self.template_source)
        except jinja2.exceptions.TemplateSyntaxError as err:
            raise ModelGenerationError(f"Invalid template syntax: {err}")

        for node in ast.body:
            self._analyze_node(node)

        # Apply condition markers to simple variables
        self._apply_condition_markers(self.variables, ())

        return self.variables

    def _apply_condition_markers(self, data: Dict, current_path: tuple) -> None:
        """Recursively apply condition markers to variables used in conditions.

        Args:
            data: Dictionary to process
            current_path: Current path in the structure
        """
        for key, value in list(data.items()):
            path = current_path + (key,)
            if path in self.condition_paths and isinstance(value, str):
                data[key] = {"__condition__": True, "value": value}
            elif isinstance(value, dict) and "__condition__" not in value:
                self._apply_condition_markers(value, path)


def _add_type_comments(data: Any, indent: int = 0) -> str:
    """Generate YAML string with type comments.

    Args:
        data: Data structure to convert
        indent: Current indentation level

    Returns:
        YAML string with type comments
    """
    lines = []
    prefix = "  " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            # Check for condition marker
            if isinstance(value, dict) and value.get("__condition__"):
                placeholder = value.get("value", f"<{key}>")
                lines.append(f"{prefix}{key}: \"{placeholder}\"  # truthy value (boolean, string, number)")
            elif isinstance(value, bool):
                lines.append(f"{prefix}{key}: {str(value).lower()}  # boolean")
            elif isinstance(value, str) and value.startswith("<") and value.endswith(">"):
                lines.append(f"{prefix}{key}: \"{value}\"  # string")
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{prefix}{key}: []  # list")
                else:
                    lines.append(f"{prefix}{key}:  # list")
                    for item in value:
                        if isinstance(item, dict):
                            item_lines = _add_type_comments(item, 0).split("\n")
                            first = True
                            for line in item_lines:
                                if line.strip():
                                    if first:
                                        lines.append(f"{prefix}  - {line.strip()}")
                                        first = False
                                    else:
                                        lines.append(f"{prefix}    {line.strip()}")
                        else:
                            lines.append(f"{prefix}  - {item}")
            elif isinstance(value, dict):
                lines.append(f"{prefix}{key}:  # object")
                lines.append(_add_type_comments(value, indent + 1))
            else:
                lines.append(f"{prefix}{key}: {value}")

    return "\n".join(lines)


def _clean_structure_for_json(data: Any) -> Any:
    """Clean the structure for JSON output by removing condition markers.

    Args:
        data: Data structure to clean

    Returns:
        Cleaned data structure suitable for JSON
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, dict) and value.get("__condition__"):
                # Replace condition marker with just the value
                result[key] = value.get("value", f"<{key}>")
            elif isinstance(value, dict):
                result[key] = _clean_structure_for_json(value)
            elif isinstance(value, list):
                result[key] = _clean_structure_for_json(value)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [_clean_structure_for_json(item) for item in data]
    else:
        return data


def generate_model(template_source: str, output_format: str = "yaml") -> str:
    """Generate a model data file from a Jinja2 template.

    Args:
        template_source: The Jinja2 template source code
        output_format: Output format ("yaml" or "json"), defaults to "yaml"

    Returns:
        YAML or JSON string with placeholders

    Raises:
        ModelGenerationError: If the template is invalid
    """
    analyzer = TemplateAnalyzer(template_source)
    structure = analyzer.analyze()

    if not structure:
        if output_format == "json":
            return "{}\n"
        return "# No variables found in template\n"

    if output_format == "json":
        clean_structure = _clean_structure_for_json(structure)
        return json.dumps(clean_structure, indent=2) + "\n"

    return _add_type_comments(structure) + "\n"


def generate_model_file(
    template_file: str,
    output_file: str = None,
    force: bool = False,
    output_format: str = "yaml"
) -> str:
    """Generate a model data file from a Jinja2 template file.

    Args:
        template_file: Path to the Jinja2 template file
        output_file: Path for the output file (default: template_name.yaml or .json)
        force: Overwrite existing file if True
        output_format: Output format ("yaml" or "json"), defaults to "yaml"

    Returns:
        Path to the generated file

    Raises:
        ModelGenerationError: If template is invalid, file exists, or I/O error
    """
    # Determine output file path
    if output_file is None:
        template_path = Path(template_file)
        extension = ".json" if output_format == "json" else ".yaml"
        output_file = str(template_path.with_suffix(extension))

    # Check if output file exists
    if os.path.exists(output_file) and not force:
        raise ModelGenerationError(
            f"Output file already exists: {output_file}. Use --force to overwrite."
        )

    # Read template
    try:
        with open(template_file, encoding="utf-8") as f:
            template_source = f.read()
    except FileNotFoundError:
        raise ModelGenerationError(f"Template file not found: {template_file}")
    except PermissionError:
        raise ModelGenerationError(f"Permission denied: {template_file}")

    # Generate model
    model_content = generate_model(template_source, output_format)

    # Write output
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(model_content)
    except PermissionError:
        raise ModelGenerationError(f"Permission denied: {output_file}")

    return output_file
