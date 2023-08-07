from jinjacraft.renderer import TemplateRenderer


def test_renderer():
    data_file = "tests/data.yaml"
    template_file = "tests/template.jinja2"
    output_file = "tests/output.txt"
    reference_output_file = "tests/reference_output.txt"
    TemplateRenderer.render(data_file, template_file, output_file)

    with open(output_file) as output:
        result = output.read()

    with open(reference_output_file) as reference:
        awaited_result = reference.read()

    assert result == awaited_result

