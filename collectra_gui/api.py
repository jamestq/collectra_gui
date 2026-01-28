"""
API backend for annotation display logic via pywebview's js_api interface.

JavaScript usage:
    await pywebview.api.load_yaml("path/to/results.yaml")
    const result = await pywebview.api.get_display_value("node_id")
    const nodes = await pywebview.api.get_all_nodes()
"""

import base64
import enum
import os
from pathlib import Path

import typer
import webview
import webview.menu as menu
import yaml
from pydantic import BaseModel
from rich import print

from collectra_gui.lineage_display import CollectraGraph, NodeDisplayValue

app = typer.Typer()


class ImageFormat(enum.Enum):
    PNG = "image/png"
    JPEG = "image/jpeg"
    JPG = "image/jpg"
    GIF = "image/gif"
    BMP = "image/bmp"
    WEBP = "image/webp"
    TIFF = "image/tiff"
    TIF = "image/tiff"


class Api:
    """
    API class exposed to JavaScript via pywebview.

    All public methods are accessible in JS as:
        window.pywebview.api.methodName(args)
    """

    def __init__(self):
        """
        Initialize the API instance.

        Sets up the annotation graph, YAML path, and window reference.
        All values are initially None until load_yaml() is called.
        """
        self._graph: CollectraGraph | None = None
        self._yaml_path: str | None = None
        self._window = None
        self._grapto_folders: list[dict] = []
        self._parent_folder: str | None = None

    def set_window(self, window):
        """Store the window reference for use in dialogs."""
        self._window = window

    def _scan_grapto_folder(self, folder_path: Path) -> dict | None:
        """
        Scan a folder for YAML and image files.

        Args:
            folder_path: Path to the folder to scan

        Returns:
            dict with yaml_path and image_path if both found, None otherwise
        """
        yaml_path = None
        image_path = None
        image_extensions = [f".{ext.lower()}" for ext in ImageFormat.__members__.keys()]

        for filename in folder_path.iterdir():
            if not filename.is_file():
                continue

            if filename.suffix in [".yaml", ".yml"] and yaml_path is None:
                yaml_path = filename

            if filename.suffix.lower() in image_extensions and image_path is None:
                image_path = filename

            if yaml_path and image_path:
                break

        if yaml_path is None or image_path is None:
            return None

        return {"yaml_path": str(yaml_path), "image_path": str(image_path)}

    def select_folder(self) -> dict:
        """
        Open native folder dialog and scan for YAML/image files.

        Returns:
            dict with folder_path, yaml_path, image_path (all absolute paths)
        """

        if self._window is None:
            return {"success": False, "error": "Window not initialized"}

        try:
            result = self._window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG)

            if not result or len(result) == 0:
                return {"success": False, "error": "No folder selected"}

            folder_path = Path(result[0])

            yaml_path = None
            image_path = None
            image_extensions = [
                f".{ext.lower()}" for ext in ImageFormat.__members__.keys()
            ]

            for filename in folder_path.iterdir():

                if not filename.is_file():
                    continue

                if filename.suffix in [".yaml", ".yml"] and yaml_path is None:
                    yaml_path = filename

                if filename.suffix in image_extensions and image_path is None:
                    image_path = filename

                if yaml_path and image_path:
                    break

            if yaml_path is None:
                return {"success": False, "error": "No YAML file found in folder"}
            if image_path is None:
                return {"success": False, "error": "No image file found in folder"}

            return {
                "success": True,
                "folder_path": str(folder_path),
                "yaml_path": str(yaml_path),
                "image_path": str(image_path),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def select_parent_folder(self) -> dict:
        """
        Open native folder dialog and scan for .grapto subdirectories.

        Returns:
            dict with parent_path and list of folder names/indices
        """
        if self._window is None:
            return {"success": False, "error": "Window not initialized"}

        try:
            result = self._window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG)

            if not result or len(result) == 0:
                return {"success": False, "error": "No folder selected"}

            parent_path = Path(result[0])
            self._parent_folder = str(parent_path)
            self._grapto_folders = []

            for entry in sorted(parent_path.iterdir()):
                if not entry.is_dir():
                    continue
                if not entry.suffix == ".grapto":
                    continue

                scan_result = self._scan_grapto_folder(entry)
                if scan_result is not None:
                    self._grapto_folders.append(
                        {
                            "name": entry.name,
                            "path": str(entry),
                            "yaml_path": scan_result["yaml_path"],
                            "image_path": scan_result["image_path"],
                        }
                    )

            folders = [
                {"name": f["name"], "index": i}
                for i, f in enumerate(self._grapto_folders)
            ]

            return {
                "success": True,
                "parent_path": str(parent_path),
                "folders": folders,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def load_grapto_folder(self, index: int) -> dict:
        """
        Load a .grapto folder by its index from the previously scanned parent folder.

        Args:
            index: Index of the folder in the _grapto_folders list

        Returns:
            dict with folder_name, yaml_path, image_path
        """
        if not self._grapto_folders:
            return {
                "success": False,
                "error": "No folders loaded. Call select_parent_folder first.",
            }

        if index < 0 or index >= len(self._grapto_folders):
            return {"success": False, "error": f"Invalid folder index: {index}"}

        folder = self._grapto_folders[index]
        return {
            "success": True,
            "folder_name": folder["name"],
            "folder_path": folder["path"],
            "yaml_path": folder["yaml_path"],
            "image_path": folder["image_path"],
        }

    def get_image_base64(self, image_path: str) -> dict:
        """
        Read an image file and return its base64 data.

        Args:
            image_path: Absolute path to the image file

        Returns:
            dict with base64-encoded data URI
        """
        try:
            extension = Path(image_path).suffix.lower()
            mime_type = ImageFormat[extension[1:].upper()].value

            with open(image_path, "rb") as f:
                image_data = f.read()

            base64_data = base64.b64encode(image_data).decode("utf-8")

            return {"success": True, "data": f"data:{mime_type};base64,{base64_data}"}

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

            self._graph = CollectraGraph.from_yaml_data(yaml_data)
            self._yaml_path = path

            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_display_value(self, node_id: str) -> dict:
        """
        Compute display value for an annotation.

        Args:
            node_id: The annotation ID

        Returns:
            dict with 'value', 'source_id', 'reason', or 'error'
        """
        if self._graph is None:
            return {"success": False, "error": "No graph loaded. Call load_yaml first."}

        try:
            result = self._graph.compute_display_value(node_id)
            return {
                "success": True,
                "value": result.value,
                "source_id": result.source_id,
                "crop_region": result.crop_region,
                "reason": result.reason,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_nodes(self) -> dict:
        """
        Get all node IDs in the graph.

        Returns:
            dict with 'nodes' list or 'error'
        """
        if self._graph is None:
            return {"success": False, "error": "No graph loaded. Call load_yaml first."}

        return {"success": True, "nodes": self._graph.nodes}

    def get_node_info(self, node_id: str) -> dict:
        """
        Get detailed information about a node.

        Args:
            node_id: The annotation ID

        Returns:
            dict with node type, data, children, parents, or 'error'
        """
        if self._graph is None:
            return {"success": False, "error": "No graph loaded. Call load_yaml first."}

        if node_id not in self._graph.nodes:
            return {"success": False, "error": f"Node '{node_id}' not found"}

        return {
            "success": True,
            "id": node_id,
            "type": self._graph.get_type(node_id),
            "data": self._graph.get_data(node_id),
            "children": self._graph.children(node_id),
            "parents": self._graph.parents(node_id),
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
            return {"success": False, "error": "No graph loaded. Call load_yaml first."}

        matching = [
            node_id
            for node_id in self._graph.nodes
            if type_filter in self._graph.get_type(node_id)
        ]

        return {"success": True, "nodes": matching, "count": len(matching)}

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
            node_display_value: NodeDisplayValue = self._graph.compute_display_value(
                node_id
            )
            rows.append(
                {
                    "id": node_id,
                    "type": self._graph.get_type(node_id),
                    "data": str(self._graph.get_data(node_id)),
                    "displayValue": node_display_value.value,
                    "crop_region": node_display_value.crop_region,
                    "displaySourceId": node_display_value.source_id,
                    "reason": node_display_value.reason,
                    "parents": ", ".join(self._graph.parents(node_id)),
                    "children": ", ".join(self._graph.children(node_id)),
                    "locked": node_display_value.locked,
                }
            )

        return {"success": True, "rows": rows}

    def update_node_data(
        self, node_id: str, new_data: str, crop_id: str | None = None
    ) -> dict:
        """
        Update the data of a specific node.

        Args:
            node_id: The annotation ID
            new_data: New data to set for the node

        Returns:
            dict with 'success' or 'error'
        """
        try:
            if self._graph is None:
                raise ValueError("No graph loaded. Call load_yaml first.")
            self._graph.set_data(node_id, new_data, crop_id)
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
            if self._graph is None:
                raise ValueError("No graph loaded. Call load_yaml first.")
            self._graph.set_crop_region(node_id, crop_region)
            self._save_to_yaml()
            return self.get_all_nodes_for_grid()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_annotation(self, crop_region: dict, label: str, parent_id: str) -> dict:
        """
        Create a new ImageCrop annotation with a Text child.

        Args:
            crop_region: dict with x_center, y_center, width_relative, height_relative

        Returns:
            dict with updated grid data or 'error'
        """
        if self._graph is None:
            return {"success": False, "error": "No graph loaded. Call load_yaml first."}

        try:
            import uuid

            # Find root Image node
            root_image_id = None
            for node_id in self._graph.nodes:
                node_type = self._graph.get_type(node_id)
                if "Image" in node_type and "ImageCrop" not in node_type:
                    root_image_id = node_id
                    break

            if root_image_id is None:
                return {"success": False, "error": "No root Image node found in graph."}

            # Generate unique IDs
            crop_id = f"{label}-{uuid.uuid4().hex[:8]}"

            if self._yaml_path is None:
                raise ValueError("YAML path is not set.")

            # Create ImageCrop node
            crop_data = {
                "label": label,
                "type": "collectra.ImageCrop",
                "id": crop_id,
                "parents": parent_id if parent_id else root_image_id,
                "data": Path(self._yaml_path).parent.name.replace(".yaml", ".jpg"),
                **crop_region,
            }
            self._graph.add_node(crop_data)
            # Save and return updated grid
            self._save_to_yaml()
            return self.get_all_nodes_for_grid()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_annotation(self, node_id: str) -> dict:
        """
        Delete an ImageCrop annotation and all its Text children.

        Args:
            node_id: The ImageCrop annotation ID to delete

        Returns:
            dict with updated grid data on success, or 'error' on failure
        """
        if self._graph is None:
            return {"success": False, "error": "No graph loaded. Call load_yaml first."}

        try:
            # Get all Text children before deleting the ImageCrop
            text_children = self._graph.children_of_type(node_id, "Text")

            # Delete Text children first
            for text_id in text_children:
                self._graph.remove_node(text_id)

            # Delete the ImageCrop node
            self._graph.remove_node(node_id)

            # Save and return updated grid
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
                yaml.dump(
                    {key: value if not isinstance(value, list) else value},
                    f,
                    sort_keys=False,
                )
                f.write("\n")


def get_resource_path(relative_path: str) -> str:
    """Get the path to a bundled resource, works for dev and PyInstaller."""
    import sys

    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        base_path = Path(getattr(sys, "_MEIPASS", ""))
    else:
        # Running in development
        base_path = Path(__file__).parent
    return str(base_path / relative_path)


@app.command()
def start(debug: bool = False):
    """
    Create and start the pywebview window with the API.

    Args:
        debug: Enable developer tools
    """
    api = Api()
    html_path = get_resource_path("index.html")
    window = webview.create_window(
        title="Annotation Display", url=html_path, js_api=api, width=1200, height=800
    )

    def on_started():
        api.set_window(window)

    webview.start(func=on_started, debug=debug)
    return window


if __name__ == "__main__":
    app()
