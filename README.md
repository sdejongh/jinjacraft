![Python](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)
# JINJACRAFT

JinjaCraft is a simple Python command-line tool which can generate text file based on a Jinja2 template
and a YAML data file.

## Installation
```
git clone https://github.com/sdejongh/jinjacraft.git
cd jinjacraft
pip install -r requirements.txt
pip install .
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
