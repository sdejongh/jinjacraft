import argparse
from jinjacraft.renderer import TemplateRenderer


def main():
    """Main routine"""
    # Configure the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("data_file", help="Yaml data file path")
    parser.add_argument("template_file", help="Jinja2 template file path")
    parser.add_argument("-o", "--output_file", help="Output file path", required=False)

    # Parse command line args
    args = parser.parse_args()

    # Render the template using YAML data
    TemplateRenderer.render(data_file=args.data_file, template_file=args.template_file, output_file=args.output_file)


if __name__ == "__main__":
    main()
