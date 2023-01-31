# Usage

The `readimc` package exports two classes for reading IMC .mcd and IMC .txt files:

```python
from readimc import MCDFile, TXTFile
```

## Loading IMC .txt files

IMC .txt files can be loaded as follows:

```python
with TXTFile("/path/to/file.txt") as f:
    print(f.channel_names)  # metals
    print(f.channel_labels)  # targets
```

### Reading IMC acquisitions

The acquisition contained in an IMC .txt file can be read as follows:

```python
with TXTFile("/path/to/file.txt") as f:
    img = f.read_acquisition()  # numpy array, shape: (c, y, x), dtype: float32
```

```{note}
IMC .txt files only contain a single IMC acquisition.
```

## Loading IMC .mcd files

IMC .mcd files can be loaded as follows:

```python
with MCDFile("/path/to/file.mcd") as f:
    num_slides = len(f.slides)
```

```{note}
Although uncommon, a single IMC .mcd file can contain multiple slides. Each slide can
have zero or more panorama images and zero or more IMC acquisitions.
```

### Extracting metadata

Basic metadata on slides, panoramas and acquisitions can be accessed through properties:

```python
with MCDFile("/path/to/file.mcd") as f:
    # first slide
    slide = f.slides[0]
    print(
        slide.id,
        slide.description,
        slide.width_um,
        slide.height_um,
    )
    # first panorama of first slide
    panorama = slide.panoramas[0]
    print(
        panorama.id,
        panorama.description,
        panorama.width_um,
        panorama.height_um,
    )
    # first acquisition of first slide
    acquisition = slide.acquisitions[0]
    print(
        acquisition.id,
        acquisition.description,
        acquisition.width_um,
        acquisition.height_um,
        acquisition.channel_names,  # metals
        acquisition.channel_labels,  # targets
    )
```

For a full list of available properties, please consult the API documentation of the
`Slide`, `Panorama` and `Acquisition` classes (additional metadata is available through
their `metadata` properties). The complete metadata embedded in IMC .mcd files is
accessible through `MCDFile.schema_xml` (in proprietary XML format).

### Reading slide images

IMC .mcd files can store slide images uploaded by the user (e.g., photographs) or
acquired by the instrument. For
[supported image file formats](https://imageio.readthedocs.io/en/stable/formats.html),
these images can be read as follows:

```python
with MCDFile("/path/to/file.mcd") as f:
    slide = f.slides[0]  # first slide
    img = f.read_slide(slide)  # numpy array or None
```

### Reading panorama images

IMC .mcd files can contain zero or more panorama images acquired by the instrument,
which can be read as follows:

```python
with MCDFile("/path/to/file.mcd") as f:
    panorama = f.slides[0].panoramas[0]  # first panorama of first slide
    img = f.read_panorama(panorama)  # numpy array
```

```{note}
`Slide.panoramas` only exposes panoramas for which panorama images are available. The
raw metadata accessible through `MCDFile.schema_xml` may contain additional panorama
entries of type `"Default"` that represent "virtual" panoramas and do not correspond
to actual images.
```

### Reading IMC acquisitions

IMC .mcd files can contain zero or more IMC acquisitions, which can be read as follows:

```python
with MCDFile("/path/to/file.mcd") as f:
    acquisition = f.slides[0].acquisitions[0]  # first acquisition of first slide
    img = f.read_acquisition(acquisition)  # array, shape: (c, y, x), dtype: float32
```

### Reading before/after-ablation images

The IMC instrument may be configured to acquire an optical image before/after each IMC
acquisition. If available, these before/after-ablation images can be read as follows:

```python
with MCDFile("/path/to/file.mcd") as f:
    acquisition = f.slides[0].acquisitions[0]  # first acquisition of first slide
    before_ablation_img = f.read_before_ablation_image(acquisition)  # array or None
    after_ablation_img = f.read_after_ablation_image(acquisition)  # array or None
```
