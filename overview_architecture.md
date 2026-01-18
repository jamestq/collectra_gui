# Format

A collectra file consists of:

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
        id: root_image_label-ril-1
        orientation: north
        data: relative_src_image.jpg        

    cropped_image_inside_root_image:
        id: cropped_image_inside_root_image-1
        data: relative_src_image.jpg
        parents: root_image_label-ril-1
        orientation: west
        x_center: 0.5
        y_center: 0.5
        width_relative: 0.4
        height_relative: 0.3

    sub_cropped_image:
        - id: sub_cropped_image-1
          data: relative_src_image.jpg
          parents: cropped_image_inside_root_image-1
          orientation: west
          x_center: 0.5
          y_center: 0.5
          width_relative: 0.4
          height_relative: 0.3
        - id: sub_cropped_image-2
          data: relative_src_image.jpg
          parents: cropped_image_inside_root_image-1
          orientation: west
          x_center: 0.2
          y_center: 0.3
          width_relative: 0.3
          height_relative: 0.4
    
    text_draft:
        - id: text_draft-1
          data: hello_world
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
          parents:
          - cropped_image_inside_root_image-1
          - text_draft-1
        - id: text_2
          data: how are you
          parents:
          - cropped_image_inside_root_image-1
          - text_draft-2

```