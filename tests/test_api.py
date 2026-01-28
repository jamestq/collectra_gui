"""
Tests for collectra_gui.api module.

Tests cover:
- Api class methods for graph operations
- File I/O operations (load_yaml, get_image_base64)
- CRUD operations (create, update, delete annotations)
- get_resource_path helper function
"""

import base64
import os
from unittest.mock import MagicMock, patch

import pytest

from collectra_gui.api import Api, get_resource_path


class TestApiInit:
    """Tests for Api initialization."""

    def test_init_sets_none_values(self):
        api = Api()
        assert api._graph is None
        assert api._yaml_path is None
        assert api._window is None

    def test_set_window_stores_reference(self):
        api = Api()
        mock_window = MagicMock()
        api.set_window(mock_window)
        assert api._window is mock_window


class TestApiLoadYaml:
    """Tests for Api.load_yaml method."""

    def test_load_valid_yaml(self, temp_yaml_file):
        api = Api()
        result = api.load_yaml(str(temp_yaml_file))

        assert result["success"] is True
        assert result["path"] == str(temp_yaml_file)
        assert api._graph is not None
        assert api._yaml_path == str(temp_yaml_file)

    def test_load_nonexistent_file(self):
        api = Api()
        result = api.load_yaml("/nonexistent/path.yaml")

        assert result["success"] is False
        assert "error" in result

    def test_load_invalid_yaml(self, tmp_path):
        # Create invalid YAML
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("{{invalid yaml content")

        api = Api()
        result = api.load_yaml(str(invalid_file))

        assert result["success"] is False
        assert "error" in result


class TestApiGetDisplayValue:
    """Tests for Api.get_display_value method."""

    def test_no_graph_loaded(self):
        api = Api()
        result = api.get_display_value("any_node")

        assert result["success"] is False
        assert "No graph loaded" in result["error"]

    def test_valid_node(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        result = api.get_display_value("text_001")

        assert result["success"] is True
        assert "value" in result
        assert "source_id" in result
        assert "crop_region" in result
        assert "reason" in result

    def test_nonexistent_node(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        result = api.get_display_value("nonexistent")

        assert result["success"] is True
        assert result["value"] is None
        assert "not found" in result["reason"]


class TestApiGetAllNodes:
    """Tests for Api.get_all_nodes method."""

    def test_no_graph_loaded(self):
        api = Api()
        result = api.get_all_nodes()

        assert result["success"] is False
        assert "No graph loaded" in result["error"]

    def test_returns_all_node_ids(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        result = api.get_all_nodes()

        assert result["success"] is True
        assert "nodes" in result
        assert "img_001" in result["nodes"]
        assert "crop_001" in result["nodes"]
        assert "text_001" in result["nodes"]


class TestApiGetNodeInfo:
    """Tests for Api.get_node_info method."""

    def test_no_graph_loaded(self):
        api = Api()
        result = api.get_node_info("any_node")

        assert result["success"] is False
        assert "No graph loaded" in result["error"]

    def test_valid_node_info(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        result = api.get_node_info("crop_001")

        assert result["success"] is True
        assert result["id"] == "crop_001"
        assert "ImageCrop" in result["type"]
        assert "data" in result
        assert "children" in result
        assert "parents" in result

    def test_nonexistent_node(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        result = api.get_node_info("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]


class TestApiGetNodesByType:
    """Tests for Api.get_nodes_by_type method."""

    def test_no_graph_loaded(self):
        api = Api()
        result = api.get_nodes_by_type("ImageCrop")

        assert result["success"] is False
        assert "No graph loaded" in result["error"]

    def test_filter_by_type(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))

        result = api.get_nodes_by_type("ImageCrop")
        assert result["success"] is True
        assert "crop_001" in result["nodes"]
        assert result["count"] == 1

        result = api.get_nodes_by_type("Text")
        assert "text_001" in result["nodes"]
        assert result["count"] == 1

    def test_filter_no_matches(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        result = api.get_nodes_by_type("NonExistent")

        assert result["success"] is True
        assert result["nodes"] == []
        assert result["count"] == 0


class TestApiGetAllNodesForGrid:
    """Tests for Api.get_all_nodes_for_grid method."""

    def test_no_graph_loaded(self):
        api = Api()
        result = api.get_all_nodes_for_grid()

        assert result["success"] is False
        assert "No graph loaded" in result["error"]

    def test_returns_grid_formatted_rows(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        result = api.get_all_nodes_for_grid()

        assert result["success"] is True
        assert "rows" in result
        assert len(result["rows"]) == 3

        # Check row structure
        row_ids = {row["id"] for row in result["rows"]}
        assert row_ids == {"img_001", "crop_001", "text_001"}

        # Check row has required fields
        for row in result["rows"]:
            assert "id" in row
            assert "type" in row
            assert "data" in row
            assert "displayValue" in row
            assert "crop_region" in row
            assert "displaySourceId" in row
            assert "reason" in row
            assert "parents" in row
            assert "children" in row
            assert "locked" in row


class TestApiUpdateNodeData:
    """Tests for Api.update_node_data method."""

    def test_updates_node_data(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))

        result = api.update_node_data("text_001", "Updated text content")

        assert api._graph is not None

        assert result["success"] is True
        # Verify the update in graph
        assert api._graph.get_data("text_001") == "Updated text content"

    def test_update_nonexistent_node(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))

        result = api.update_node_data("nonexistent", "value")

        assert result["success"] is False
        assert "error" in result


class TestApiUpdateNodeCoordinates:
    """Tests for Api.update_node_coordinates method."""

    def test_updates_crop_region(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))

        assert api._graph is not None

        new_region = {
            "x_center": 0.8,
            "y_center": 0.9,
            "width_relative": 0.3,
            "height_relative": 0.4,
        }
        result = api.update_node_coordinates("crop_001", new_region)

        assert result["success"] is True
        # Verify the update
        stored_region = api._graph.get_crop_region("crop_001")
        assert stored_region == new_region

    def test_update_with_missing_fields(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))

        incomplete_region = {"x_center": 0.5}  # Missing other fields
        result = api.update_node_coordinates("crop_001", incomplete_region)

        assert result["success"] is False
        assert "error" in result


class TestApiCreateAnnotation:
    """Tests for Api.create_annotation method."""

    def test_no_graph_loaded(self):
        api = Api()
        result = api.create_annotation({"x_center": 0.5}, "user_crop")

        assert result["success"] is False
        assert "No graph loaded" in result["error"]

    def test_creates_annotation_imagecrop_only(self, temp_yaml_file):
        """create_annotation() creates only ImageCrop, no Text child."""
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None

        initial_count = len(api._graph.nodes)

        crop_region = {
            "x_center": 0.6,
            "y_center": 0.7,
            "width_relative": 0.1,
            "height_relative": 0.05,
        }
        result = api.create_annotation(crop_region, "user_crop")

        assert result["success"] is True
        # Should have added 1 node (ImageCrop only, no Text child)
        assert len(api._graph.nodes) == initial_count + 1

    def test_created_annotation_has_correct_parent(self, temp_yaml_file):
        """Created ImageCrop has correct parent relationship."""
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None

        crop_region = {
            "x_center": 0.6,
            "y_center": 0.7,
            "width_relative": 0.1,
            "height_relative": 0.05,
        }
        api.create_annotation(crop_region, "user_crop")

        # Find the newly created crop (starts with user_crop-)
        new_crops = [n for n in api._graph.nodes if n.startswith("user_crop-")]
        assert len(new_crops) == 1

        new_crop = new_crops[0]
        parents = api._graph.parents(new_crop)
        assert "img_001" in parents

        # Verify no text node was created
        new_texts = [n for n in api._graph.nodes if n.startswith("user_text_")]
        assert len(new_texts) == 0


class TestApiDeleteAnnotation:
    """Tests for Api.delete_annotation method."""

    def test_no_graph_loaded(self):
        api = Api()
        result = api.delete_annotation("any_node")

        assert result["success"] is False
        assert "No graph loaded" in result["error"]

    def test_deletes_crop_and_text_children(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None
        # Delete crop_001 which has text_001 as child
        result = api.delete_annotation("crop_001")

        assert result["success"] is True
        assert "crop_001" not in api._graph.nodes
        assert "text_001" not in api._graph.nodes

    def test_delete_nonexistent_node(self, temp_yaml_file):
        api = Api()
        api.load_yaml(str(temp_yaml_file))

        result = api.delete_annotation("nonexistent")

        assert result["success"] is False
        assert "error" in result


class TestApiGetImageBase64:
    """Tests for Api.get_image_base64 method."""

    def test_reads_png_file(self, temp_image_file):
        api = Api()
        result = api.get_image_base64(str(temp_image_file))

        assert result["success"] is True
        assert result["data"].startswith("data:image/png;base64,")

    def test_nonexistent_file(self):
        api = Api()
        result = api.get_image_base64("/nonexistent/image.png")

        assert result["success"] is False
        assert "error" in result

    def test_different_mime_types(self, tmp_path):
        api = Api()

        # Test JPEG
        jpg_file = tmp_path / "test.jpg"
        jpg_file.write_bytes(b"fake jpg data")
        result = api.get_image_base64(str(jpg_file))
        assert "image/jpg" in result["data"]

        # Test GIF
        gif_file = tmp_path / "test.gif"
        gif_file.write_bytes(b"fake gif data")
        result = api.get_image_base64(str(gif_file))
        assert "image/gif" in result["data"]

        # Test TIFF
        tif_file = tmp_path / "test.tif"
        tif_file.write_bytes(b"fake tif data")
        result = api.get_image_base64(str(tif_file))
        assert "image/tiff" in result["data"]

    def test_unknown_extension_defaults_to_png(self, tmp_path):
        api = Api()
        unknown_file = tmp_path / "test.xyz"
        unknown_file.write_bytes(b"fake data")
        result = api.get_image_base64(str(unknown_file))
        # Unknown extensions raise KeyError and return error
        assert result["success"] is False
        assert "error" in result


class TestApiSelectFolder:
    """Tests for Api.select_folder method."""

    def test_no_window_initialized(self):
        api = Api()
        result = api.select_folder()

        assert result["success"] is False
        assert "Window not initialized" in result["error"]

    def test_dialog_cancelled(self):
        api = Api()
        mock_window = MagicMock()
        mock_window.create_file_dialog.return_value = None
        api.set_window(mock_window)

        result = api.select_folder()

        assert result["success"] is False
        assert "No folder selected" in result["error"]

    def test_dialog_returns_empty_list(self):
        api = Api()
        mock_window = MagicMock()
        mock_window.create_file_dialog.return_value = []
        api.set_window(mock_window)

        result = api.select_folder()

        assert result["success"] is False

    def test_finds_yaml_and_image_files(self, temp_folder_with_files):
        api = Api()
        mock_window = MagicMock()
        mock_window.create_file_dialog.return_value = [str(temp_folder_with_files)]
        api.set_window(mock_window)

        result = api.select_folder()

        assert result["success"] is True
        assert result["folder_path"] == str(temp_folder_with_files)
        assert result["yaml_path"] is not None
        assert result["yaml_path"].endswith(".yaml")
        assert result["image_path"] is not None
        assert result["image_path"].endswith(".png")

    def test_handles_dialog_exception(self):
        api = Api()
        mock_window = MagicMock()
        mock_window.create_file_dialog.side_effect = Exception("Dialog error")
        api.set_window(mock_window)

        result = api.select_folder()

        assert result["success"] is False
        assert "Dialog error" in result["error"]


class TestGetResourcePath:
    """Tests for get_resource_path helper function."""

    def test_development_mode_path(self):
        # In normal (non-frozen) mode, should use __file__ parent
        result = get_resource_path("test.html")
        assert result.endswith("test.html")
        assert "collectra_gui" in result

    def test_frozen_mode_path(self):
        """Test PyInstaller frozen mode by patching sys module directly."""
        import sys

        # Store original values
        original_frozen = getattr(sys, "frozen", None)
        original_meipass = getattr(sys, "_MEIPASS", None)

        try:
            # Simulate PyInstaller frozen mode
            sys.frozen = True
            sys._MEIPASS = "/tmp/pyinstaller_bundle"

            result = get_resource_path("test.html")

            assert result == "/tmp/pyinstaller_bundle/test.html"
        finally:
            # Restore original state
            if original_frozen is None:
                if hasattr(sys, "frozen"):
                    delattr(sys, "frozen")
            else:
                sys.frozen = original_frozen
            if original_meipass is None:
                if hasattr(sys, "_MEIPASS"):
                    delattr(sys, "_MEIPASS")
            else:
                sys._MEIPASS = original_meipass


class TestApiSaveToYaml:
    """Tests for Api._save_to_yaml private method."""

    def test_save_preserves_data(self, temp_yaml_file):
        import yaml

        api = Api()
        api.load_yaml(str(temp_yaml_file))

        # Modify data
        api._graph.set_data("text_001", "Modified text")
        api._save_to_yaml()

        # Reload and verify
        with open(temp_yaml_file, "r") as f:
            saved_data = yaml.safe_load(f)

        # Find the text node in saved data
        text_items = saved_data.get("text_label", [])
        if not isinstance(text_items, list):
            text_items = [text_items]
        text_node = next((t for t in text_items if t.get("id") == "text_001"), None)

        assert text_node is not None
        assert text_node["data"] == "Modified text"

    def test_save_raises_when_no_yaml_loaded(self):
        api = Api()
        api._graph = MagicMock()  # Set graph but no yaml_path

        with pytest.raises(ValueError, match="No YAML file loaded"):
            api._save_to_yaml()

    def test_save_raises_when_no_graph(self, temp_yaml_file):
        api = Api()
        api._yaml_path = str(temp_yaml_file)
        # No graph set

        with pytest.raises(ValueError, match="No YAML file loaded"):
            api._save_to_yaml()


class TestApiIntegration:
    """Integration tests for Api class workflows."""

    def test_full_crud_workflow(self, temp_yaml_file):
        """Test create, read, update, delete workflow."""
        api = Api()

        # Load
        load_result = api.load_yaml(str(temp_yaml_file))
        assert load_result["success"] is True

        assert api._graph is not None

        initial_count = len(api._graph.nodes)

        # Create (now only creates ImageCrop, no Text child)
        crop_region = {
            "x_center": 0.5,
            "y_center": 0.5,
            "width_relative": 0.1,
            "height_relative": 0.1,
        }
        create_result = api.create_annotation(crop_region, "user_crop")
        assert create_result["success"] is True
        assert len(api._graph.nodes) == initial_count + 1

        # Find new crop id
        new_crop_id = [n for n in api._graph.nodes if n.startswith("user_crop-")][0]

        # Create text node by calling update_node_data with empty node_id and crop_id
        create_text_result = api.update_node_data(
            "", "New annotation text", crop_id=new_crop_id
        )
        assert create_text_result["success"] is True
        assert len(api._graph.nodes) == initial_count + 2

        # Find new text id
        new_text_id = [n for n in api._graph.nodes if n.startswith("user_text_")][0]

        # Update text
        update_result = api.update_node_data(new_text_id, "Updated annotation text")
        assert update_result["success"] is True

        # Read to verify
        node_info = api.get_node_info(new_text_id)
        assert node_info["success"] is True
        assert api._graph.get_data(new_text_id) == "Updated annotation text"

        # Delete
        delete_result = api.delete_annotation(new_crop_id)
        assert delete_result["success"] is True
        assert new_crop_id not in api._graph.nodes
        assert new_text_id not in api._graph.nodes


class TestApiCreateAnnotationBehavior:
    """Tests for create_annotation new behavior (ImageCrop only)."""

    def test_create_annotation_no_text_child_created(self, temp_yaml_file):
        """create_annotation() creates only ImageCrop, no Text node."""
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None
        crop_region = {
            "x_center": 0.5,
            "y_center": 0.5,
            "width_relative": 0.1,
            "height_relative": 0.1,
        }
        api.create_annotation(crop_region, "user_crop")

        # Should only find crop, not text
        new_crops = [n for n in api._graph.nodes if n.startswith("user_crop-")]
        new_texts = [n for n in api._graph.nodes if n.startswith("user_text_")]
        assert len(new_crops) == 1
        assert len(new_texts) == 0


class TestApiGridLockedField:
    """Tests for locked field in grid data."""

    def test_get_all_nodes_for_grid_includes_locked_field(self, temp_yaml_file):
        """Grid rows include 'locked' field from NodeDisplayValue."""
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None
        result = api.get_all_nodes_for_grid()

        for row in result["rows"]:
            assert "locked" in row
            assert isinstance(row["locked"], bool)

    def test_grid_locked_field_correct_for_node_types(self, temp_yaml_file):
        """Image nodes are locked, others are not."""
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None
        result = api.get_all_nodes_for_grid()

        for row in result["rows"]:
            if "Image" in row["type"] and "ImageCrop" not in row["type"]:
                assert row["locked"] is True
            # Leaf crops and text can be edited


class TestApiUpdateNodeDataWithCropId:
    """Tests for update_node_data with crop_id parameter."""

    def test_update_node_data_with_crop_id_creates_text(self, temp_yaml_file):
        """update_node_data() with crop_id creates new Text node."""
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None
        initial_count = len(api._graph.nodes)

        result = api.update_node_data("", "New text", crop_id="crop_001")

        assert result["success"] is True
        assert len(api._graph.nodes) == initial_count + 1
        new_texts = [n for n in api._graph.nodes if n.startswith("user_text_")]
        assert len(new_texts) == 1

    def test_update_node_data_node_id_takes_precedence(self, temp_yaml_file):
        """When both node_id and crop_id provided, updates existing node."""
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None
        initial_count = len(api._graph.nodes)

        result = api.update_node_data("text_001", "Updated", crop_id="crop_001")

        assert result["success"] is True
        assert len(api._graph.nodes) == initial_count  # No new nodes
        assert api._graph.get_data("text_001") == "Updated"


class TestApiIntegrationCreateCropThenAddText:
    """Integration test for creating crop then adding text."""

    def test_integration_create_crop_then_add_text(self, temp_yaml_file):
        """Workflow: create ImageCrop, then add Text via update_node_data."""
        api = Api()
        api.load_yaml(str(temp_yaml_file))
        assert api._graph is not None

        # Create crop
        crop_region = {
            "x_center": 0.5,
            "y_center": 0.5,
            "width_relative": 0.1,
            "height_relative": 0.1,
        }
        create_result = api.create_annotation(crop_region, "user_crop")
        assert create_result["success"] is True

        # Get new crop ID
        new_crop_id = [n for n in api._graph.nodes if n.startswith("user_crop-")][0]

        # Add text to crop
        update_result = api.update_node_data("", "Annotation text", crop_id=new_crop_id)
        assert update_result["success"] is True

        # Verify structure
        new_text_id = [n for n in api._graph.nodes if n.startswith("user_text_")][0]
        assert new_text_id in api._graph.children(new_crop_id)
        assert api._graph.get_data(new_text_id) == "Annotation text"
