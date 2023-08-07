import argparse
from jinjacraft.renderer import TemplateRenderer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_file", help="Yaml data file path")
    parser.add_argument("template_file", help="Jinja2 template file path")
    parser.add_argument("output_file", default="", help="Output file path")
    args = parser.parse_args()
    TemplateRenderer.render(data_file=args.data_file, template_file=args.template_file, output_file=args.output_file)


if __name__ == "__main__":
    main()
