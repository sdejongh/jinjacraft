import argparse
import sys
from jinjacraft.renderer import TemplateRenderer
from jinjacraft.model_generator import generate_model_file
from jinjacraft.exceptions import JinjaCraftError


def main():
    """Main routine"""
    # Configure the argument parser
    parser = argparse.ArgumentParser(
        description="Generate text files from Jinja2 templates and YAML data"
    )
    parser.add_argument(
        "-g", "--generate-model",
        metavar="TEMPLATE",
        help="Generate a model YAML file from a Jinja2 template"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing output file"
    )
    parser.add_argument(
        "data_file",
        nargs="?",
        help="YAML data file path"
    )
    parser.add_argument(
        "template_file",
        nargs="?",
        help="Jinja2 template file path"
    )
    parser.add_argument(
        "-o", "--output_file",
        help="Output file path"
    )

    # Parse command line args
    args = parser.parse_args()

    try:
        if args.generate_model:
            # Generate model mode
            output_path = generate_model_file(
                template_file=args.generate_model,
                output_file=args.output_file,
                force=args.force
            )
            print(f"Model generated: {output_path}")
        else:
            # Render mode
            if not args.data_file or not args.template_file:
                parser.error("data_file and template_file are required for rendering")

            TemplateRenderer.render(
                data_file=args.data_file,
                template_file=args.template_file,
                output_file=args.output_file
            )
    except JinjaCraftError as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
