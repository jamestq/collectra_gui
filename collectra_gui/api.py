"""
pywebview API backend for annotation display logic.

Exposes compute_display_value and related graph operations to JavaScript
via pywebview's js_api interface.

JavaScript usage:
    await pywebview.api.load_yaml("path/to/results.yaml")
    const result = await pywebview.api.get_display_value("node_id")
    const nodes = await pywebview.api.get_all_nodes()
"""

import webview
import webview.menu as menu
import typer
import yaml
import base64
import os
from pathlib import Path
from collectra_gui.lineage_display import AnnotationGraph, compute_display_value
from rich import print

app = typer.Typer() 

class Api:
    """
    API class exposed to JavaScript via pywebview.

    All public methods are accessible in JS as:
        window.pywebview.api.methodName(args)
    """

    def __init__(self):
        self._graph: AnnotationGraph | None = None
        self._yaml_path: str | None = None
        self._window = None

    def set_window(self, window):
        """Store the window reference for use in dialogs."""
        self._window = window

    def select_folder(self) -> dict:
        """
        Open native folder dialog and scan for YAML/image files.

        Returns:
            dict with folder_path, yaml_path, image_path (all absolute paths)
        """
        if self._window is None:
            return {"success": False, "error": "Window not initialized"}

        try:
            result = self._window.create_file_dialog(
                dialog_type=webview.FOLDER_DIALOG
            )

            if not result or len(result) == 0:
                return {"success": False, "error": "No folder selected"}

            folder_path = result[0]

            yaml_path = None
            image_path = None
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tif', '.tiff')

            for filename in os.listdir(folder_path):
                filepath = os.path.join(folder_path, filename)
                if not os.path.isfile(filepath):
                    continue

                lower_name = filename.lower()

                if lower_name.endswith(('.yaml', '.yml')) and yaml_path is None:
                    yaml_path = filepath

                if lower_name.endswith(image_extensions) and image_path is None:
                    image_path = filepath

            return {
                "success": True,
                "folder_path": folder_path,
                "yaml_path": yaml_path,
                "image_path": image_path
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_image_base64(self, image_path: str) -> dict:
        """
        Read an image file and return its base64 data.

        Args:
            image_path: Absolute path to the image file

        Returns:
            dict with base64-encoded data URI
        """
        try:
            extension = os.path.splitext(image_path)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp',
                '.tif': 'image/tiff',
                '.tiff': 'image/tiff'
            }
            mime_type = mime_types.get(extension, 'image/png')

            with open(image_path, 'rb') as f:
                image_data = f.read()

            base64_data = base64.b64encode(image_data).decode('utf-8')

            return {
                "success": True,
                "data": f"data:{mime_type};base64,{base64_data}"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def load_yaml(self, path: str) -> dict:
        """
        Load a YAML file and build the annotation graph.

        Args:
            path: Path to the YAML file

        Returns:
            dict with 'success', 'node_count', 'edge_count', or 'error'
        """
        try:
            with open(path, "r") as f:
                yaml_data = yaml.safe_load(f)

            self._graph = AnnotationGraph.from_yaml_data(yaml_data)
            self._yaml_path = path

            return {
                "success": True,
                "node_count": len(self._graph.nodes),
                "edge_count": len(self._graph.edges),
                "path": path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_display_value(self, node_id: str) -> dict:
        """
        Compute display value for an annotation.

        Args:
            node_id: The annotation ID

        Returns:
            dict with 'value', 'source_id', 'reason', or 'error'
        """
        if self._graph is None:
            return {
                "success": False,
                "error": "No graph loaded. Call load_yaml first."
            }

        try:
            value, source_id, reason = compute_display_value(self._graph, node_id)
            return {
                "success": True,
                "value": value,
                "source_id": source_id,
                "reason": reason
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_all_nodes(self) -> dict:
        """
        Get all node IDs in the graph.

        Returns:
            dict with 'nodes' list or 'error'
        """
        if self._graph is None:
            return {
                "success": False,
                "error": "No graph loaded. Call load_yaml first."
            }

        return {
            "success": True,
            "nodes": list(self._graph.nodes.keys())
        }

    def get_node_info(self, node_id: str) -> dict:
        """
        Get detailed information about a node.

        Args:
            node_id: The annotation ID

        Returns:
            dict with node type, data, children, parents, or 'error'
        """
        if self._graph is None:
            return {
                "success": False,
                "error": "No graph loaded. Call load_yaml first."
            }

        if node_id not in self._graph.nodes:
            return {
                "success": False,
                "error": f"Node '{node_id}' not found"
            }

        return {
            "success": True,
            "id": node_id,
            "type": self._graph.get_type(node_id),
            "data": self._graph.get_data(node_id),
            "children": self._graph.children(node_id),
            "parents": self._graph.parents(node_id)
        }

    def get_nodes_by_type(self, type_filter: str) -> dict:
        """
        Get all nodes containing a type substring.

        Args:
            type_filter: Substring to match in node types (e.g., "ImageCrop", "Text")

        Returns:
            dict with 'nodes' list of matching node IDs
        """
        if self._graph is None:
            return {
                "success": False,
                "error": "No graph loaded. Call load_yaml first."
            }

        matching = [
            node_id for node_id in self._graph.nodes
            if type_filter in self._graph.get_type(node_id)
        ]

        return {
            "success": True,
            "nodes": matching,
            "count": len(matching)
        }

    def get_display_values_for_type(self, type_filter: str) -> dict:
        """
        Compute display values for all nodes matching a type filter.

        Args:
            type_filter: Substring to match in node types

        Returns:
            dict with 'results' list of display value info
        """
        if self._graph is None:
            return {
                "success": False,
                "error": "No graph loaded. Call load_yaml first."
            }

        results = []
        for node_id in self._graph.nodes:
            if type_filter in self._graph.get_type(node_id):
                value, source_id, crop_region, reason = compute_display_value(self._graph, node_id)                
                results.append({
                    "node_id": node_id,
                    "type": self._graph.get_type(node_id),
                    "crop_region": crop_region,
                    "value": value,
                    "source_id": source_id,
                    "reason": reason
                })

        return {
            "success": True,
            "results": results,
            "count": len(results)
        }

    def get_all_nodes_for_grid(self) -> dict:
        """
        Return all nodes formatted for AG Grid rows.

        Returns:
            dict with 'rows' list containing node data for grid display
        """
        if self._graph is None:
            return {"success": False, "error": "No graph loaded. Call load_yaml first."}

        rows = []
        for node_id in self._graph.nodes:
            value, source_id, crop_region,reason = compute_display_value(self._graph, node_id)
            rows.append({
                "id": node_id,
                "type": self._graph.get_type(node_id),
                "data": str(self._graph.get_data(node_id)),
                "displayValue": value,
                "crop_region": crop_region,
                "displaySourceId": source_id,
                "reason": reason,
                "parents": ", ".join(self._graph.parents(node_id)),
                "children": ", ".join(self._graph.children(node_id)),
            })

        return {"success": True, "rows": rows}
    
    def update_node_data(self, node_id: str, new_data: str) -> dict:
        """
        Update the data of a specific node.

        Args:
            node_id: The annotation ID
            new_data: New data to set for the node

        Returns:
            dict with 'success' or 'error'
        """
        try:
            self._graph.set_data(node_id, new_data)
            self._save_to_yaml()
            return self.get_all_nodes_for_grid()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_node_coordinates(self, node_id: str, crop_region: dict) -> dict:
        """
        Update the crop region coordinates of a specific node.

        Args:
            node_id: The annotation ID
            crop_region: dict with x_center, y_center, width_relative, height_relative

        Returns:
            dict with 'success' and updated rows, or 'error'
        """
        try:
            self._graph.set_crop_region(node_id, crop_region)
            self._save_to_yaml()
            return self.get_all_nodes_for_grid()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _save_to_yaml(self) -> None:
        """Save the current graph back to the original YAML file."""
        if self._yaml_path is None or self._graph is None:
            raise ValueError("No YAML file loaded to save to.")
        yaml_data = self._graph.to_yaml_data()
        with open(self._yaml_path, "w") as f:
            for key, value in yaml_data.items():                
                yaml.dump({key: [value] if not isinstance(value, list) else value}, f, sort_keys=False)
                f.write("\n")        
        

    def get_lineage(self, node_id: str) -> dict:
        """
        Get the full lineage (ancestors and descendants) of a node.

        Args:
            node_id: The annotation ID

        Returns:
            dict with 'ancestors' and 'descendants' lists
        """
        if self._graph is None:
            return {
                "success": False,
                "error": "No graph loaded. Call load_yaml first."
            }

        if node_id not in self._graph.nodes:
            return {
                "success": False,
                "error": f"Node '{node_id}' not found"
            }

        # Get ancestors (traverse up)
        ancestors = []
        visited = set()
        stack = list(self._graph.parents(node_id))
        while stack:
            current = stack.pop()
            if current in visited or current not in self._graph.nodes:
                continue
            visited.add(current)
            ancestors.append({
                "id": current,
                "type": self._graph.get_type(current)
            })
            stack.extend(self._graph.parents(current))

        # Get descendants (traverse down)
        descendants = []
        visited = set()
        stack = list(self._graph.children(node_id))
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            descendants.append({
                "id": current,
                "type": self._graph.get_type(current)
            })
            stack.extend(self._graph.children(current))

        return {
            "success": True,
            "node_id": node_id,
            "ancestors": ancestors,
            "descendants": descendants
        }

@app.command()
def start(
    html_path = Path.cwd() / "collectra_gui/index.html",
    debug: bool = True
):
    """
    Create and start the pywebview window with the API.

    Args:
        html_path: Path to the HTML file to load
        debug: Enable developer tools
    """
    api = Api()
    print(html_path)
    window = webview.create_window(
        title="Annotation Display",
        url=html_path,
        js_api=api,
        width=1200,
        height=800
    )

    def on_started():
        api.set_window(window)

    webview.start(func=on_started, debug=debug)
    return window

@app.command()
def placeholder():
    """
    Placeholder command to allow script execution.
    """
    pass

if __name__ == "__main__":
    app()
