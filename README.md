![Python](https://img.shields.io/pypi/pyversions/jinjacraft?v=1.4.1)
# JINJACRAFT

JinjaCraft is a simple Python command-line tool which can generate text file based on a Jinja2 template
and a YAML data file and  event generate a base data file in Yaml format from a Jinja2 template.

## Requirements

Python 3.9 or higher

## Installation

Using pip:
```bash
pip install jinjacraft
```

Using pipx (recommended for CLI tools):
```bash
pipx install jinjacraft
```

## Usage
```
usage: jinjacraft [-h] [-g TEMPLATE] [-f] [-o OUTPUT_FILE] [data_file] [template_file]

Generate text files from Jinja2 templates and YAML data

positional arguments:
  data_file             YAML data file path
  template_file         Jinja2 template file path

options:
  -h, --help            show this help message and exit
  -g TEMPLATE, --generate-model TEMPLATE
                        Generate a model YAML file from a Jinja2 template
  -f, --force           Overwrite existing output file
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Output file path
```

## Features

### Data Validation

JinjaCraft validates your YAML data against the template before rendering:

- **Missing variables**: If a variable is used in the template but not defined in the YAML file, an error is returned and rendering is aborted.
- **Unused variables**: If a variable is defined in the YAML file but not used in the template, a warning is displayed but rendering continues.

### Model Generation

Generate a model YAML file from a Jinja2 template to see which variables are expected:

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

Use `-o` to specify a custom output file, and `-f` to overwrite an existing file:

```bash
jinjacraft -g template.jinja2 -o model.yaml -f
```

## Example

### YAML file
```yaml
title: Hello World
tasks:
  - name: First task
    completed: True
  - name: Second task
    completed: False

```

### Template file
```jinja2
Document: {{ title }}
Tasks:
{% for task in tasks %}- {{ task.name }} ({% if task.completed %}completed{% else %}not completed{% endif %})
{%  endfor %}
```

### Command line
```bash
jinjacraft data.yaml template.jinja2 -o outputfile.txt
```

### Output file content
```
Document: Hello World
Tasks:
- First task (completed)
- Second task (not completed)
```
