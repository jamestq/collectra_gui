"""
Parses YAML structure, builds lineage relationships, and computes display values
for ImageCrop annotations based on the rules:

1. Container crop (has ImageCrop children) → display blank
2. Leaf crop with Text child → traverse to deepest Text → display that text
3. Leaf crop without Text child → display blank

"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping

import networkx as nx
from pydantic import BaseModel
from rich import print
from typing_extensions import Self

from .utils import normalise_items


class Metadata(BaseModel):
    """Metadata for collectra results."""

    key: str = "collectra_results_metadata"
    version: str = "1.0.0"
    workflow: str = "collectra_gui"
    timestamp: str = ""

    def model_dump(self, *args, **kwargs) -> dict:
        data = super().model_dump(*args, **kwargs)
        key = data.pop("key", None)
        if key is None:
            raise ValueError("Metadata key is missing.")
        return data


class CollectraNodeFactory:

    @staticmethod
    def create_node(data: dict) -> "CollectraNode":
        """Factory method to create appropriate CollectraNode subclass."""
        node_type = data.get("type", "")
        if "ImageCrop" in node_type:
            crop_region = CollectraCropRegion(
                x_center=data["x_center"],
                y_center=data["y_center"],
                width_relative=data["width_relative"],
                height_relative=data["height_relative"],
            )
            return CollectraAnnotationNode(**data, crop_region=crop_region)
        return CollectraNode(**data)


class CollectraNode(BaseModel):
    """Node in the annotation graph."""

    id: str
    type: str
    data: str = ""
    label: str = ""  # Added for label lookup
    parents: list[str] = []

    def model_dump(self, *args, **kwargs) -> dict[str, str | float]:
        data = super().model_dump(*args, **kwargs)
        label = data.pop("label", None)  # Exclude label from dump
        if "parents" in data:
            data["parents"] = (
                data["parents"][0] if len(data["parents"]) == 1 else data["parents"]
            )
        if label is None:
            raise ValueError("Label is missing from node data.")
        return data


class CollectraCropRegion(BaseModel):
    """Crop region fields for annotation nodes."""

    x_center: float
    y_center: float
    width_relative: float
    height_relative: float


class CollectraAnnotationNode(CollectraNode):
    """Annotation node in the graph."""

    crop_region: CollectraCropRegion

    @property
    def crop(self) -> dict[str, float]:
        """Return crop region as a dict."""
        return self.crop_region.model_dump()

    def model_dump(self, *args, **kwargs) -> dict[str, str | float]:
        data = super().model_dump(*args, **kwargs)
        data.pop("crop_region", None)  # Remove crop_region field
        for key, value in self.crop.items():
            data[key] = value
        return data


class NodeDisplayValue(BaseModel):
    """Display value for a node."""

    reason: str
    value: str | None = None
    source_id: str | None = None
    crop_region: dict[str, float] | None = None
    locked: bool = False


@dataclass
class CollectraGraph:
    """
    Graph structure for annotation lineage relationships.

    Provides clean interface for traversal without external dependencies.
    """

    _graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    metadata: Metadata = field(default_factory=Metadata)

    # Cached indexes for O(1) lookups
    _children_index: dict[str, list[str]] = field(default_factory=dict, repr=False)
    _parents_index: dict[str, list[str]] = field(default_factory=dict, repr=False)

    @property
    def nodes(self) -> list[str]:
        """List of node IDs in the graph."""
        if self._graph is None:
            return []
        return list(self._graph.nodes)

    @classmethod
    def from_yaml_data(cls, data: dict) -> "CollectraGraph":
        """Build graph from parsed YAML data."""
        graph = cls()

        metadata = data.pop("collectra_results_metadata", dict())

        if metadata:
            graph.metadata = Metadata(**metadata)

        for label, value in data.items():
            items = normalise_items(value)
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    item["label"] = label  # Store label for reverse lookup
                    graph.add_node(item)

        return graph

    def add_node(self, data: dict) -> None:
        """Add a node and its parent edges."""
        data["parents"] = normalise_items(data.get("parents", []))
        node = CollectraNodeFactory.create_node(data)
        self._graph.add_node(
            node.id,
            node=node,
        )

        for parent in data["parents"]:
            self._graph.add_edge(parent, node.id)

    def children(self, node_id: str) -> list[str]:
        """Get immediate children of a node."""
        return list(self._graph.successors(node_id))

    def parents(self, node_id: str) -> list[str]:
        """Get immediate parents of a node."""
        return list(self._graph.predecessors(node_id))

    def _get_node(self, node_id: str) -> CollectraNode | None:
        """Get the AnnotationNode object for a given node ID."""
        node = self._graph.nodes.get(node_id, {}).get("node", None)
        return node

    def get_type(self, node_id: str) -> str:
        """Get type of a node."""
        node = self._get_node(node_id)
        return node.type if node else ""

    def get_data(self, node_id: str) -> str:
        """Get data field of a node."""
        node = self._get_node(node_id)
        return node.data if node else ""

    def get_crop_region(self, node_id: str) -> dict[str, float]:
        """
        Get the crop region coordinates of a node.

        Args:
            node_id: The node ID to get crop region from

        Returns:
            dict with x_center, y_center, width_relative, height_relative

        Raises:
            ValueError: If node is missing crop region fields
        """
        node = self._get_node(node_id)
        if not isinstance(node, CollectraAnnotationNode):
            raise ValueError(f"Node {node_id} is not an annotation node.")

        return node.crop

    def set_data(self, node_id: str, data: str, crop_id: str | None = None) -> None:
        """Set data field of a node."""
        if node_id:
            node = self._get_node(node_id)
            if node is None:
                raise ValueError(f"Node {node_id} not found in graph.")
            node.data = data
            return
        if not crop_id:
            raise ValueError(f"Node {node_id} not found and crop_id not provided.")
        text_data = {
            "label": "user_annotation_text",
            "type": "collectra.Text",
            "id": f"user_text_{uuid.uuid4().hex[:8]}",
            "parents": crop_id,
            "data": data,
        }
        self.add_node(text_data)

    def set_crop_region(self, node_id: str, crop_region: dict[str, float]) -> None:
        """Set crop region fields of a node (x_center, y_center, width_relative, height_relative)."""
        node = self._get_node(node_id)
        crop: CollectraCropRegion = CollectraCropRegion(**crop_region)
        if not isinstance(node, CollectraAnnotationNode):
            raise ValueError(f"Node {node_id} is not an annotation node.")
        node.crop_region = crop

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all edges connected to it."""
        self._graph.remove_node(node_id)

    def children_of_type(self, node_id: str, type_substr: str) -> list[str]:
        """Get immediate children containing type_substr in their type."""
        return [
            child_id
            for child_id in self.children(node_id)
            if type_substr in self.get_type(child_id)
        ]

    def dfs_leaves(self, start: str, type_filter: str) -> list[str]:
        """
        DFS traversal following only edges to nodes matching type_filter.
        Returns leaf nodes (nodes with no children of the filtered type).
        """
        leaves = []
        visited = set()
        stack = [start]

        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue
            visited.add(node_id)

            # Get children matching the type filter
            typed_children = self.children_of_type(node_id, type_filter)

            if not typed_children:
                # This is a leaf in the filtered subgraph
                leaves.append(node_id)
            else:
                stack.extend(typed_children)

        return leaves

    def find_deepest(self, start: str, type_filter: str) -> str:
        """
        Find the deepest node reachable from start following only type_filter edges.
        Returns the first leaf found (DFS order).
        """
        leaves = self.dfs_leaves(start, type_filter)
        return leaves[0] if leaves else ""

    def to_yaml_data(self) -> dict:
        """Convert graph back to YAML data structure."""
        yaml_data: dict = {}

        for node_id in self._graph.nodes:
            node = self._get_node(node_id)
            if node is None:
                continue
            node_data = node.model_dump()
            yaml_data.setdefault(node.label, []).append({**node_data})

        final_data: dict[str, list[dict] | dict] = dict()

        if self.metadata:
            metadata = self.metadata.model_dump()
            final_data[self.metadata.key] = metadata

        for key, value in yaml_data.items():
            if isinstance(value, list) and len(value) == 1:
                final_data[key] = value[0]
            else:
                final_data[key] = value

        return final_data

    def compute_display_value(self, node_id: str) -> NodeDisplayValue:
        """
        Compute display value for an annotation.

        Args:
            node_id: The node ID to compute display value for

        Returns:
            NodeDisplayValue with value, source_id, crop_region, reason
        """
        if self._get_node(node_id) is None:
            return NodeDisplayValue(reason=f"{node_id} Element not found")

        node_type = self.get_type(node_id)

        # Rule: Image type displays empty
        if "Image" in node_type and "ImageCrop" not in node_type:
            return NodeDisplayValue(
                reason=f"{node_id} is of collectra.Image type: display blank",
                locked=True,
            )

        # Rules for ImageCrop
        if "ImageCrop" in node_type:
            crop_data = self.get_crop_region(node_id)

            # Rule 1: Container crop (has ImageCrop children)
            if self.children_of_type(node_id, "ImageCrop"):
                return NodeDisplayValue(
                    crop_region=crop_data,
                    reason=f"{node_id} is a container crop: display blank",
                    locked=True,
                )

            # Rule 2: Leaf crop with Text child
            text_children = self.children_of_type(node_id, "Text")
            text_children = text_children[0] if text_children else ""
            if text_children:
                deepest_id = self.find_deepest(text_children, "Text")
                if deepest_id == "":
                    raise ValueError(
                        f"Expected to find deepest Text child for node {node_id}, but none found."
                    )
                deepest_data = self.get_data(deepest_id) if deepest_id else ""
                return NodeDisplayValue(
                    value=deepest_data,
                    source_id=deepest_id,
                    crop_region=crop_data,
                    reason=f"Leaf crop {node_id} with Text child: deepest Text is {deepest_id}",
                )

            # Rule 3: Leaf crop without Text child
            return NodeDisplayValue(
                value="",
                source_id="",
                crop_region=crop_data,
                reason=f"Leaf crop {node_id} without Text child",
            )

        # Text elements (for completeness)
        if "Text" in node_type:
            return NodeDisplayValue(
                value=self.get_data(node_id),
                source_id=node_id,
                crop_region=None,
                reason="Text element: display data",
            )

        return NodeDisplayValue(
            value="",
            source_id="",
            crop_region=None,
            reason="Unknown type",
        )
