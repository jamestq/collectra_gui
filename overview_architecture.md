# Format

A collectra "file" is a folder consisting of:

```bash
|- collectra_folder.extension
|---- results.yaml
|---- relative_src_image.jpg
```

The results.yaml format:

```yaml
    collectra_results_metadata:
        workflow: workflow_name
        timestamp: time_stamp
    
    root_image_label:
        type: collectra.Image
        id: root_image_label-ril-1
        orientation: north
        data: relative_src_image.jpg        

    cropped_image_inside_root_image:
        id: cropped_image_inside_root_image-1
        type: collectra.ImageCrop
        data: relative_src_image.jpg
        parents: root_image_label-ril-1
        orientation: west
        x_center: 0.5
        y_center: 0.5
        width_relative: 0.4
        height_relative: 0.3
```

## Coordinate System

- All coordinates (`x_center`, `y_center`, `width_relative`, `height_relative`) are relative to the **root image** dimensions
- Origin: top-left (0, 0) to bottom-right (1, 1)
- `orientation` applies visual rotation after positioning:
  - `north` = 0° (default)
  - `west` = 90° counter-clockwise
  - `south` = 180°
  - `east` = 90° clockwise

## Workflow Stages

- `text_draft`: intermediate annotation data
- `text`: Output from workflow processing (e.g., OCR correction, validation), editable by user
- The `workflow` field in metadata identifies which processing pipeline was applied
- UI displays the deepest Text in the chain (the most processed version)

## Multi-Parent Relationships

- An element may reference multiple parents for provenance tracking
- The last parent in the array is the geometric container
- Additional parents provide lineage information
- Delete cascades trigger on ANY parent deletion

## YAML Array vs Object Rule

- Single items are stored as objects (e.g., `root_image_label`, `cropped_image_inside_root_image`)
- Multiple items of the same category are stored as arrays (e.g., `sub_cropped_image`, `text_draft`, `text`)

```yaml
    sub_cropped_image:
        - id: sub_cropped_image-1
          data: relative_src_image.jpg
          type: collectra.ImageCrop
          parents: cropped_image_inside_root_image-1
          orientation: west
          x_center: 0.5
          y_center: 0.5
          width_relative: 0.4
          height_relative: 0.3
        - id: sub_cropped_image-2
          data: relative_src_image.jpg
          type: collectra.ImageCrop
          parents: cropped_image_inside_root_image-1
          orientation: west
          x_center: 0.2
          y_center: 0.3
          width_relative: 0.3
          height_relative: 0.4
    
    text_draft:
        - id: text_draft-1
          data: hello_world
          type: collectra.Text
          parents:
          - cropped_image_inside_root_image-1
          - sub_cropped_image-1
        - id: text_draft-2
          data: how are you
          parents:
          - cropped_image_inside_root_image-1
          - sub_cropped_image-2
    
    text:
        - id: text_1
          data: hello_world
          type: collectra.Text
          parents:
          - cropped_image_inside_root_image-1
          - text_draft-1
        - id: text_2
          data: how are you
          parents:
          - cropped_image_inside_root_image-1
          - text_draft-2

```

## User Interface & Annotation display logic
- A simple upload form for user to drag one or multiple collectra files
- For each collectra file there will be:
  - A window displaying the image with the annotation boxes defined by the results.yaml file
  - A table displaying the content of the annotation boxes:
    - If the annotation box comes from a `collectra.Image` type, the displayed data should be empty (not editable).
    - If the annotation box comes from a `collectra.ImageCrop` type:
      1. **Container crop** (has any immediate ImageCrop children): Display blank (not editable)
      2. **Leaf crop** (no ImageCrop children) with immediate Text child: Traverse the Text chain (text_draft → text → ...) to find the deepest Text element and display its data (editable)
      3. **Leaf crop** without Text child: Display blank (not editable)
    - **Delete behavior**: When an annotation is deleted through the table, all elements listing it as ANY parent are also deleted (cascade). This applies recursively to children of children.
    - If an annotation box is created inside another annotation box, it should have the id of the annotation box it lives inside as the parent. That annotation box should have an immediate Text child element for saving the data in the table. 


## Tools
- Use static js and html
- [Use Annotorious for bounding boxes](https://annotorious.dev/getting-started/)
- [Server via python](https://pywebview.flowrl.com)