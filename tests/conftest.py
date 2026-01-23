"""
Shared pytest fixtures for collectra_gui tests.
"""

import pytest

from collectra_gui.lineage_display import CollectraGraph


@pytest.fixture
def sample_yaml_data():
    """Minimal valid YAML structure for testing."""
    return {
        "collectra_results_metadata": {"version": "1.0"},
        "image_label": [
            {
                "type": "collectra.Image",
                "id": "img_001",
                "data": "test_image.jpg",
            }
        ],
        "crop_label": [
            {
                "type": "collectra.ImageCrop",
                "id": "crop_001",
                "parents": "img_001",
                "data": "test_image.jpg",
                "x_center": 0.5,
                "y_center": 0.5,
                "width_relative": 0.2,
                "height_relative": 0.1,
            }
        ],
        "text_label": [
            {
                "type": "collectra.Text",
                "id": "text_001",
                "parents": "crop_001",
                "data": "Hello World",
            }
        ],
    }


@pytest.fixture
def complex_yaml_data():
    """Complex YAML with nested crops, containers, and multiple text children."""
    return {
        "collectra_results_metadata": {"version": "1.0"},
        "image_label": [
            {
                "type": "collectra.Image",
                "id": "img_001",
                "data": "test_image.jpg",
            }
        ],
        "container_crop": [
            {
                "type": "collectra.ImageCrop",
                "id": "container_crop_001",
                "parents": "img_001",
                "data": "test_image.jpg",
                "x_center": 0.5,
                "y_center": 0.5,
                "width_relative": 0.8,
                "height_relative": 0.8,
            }
        ],
        "leaf_crop": [
            {
                "type": "collectra.ImageCrop",
                "id": "leaf_crop_001",
                "parents": "container_crop_001",
                "data": "test_image.jpg",
                "x_center": 0.3,
                "y_center": 0.3,
                "width_relative": 0.2,
                "height_relative": 0.1,
            },
            {
                "type": "collectra.ImageCrop",
                "id": "leaf_crop_no_text",
                "parents": "container_crop_001",
                "data": "test_image.jpg",
                "x_center": 0.7,
                "y_center": 0.7,
                "width_relative": 0.2,
                "height_relative": 0.1,
            },
        ],
        "text_label": [
            {
                "type": "collectra.Text",
                "id": "text_001",
                "parents": "leaf_crop_001",
                "data": "First text",
            },
            {
                "type": "collectra.Text",
                "id": "text_002",
                "parents": "text_001",
                "data": "Deepest text",
            },
        ],
    }


@pytest.fixture
def sample_graph(sample_yaml_data):
    """Pre-built AnnotationGraph from sample_yaml_data."""
    return CollectraGraph.from_yaml_data(sample_yaml_data)


@pytest.fixture
def complex_graph(complex_yaml_data):
    """Pre-built AnnotationGraph from complex_yaml_data."""
    return CollectraGraph.from_yaml_data(complex_yaml_data)


@pytest.fixture
def empty_graph():
    """Empty AnnotationGraph."""
    return CollectraGraph()


@pytest.fixture
def temp_yaml_file(tmp_path, sample_yaml_data):
    """Create a temporary YAML file for file I/O tests."""
    import yaml

    yaml_file = tmp_path / "test_results.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(sample_yaml_data, f)
    return yaml_file


@pytest.fixture
def temp_image_file(tmp_path):
    """Create a temporary image file for image tests."""
    # Create a minimal valid PNG (1x1 pixel, red)
    png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
        b"\x00\x05\xfe\xd4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    image_file = tmp_path / "test_image.png"
    image_file.write_bytes(png_data)
    return image_file


@pytest.fixture
def temp_folder_with_files(tmp_path, sample_yaml_data):
    """Create a temp folder containing both a YAML and an image file."""
    import yaml

    # Create YAML file
    yaml_file = tmp_path / "results.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(sample_yaml_data, f)

    # Create minimal PNG
    png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
        b"\x00\x05\xfe\xd4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    image_file = tmp_path / "image.png"
    image_file.write_bytes(png_data)

    return tmp_path
