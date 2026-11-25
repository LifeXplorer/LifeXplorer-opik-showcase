from PIL import Image

from labels import SPECS, LabelFields, generate_labels, render_label


def test_labels_render_deterministically(tmp_path):
    first = [p.read_bytes() for p in generate_labels(tmp_path / "a")]
    second = [p.read_bytes() for p in generate_labels(tmp_path / "b")]
    assert first == second and len(first) == 6


def test_rotated_label_is_landscape():
    spec = next(s for s in SPECS if s.rotate)
    width, height = render_label(spec).size
    assert width > height


def test_schema_is_strict_for_openai_structured_output():
    schema = LabelFields.model_json_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(LabelFields.model_fields)


def test_generated_pngs_open(tmp_path):
    for path in generate_labels(tmp_path):
        with Image.open(path) as img:
            assert img.format == "PNG"
