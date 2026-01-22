"""
Tests for collectra_gui.lineage_display module.

Tests cover:
- normalize_parents helper function
- AnnotationGraph class methods
- compute_display_value function with all display rules
"""

import pytest

from collectra_gui.lineage_display import (
    AnnotationGraph,
    compute_display_value,
    normalize_parents,
)


class TestNormalizeParents:
    """Tests for normalize_parents helper function."""

    def test_none_returns_empty_list(self):
        assert normalize_parents(None) == []

    def test_single_string_returns_list(self):
        assert normalize_parents("parent_001") == ["parent_001"]

    def test_list_returns_list(self):
        assert normalize_parents(["p1", "p2"]) == ["p1", "p2"]

    def test_empty_list_returns_empty_list(self):
        assert normalize_parents([]) == []

    def test_tuple_converted_to_list(self):
        result = normalize_parents(("p1", "p2"))
        assert result == ["p1", "p2"]
        assert isinstance(result, list)


class TestAnnotationGraphFromYamlData:
    """Tests for AnnotationGraph.from_yaml_data class method."""

    def test_creates_graph_from_valid_data(self, sample_yaml_data):
        graph = AnnotationGraph.from_yaml_data(sample_yaml_data)
        assert len(graph.nodes) == 3
        assert "img_001" in graph.nodes
        assert "crop_001" in graph.nodes
        assert "text_001" in graph.nodes

    def test_parses_metadata(self, sample_yaml_data):
        graph = AnnotationGraph.from_yaml_data(sample_yaml_data)
        assert "collectra_results_metadata" in graph.metadata

    def test_empty_data_creates_empty_graph(self):
        graph = AnnotationGraph.from_yaml_data({})
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_creates_edges_from_parents(self, sample_yaml_data):
        graph = AnnotationGraph.from_yaml_data(sample_yaml_data)
        assert ("img_001", "crop_001") in graph.edges
        assert ("crop_001", "text_001") in graph.edges

    def test_handles_list_values(self, complex_yaml_data):
        graph = AnnotationGraph.from_yaml_data(complex_yaml_data)
        # Should have parsed both leaf crops
        assert "leaf_crop_001" in graph.nodes
        assert "leaf_crop_no_text" in graph.nodes

    def test_skips_items_without_id(self):
        data = {"label": [{"type": "collectra.Text", "data": "no id"}]}
        graph = AnnotationGraph.from_yaml_data(data)
        assert len(graph.nodes) == 0

    def test_handles_non_dict_items(self):
        data = {"label": ["string_item", 123, None]}
        graph = AnnotationGraph.from_yaml_data(data)
        assert len(graph.nodes) == 0


class TestAnnotationGraphAddNode:
    """Tests for AnnotationGraph.add_node method."""

    def test_adds_node_to_empty_graph(self, empty_graph):
        data = {"type": "collectra.Text", "id": "t1", "data": "hello"}
        empty_graph.add_node("label", "t1", data)
        assert "t1" in empty_graph.nodes
        assert empty_graph.label_lookup["t1"] == "label"

    def test_adds_edges_for_parents(self, empty_graph):
        empty_graph.add_node("l1", "parent", {"type": "t", "id": "parent"})
        empty_graph.add_node(
            "l2", "child", {"type": "t", "id": "child", "parents": "parent"}
        )
        assert ("parent", "child") in empty_graph.edges

    def test_handles_multiple_parents(self, empty_graph):
        empty_graph.add_node("l1", "p1", {"type": "t", "id": "p1"})
        empty_graph.add_node("l2", "p2", {"type": "t", "id": "p2"})
        empty_graph.add_node(
            "l3", "child", {"type": "t", "id": "child", "parents": ["p1", "p2"]}
        )
        assert ("p1", "child") in empty_graph.edges
        assert ("p2", "child") in empty_graph.edges

    def test_invalidates_cache_on_add(self, sample_graph):
        # Populate cache by calling children
        sample_graph.children("img_001")
        assert sample_graph._children_index  # Cache populated

        # Add new node
        sample_graph.add_node(
            "new_label",
            "new_node",
            {"type": "collectra.Text", "id": "new_node", "parents": "crop_001"},
        )
        assert not sample_graph._children_index  # Cache cleared


class TestAnnotationGraphTraversal:
    """Tests for children, parents, and traversal methods."""

    def test_children_returns_immediate_children(self, sample_graph):
        children = sample_graph.children("img_001")
        assert children == ["crop_001"]

    def test_children_returns_empty_for_leaf(self, sample_graph):
        children = sample_graph.children("text_001")
        assert children == []

    def test_children_returns_empty_for_unknown_node(self, sample_graph):
        children = sample_graph.children("nonexistent")
        assert children == []

    def test_parents_returns_immediate_parents(self, sample_graph):
        parents = sample_graph.parents("crop_001")
        assert parents == ["img_001"]

    def test_parents_returns_empty_for_root(self, sample_graph):
        parents = sample_graph.parents("img_001")
        assert parents == []

    def test_parents_returns_empty_for_unknown_node(self, sample_graph):
        parents = sample_graph.parents("nonexistent")
        assert parents == []

    def test_children_of_type_filters_correctly(self, complex_graph):
        crops = complex_graph.children_of_type("container_crop_001", "ImageCrop")
        assert "leaf_crop_001" in crops
        assert "leaf_crop_no_text" in crops

    def test_children_of_type_returns_empty_when_no_match(self, sample_graph):
        # text_001 has no children at all
        result = sample_graph.children_of_type("text_001", "Text")
        assert result == []

    def test_dfs_leaves_finds_leaves(self, complex_graph):
        # Starting from text_001, find leaves of type Text
        leaves = complex_graph.dfs_leaves("text_001", "Text")
        assert "text_002" in leaves

    def test_dfs_leaves_returns_start_if_no_children(self, sample_graph):
        leaves = sample_graph.dfs_leaves("text_001", "Text")
        assert leaves == ["text_001"]

    def test_find_deepest_returns_deepest_node(self, complex_graph):
        deepest = complex_graph.find_deepest("text_001", "Text")
        assert deepest == "text_002"

    def test_find_deepest_returns_start_if_leaf(self, sample_graph):
        deepest = sample_graph.find_deepest("text_001", "Text")
        assert deepest == "text_001"

    def test_find_deepest_returns_none_for_nonexistent_type(self, sample_graph):
        # Start from img_001, look for "NonExistent" type
        deepest = sample_graph.find_deepest("img_001", "NonExistent")
        # Should return img_001 as it's a leaf in "NonExistent" type subgraph
        assert deepest == "img_001"


class TestAnnotationGraphGetters:
    """Tests for get_type, get_data, get_crop_region."""

    def test_get_type_returns_type(self, sample_graph):
        assert sample_graph.get_type("img_001") == "collectra.Image"
        assert sample_graph.get_type("crop_001") == "collectra.ImageCrop"
        assert sample_graph.get_type("text_001") == "collectra.Text"

    def test_get_type_returns_empty_for_unknown(self, sample_graph):
        assert sample_graph.get_type("nonexistent") == ""

    def test_get_data_returns_data(self, sample_graph):
        assert sample_graph.get_data("text_001") == "Hello World"

    def test_get_data_returns_empty_for_unknown(self, sample_graph):
        assert sample_graph.get_data("nonexistent") == ""

    def test_get_crop_region_returns_coordinates(self, sample_graph):
        region = sample_graph.get_crop_region("crop_001")
        assert region["x_center"] == 0.5
        assert region["y_center"] == 0.5
        assert region["width_relative"] == 0.2
        assert region["height_relative"] == 0.1

    def test_get_crop_region_raises_for_missing_fields(self, sample_graph):
        with pytest.raises(ValueError, match="missing crop region"):
            sample_graph.get_crop_region("text_001")

    def test_get_crop_region_raises_for_partial_fields(self, empty_graph):
        # Node with only some crop fields
        empty_graph.add_node(
            "label",
            "partial_crop",
            {"type": "collectra.ImageCrop", "id": "partial_crop", "x_center": 0.5},
        )
        with pytest.raises(ValueError):
            empty_graph.get_crop_region("partial_crop")


class TestAnnotationGraphSetters:
    """Tests for set_data, set_crop_region."""

    def test_set_data_updates_value(self, sample_graph):
        sample_graph.set_data("text_001", "Updated text")
        assert sample_graph.get_data("text_001") == "Updated text"

    def test_set_data_raises_for_unknown_node(self, sample_graph):
        with pytest.raises(ValueError, match="not found"):
            sample_graph.set_data("nonexistent", "value")

    def test_set_data_raises_for_missing_data_field(self, empty_graph):
        empty_graph.add_node(
            "label", "node_no_data", {"type": "t", "id": "node_no_data"}
        )
        with pytest.raises(ValueError, match="no data field"):
            empty_graph.set_data("node_no_data", "value")

    def test_set_crop_region_updates_values(self, sample_graph):
        new_region = {
            "x_center": 0.8,
            "y_center": 0.9,
            "width_relative": 0.3,
            "height_relative": 0.4,
        }
        sample_graph.set_crop_region("crop_001", new_region)
        result = sample_graph.get_crop_region("crop_001")
        assert result == new_region

    def test_set_crop_region_raises_for_unknown_node(self, sample_graph):
        with pytest.raises(ValueError, match="not found"):
            sample_graph.set_crop_region("nonexistent", {"x_center": 0.5})

    def test_set_crop_region_raises_for_missing_required_field(self, sample_graph):
        incomplete = {"x_center": 0.5, "y_center": 0.5}  # Missing width/height
        with pytest.raises(ValueError, match="Missing required field"):
            sample_graph.set_crop_region("crop_001", incomplete)


class TestAnnotationGraphRemoveNode:
    """Tests for remove_node method."""

    def test_removes_node_from_nodes(self, sample_graph):
        sample_graph.remove_node("text_001")
        assert "text_001" not in sample_graph.nodes

    def test_removes_node_from_label_lookup(self, sample_graph):
        sample_graph.remove_node("text_001")
        assert "text_001" not in sample_graph.label_lookup

    def test_removes_edges_involving_node(self, sample_graph):
        sample_graph.remove_node("crop_001")
        # Edges to/from crop_001 should be gone
        assert ("img_001", "crop_001") not in sample_graph.edges
        assert ("crop_001", "text_001") not in sample_graph.edges

    def test_invalidates_cache_on_remove(self, sample_graph):
        sample_graph.children("img_001")  # Populate cache
        sample_graph.remove_node("text_001")
        assert not sample_graph._children_index

    def test_raises_for_unknown_node(self, sample_graph):
        with pytest.raises(ValueError, match="not found"):
            sample_graph.remove_node("nonexistent")


class TestAnnotationGraphToYamlData:
    """Tests for to_yaml_data method."""

    def test_roundtrip_preserves_structure(self, sample_yaml_data):
        graph = AnnotationGraph.from_yaml_data(sample_yaml_data)
        result = graph.to_yaml_data()

        # Check metadata preserved
        assert "collectra_results_metadata" in result

        # Check all nodes present in output
        all_ids = set()
        for key, value in result.items():
            if key == "collectra_results_metadata":
                continue
            items = value if isinstance(value, list) else [value]
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    all_ids.add(item["id"])

        assert all_ids == {"img_001", "crop_001", "text_001"}

    def test_raises_for_node_without_label(self, empty_graph):
        # Manually add node without proper label_lookup
        empty_graph.nodes["orphan"] = {"type": "t", "id": "orphan"}
        with pytest.raises(ValueError, match="Label not found"):
            empty_graph.to_yaml_data()

    def test_raises_for_node_without_type(self, empty_graph):
        empty_graph.label_lookup["orphan"] = "label"
        empty_graph.nodes["orphan"] = {"id": "orphan"}  # No type
        with pytest.raises(ValueError, match="Type not found"):
            empty_graph.to_yaml_data()


class TestComputeDisplayValue:
    """Tests for compute_display_value function."""

    def test_nonexistent_node_returns_not_found(self, sample_graph):
        value, source_id, crop_region, reason = compute_display_value(
            sample_graph, "nonexistent"
        )
        assert value == ""
        assert source_id == ""
        assert crop_region is None
        assert "not found" in reason

    def test_image_type_returns_blank(self, sample_graph):
        value, source_id, crop_region, reason = compute_display_value(
            sample_graph, "img_001"
        )
        assert value == ""
        assert "Image type" in reason or "Image" in reason

    def test_container_crop_returns_blank(self, complex_graph):
        value, source_id, crop_region, reason = compute_display_value(
            complex_graph, "container_crop_001"
        )
        assert value == ""
        assert crop_region is not None
        assert "container" in reason.lower()

    def test_leaf_crop_with_text_returns_deepest_text(self, complex_graph):
        value, source_id, crop_region, reason = compute_display_value(
            complex_graph, "leaf_crop_001"
        )
        assert value == "Deepest text"
        assert source_id == "text_002"
        assert crop_region is not None

    def test_leaf_crop_without_text_returns_blank(self, complex_graph):
        value, source_id, crop_region, reason = compute_display_value(
            complex_graph, "leaf_crop_no_text"
        )
        assert value == ""
        assert crop_region is not None
        assert "without Text" in reason

    def test_text_element_returns_own_data(self, sample_graph):
        value, source_id, crop_region, reason = compute_display_value(
            sample_graph, "text_001"
        )
        assert value == "Hello World"
        assert source_id == "text_001"
        assert crop_region is None

    def test_simple_leaf_crop_with_direct_text(self, sample_graph):
        value, source_id, crop_region, reason = compute_display_value(
            sample_graph, "crop_001"
        )
        assert value == "Hello World"
        assert source_id == "text_001"
        assert crop_region is not None

    def test_unknown_type_returns_blank(self, empty_graph):
        empty_graph.add_node(
            "label", "unknown_type", {"type": "collectra.Unknown", "id": "unknown_type"}
        )
        value, source_id, crop_region, reason = compute_display_value(
            empty_graph, "unknown_type"
        )
        assert value == ""
        assert "Unknown type" in reason


class TestComputeDisplayValueEdgeCases:
    """Edge case tests for compute_display_value."""

    def test_empty_text_data(self, empty_graph):
        empty_graph.add_node(
            "img",
            "img",
            {
                "type": "collectra.Image",
                "id": "img",
                "data": "test.jpg",
            },
        )
        empty_graph.add_node(
            "crop",
            "crop",
            {
                "type": "collectra.ImageCrop",
                "id": "crop",
                "parents": "img",
                "data": "test.jpg",
                "x_center": 0.5,
                "y_center": 0.5,
                "width_relative": 0.2,
                "height_relative": 0.1,
            },
        )
        empty_graph.add_node(
            "text",
            "text",
            {
                "type": "collectra.Text",
                "id": "text",
                "parents": "crop",
                "data": "",
            },
        )
        value, source_id, crop_region, reason = compute_display_value(
            empty_graph, "crop"
        )
        assert value == ""
        assert source_id == "text"

    def test_deeply_nested_text_chain(self, empty_graph):
        # Create a chain: Image -> Crop -> Text1 -> Text2 -> Text3
        empty_graph.add_node(
            "img", "img", {"type": "collectra.Image", "id": "img", "data": "test.jpg"}
        )
        empty_graph.add_node(
            "crop",
            "crop",
            {
                "type": "collectra.ImageCrop",
                "id": "crop",
                "parents": "img",
                "data": "test.jpg",
                "x_center": 0.5,
                "y_center": 0.5,
                "width_relative": 0.2,
                "height_relative": 0.1,
            },
        )
        empty_graph.add_node(
            "text1",
            "text1",
            {"type": "collectra.Text", "id": "text1", "parents": "crop", "data": "t1"},
        )
        empty_graph.add_node(
            "text2",
            "text2",
            {"type": "collectra.Text", "id": "text2", "parents": "text1", "data": "t2"},
        )
        empty_graph.add_node(
            "text3",
            "text3",
            {
                "type": "collectra.Text",
                "id": "text3",
                "parents": "text2",
                "data": "deepest",
            },
        )

        value, source_id, crop_region, reason = compute_display_value(
            empty_graph, "crop"
        )
        assert value == "deepest"
        assert source_id == "text3"
