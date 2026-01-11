![Python](https://img.shields.io/pypi/pyversions/jinjacraft)
# JINJACRAFT

JinjaCraft is a simple Python command-line tool which can generate text file based on a Jinja2 template
and a YAML data file.

## Installation
```
pip install jinjacraft
```

## Usage
```
usage: jinjacraft [-h] [-o OUTPUT_FILE] data_file template_file

positional arguments:
  data_file             Yaml data file path
  template_file         Jinja2 template file path

options:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Output file path
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


