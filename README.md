![Python](https://img.shields.io/pypi/pyversions/jinjacraft?v=1.5.1)
# JINJACRAFT

JinjaCraft is a simple Python command-line tool which can generate text files based on a Jinja2 template
and a YAML or JSON data file. It can also generate a model data file from a Jinja2 template.

## Requirements

- Python 3.9 or higher
- Supported platforms: Linux, Windows, macOS

## Installation

Using pipx (recommended):
```bash
pipx install jinjacraft
```

Using pip:
```bash
pip install jinjacraft
```

## Usage
```
usage: jinjacraft [-h] [-g TEMPLATE] [-f] [-o OUTPUT_FILE] [--format {yaml,json}]
                  [data_file] [template_file]

Generate text files from Jinja2 templates and YAML/JSON data

positional arguments:
  data_file             Data file path (YAML or JSON)
  template_file         Jinja2 template file path

options:
  -h, --help            show this help message and exit
  -g TEMPLATE, --generate-model TEMPLATE
                        Generate a model data file from a Jinja2 template
  -f, --force           Overwrite existing output file
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Output file path
  --format {yaml,json}  Data file format (default: yaml)
```

## Features

### Data Validation

JinjaCraft validates your data (YAML or JSON) against the template before rendering:

- **Missing variables**: If a variable is used in the template but not defined in the data file, an error is returned and rendering is aborted.
- **Unused variables**: If a variable is defined in the data file but not used in the template, a warning is displayed but rendering continues.

### Model Generation

Generate a model data file from a Jinja2 template to see which variables are expected:

```bash
jinjacraft -g template.jinja2
```

This creates `template.yaml` with placeholders and type comments:

```yaml
title: "<title>"  # string
tasks:  # list
  - name: "<name>"  # string
    completed: "<completed>"  # truthy value (boolean, string, number)
```

Use `--format json` to generate a JSON model instead:

```bash
jinjacraft -g template.jinja2 --format json
```

This creates `template.json`:

```json
{
  "title": "<title>",
  "tasks": [
    {
      "name": "<name>",
      "completed": "<completed>"
    }
  ]
}
```

Use `-o` to specify a custom output file, and `-f` to overwrite an existing file:

```bash
jinjacraft -g template.jinja2 -o model.yaml -f
```

## Examples

### Using YAML data

#### YAML file
```yaml
title: Hello World
tasks:
  - name: First task
    completed: True
  - name: Second task
    completed: False
```

#### Template file
```jinja2
Document: {{ title }}
Tasks:
{% for task in tasks %}- {{ task.name }} ({% if task.completed %}completed{% else %}not completed{% endif %})
{% endfor %}
```

#### Command line
```bash
jinjacraft data.yaml template.jinja2 -o outputfile.txt
```

#### Output
```
Document: Hello World
Tasks:
- First task (completed)
- Second task (not completed)
```

### Using JSON data

#### JSON file
```json
{
  "title": "Hello World",
  "tasks": [
    {"name": "First task", "completed": true},
    {"name": "Second task", "completed": false}
  ]
}
```

#### Command line
```bash
jinjacraft data.json template.jinja2 --format json -o outputfile.txt
```

The output is the same as with YAML data.
