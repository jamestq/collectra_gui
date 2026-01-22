"""
Demonstrates annotation display logic from overview_architecture.md.

Parses YAML structure, builds lineage relationships, and computes display values
for ImageCrop annotations based on the rules:
1. Container crop (has ImageCrop children) → display blank
2. Leaf crop with Text child → traverse to deepest Text → display that text
3. Leaf crop without Text child → display blank

NO EXTERNAL DEPENDENCIES - uses built-in libraries only.
"""

from typing import Any
from dataclasses import dataclass, field
from rich import print
import yaml


def normalize_parents(parents: Any) -> list[str]:
    """Convert parents field to list (handles single string or list)."""
    if parents is None:
        return []
    if isinstance(parents, str):
        return [parents]
    return list(parents)


@dataclass
class AnnotationGraph:
    """
    Graph structure for annotation lineage relationships.

    Provides clean interface for traversal without external dependencies.
    """
    metadata: dict[str, Any] = field(default_factory=dict)
    label_lookup: dict[str, str] = field(default_factory=dict)
    nodes: dict[str, dict] = field(default_factory=dict)
    edges: set[tuple[str, str]] = field(default_factory=set)  # (parent, child)

    # Cached indexes for O(1) lookups
    _children_index: dict[str, list[str]] = field(default_factory=dict, repr=False)
    _parents_index: dict[str, list[str]] = field(default_factory=dict, repr=False)

    @classmethod
    def from_yaml_data(cls, data: dict) -> "AnnotationGraph":
        """Build graph from parsed YAML data."""
        graph = cls()

        for label, value in data.items():
            if label == "collectra_results_metadata":
                graph.metadata = {label: value}
                continue
            items = value if isinstance(value, list) else [value]
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    graph.add_node(label, item["id"], item)

        return graph

    def add_node(self, label: str, node_id: str, data: dict) -> None:
        """Add a node and its parent edges."""
        self.label_lookup[node_id] = label
        self.nodes[node_id] = data        
        parents = normalize_parents(data.get("parents"))

        for parent_id in parents:
            self.edges.add((parent_id, node_id))

        # Invalidate cache
        self._children_index.clear()
        self._parents_index.clear()

    def _build_indexes(self) -> None:
        """Build parent/child indexes from edges."""
        if self._children_index:
            return

        for node_id in self.nodes:
            self._children_index[node_id] = []
            self._parents_index[node_id] = []

        for parent_id, child_id in self.edges:
            if parent_id in self._children_index:
                self._children_index[parent_id].append(child_id)
            if child_id in self._parents_index:
                self._parents_index[child_id].append(parent_id)

    def children(self, node_id: str) -> list[str]:
        """Get immediate children of a node."""
        self._build_indexes()
        return self._children_index.get(node_id, [])

    def parents(self, node_id: str) -> list[str]:
        """Get immediate parents of a node."""
        self._build_indexes()
        return self._parents_index.get(node_id, [])

    def get_type(self, node_id: str) -> str:
        """Get type of a node."""
        node = self.nodes.get(node_id)
        return node.get("type", "") if node else ""

    def get_data(self, node_id: str) -> str:
        """Get data field of a node."""
        node = self.nodes.get(node_id)
        return node.get("data", "") if node else ""
    
    def get_crop_region(self, node_id: str) -> dict[str, float]:        
        node = self.nodes.get(node_id)
        if not (node.get("x_center", None) and node.get("y_center", None) and 
                node.get("width_relative", None) and node.get("height_relative", None)):
            raise ValueError(f"Node {node_id} missing crop region fields.")
        return {
            "x_center": node["x_center"],
            "y_center": node["y_center"],
            "width_relative": node["width_relative"],
            "height_relative": node["height_relative"]
        }

    def set_data(self, node_id: str, data: str) -> None:
        """Set data field of a node."""
        node = self.nodes.get(node_id)
        if not node.get("data", ""):
            raise ValueError(f"Node {node_id} has no data field to set.")
        node["data"] = data

    def set_crop_region(self, node_id: str, crop_region: dict[str, float]) -> None:
        """Set crop region fields of a node (x_center, y_center, width_relative, height_relative)."""
        node = self.nodes.get(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found.")
        required_fields = ["x_center", "y_center", "width_relative", "height_relative"]
        for field in required_fields:
            if field not in crop_region:
                raise ValueError(f"Missing required field: {field}")
        node["x_center"] = crop_region["x_center"]
        node["y_center"] = crop_region["y_center"]
        node["width_relative"] = crop_region["width_relative"]
        node["height_relative"] = crop_region["height_relative"]

    def children_of_type(self, node_id: str, type_substr: str) -> list[str]:
        """Get immediate children containing type_substr in their type."""
        return [
            child_id for child_id in self.children(node_id)
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

    def find_deepest(self, start: str, type_filter: str) -> str | None:
        """
        Find the deepest node reachable from start following only type_filter edges.
        Returns the first leaf found (DFS order).
        """
        leaves = self.dfs_leaves(start, type_filter)        
        return leaves[0] if leaves else None

    def to_yaml_data(self) -> dict:
        """Convert graph back to YAML data structure."""
        yaml_data: dict[str, dict] = {}
        
        if self.metadata:
            yaml_data.update(self.metadata)

        for node_id, node_data in self.nodes.items():    
            label = self.label_lookup.get(node_id, "")
            if not label:        
                raise ValueError(f"Label not found for node ID {node_id}")
            type_key = node_data.get("type", "")
            if not type_key:
                raise ValueError(f"Type not found for node ID {node_id}")
            yaml_data.setdefault(label, []).append({
                **node_data})
                        
        return yaml_data


def compute_display_value(graph: AnnotationGraph, node_id: str) -> tuple[str, str, str]:
    """
    Compute display value for an annotation.
    Returns (display_value, reason).
    """
    if node_id not in graph.nodes:
        return ("", "", None, f"{node_id} Element not found")

    node_type = graph.get_type(node_id)

    # Rule: Image type displays empty
    if "Image" in node_type and "ImageCrop" not in node_type:        
        return ("", "", None, f"{node_id} is of collectra.Image type: display blank")

    # Rules for ImageCrop
    if "ImageCrop" in node_type:
        crop_data = graph.get_crop_region(node_id)

        # Rule 1: Container crop (has ImageCrop children)
        if graph.children_of_type(node_id, "ImageCrop"):
            return ("", "", crop_data, f"{node_id} is a container crop: display blank")

        # Rule 2: Leaf crop with Text child
        text_children = graph.children_of_type(node_id, "Text")        
        text_children = text_children[0] if text_children else ""
        if text_children:
            deepest_id = graph.find_deepest(text_children, "Text")
            deepest_data = graph.get_data(deepest_id) if deepest_id else ""            
            return (deepest_data, deepest_id, crop_data, f"Leaf crop {node_id} with Text child: deepest Text is {deepest_id}")

        # Rule 3: Leaf crop without Text child
        return ("", "", crop_data, f"Leaf crop {node_id} without Text child")

    # Text elements (for completeness)
    if "Text" in node_type:
        return (graph.get_data(node_id), node_id, None, "Text element: display data")

    return ("", "", None, "Unknown type")


def print_lineage(graph: AnnotationGraph) -> None:
    """Print the lineage structure."""
    print("=" * 60)
    print("LINEAGE STRUCTURE")
    print("=" * 60)

    # Build parent_to_children from edges for display
    parent_to_children: dict[str, list[str]] = {}
    for parent_id, child_id in graph.edges:
        if parent_id not in parent_to_children:
            parent_to_children[parent_id] = []
        parent_to_children[parent_id].append(child_id)

    print("\nParent -> Children mapping:")
    for parent_id, children in sorted(parent_to_children.items()):
        parent_type = graph.get_type(parent_id)
        print(f"  {parent_id} ({parent_type})")
        for child_id in children:
            child_type = graph.get_type(child_id)
            print(f"    -> {child_id} ({child_type})")

    print("\nChild -> Parents mapping:")
    for node_id in sorted(graph.nodes.keys()):
        parents = graph.parents(node_id)
        if parents:
            node_type = graph.get_type(node_id)
            print(f"  {node_id} ({node_type})")
            for parent_id in parents:
                parent_type = graph.get_type(parent_id)
                print(f"    <- {parent_id} ({parent_type})")


def print_display_values(graph: AnnotationGraph) -> None:
    """Print computed display values for all annotations."""
    print("\n" + "=" * 60)
    print("COMPUTED DISPLAY VALUES")
    print("=" * 60)

    # Group by type for clarity
    images = []
    crops = []
    texts = []

    for node_id in graph.nodes:
        node_type = graph.get_type(node_id)
        if "ImageCrop" in node_type:
            crops.append(node_id)
        elif "Image" in node_type:
            images.append(node_id)
        elif "Text" in node_type:
            texts.append(node_id)

    print("\n[Image Elements]")
    for node_id in sorted(images):
        display_val, display_id, reason = compute_display_value(graph, node_id)
        print(f"  {node_id}")
        print(f"    Value: '{display_val}'")
        print(f"    ID:    '{display_id}'")
        print(f"    Reason:  {reason}")

    print("\n[ImageCrop Elements]")
    for node_id in sorted(crops):
        display_val, display_id, reason = compute_display_value(graph, node_id)
        print(f"  {node_id}")
        print(f"    Value: '{display_val}'")
        print(f"    ID:    '{display_id}'")
        print(f"    Reason:  {reason}")

    print("\n[Text Elements (for reference)]")
    for node_id in sorted(texts):
        print(f"  {node_id}")
        print(f"    Data: '{graph.get_data(node_id)}'")


def main():
    data = "MMRIRN1505437_P350090.grapto/results.yaml"

    with open(data, "r") as f:
        yaml_data = yaml.safe_load(f)

    print("Annotation Display Logic Demo")
    print("Based on overview_architecture.md\n")

    # Build graph from YAML
    graph = AnnotationGraph.from_yaml_data(yaml_data)
    print(f"Parsed {len(graph.nodes)} nodes, {len(graph.edges)} edges\n")

    # Print results
    print_lineage(graph)    
    print_display_values(graph)    

if __name__ == "__main__":
    main()
