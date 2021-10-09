# Usage

The `readimc` package exports two classes for reading Fluidigm&reg; MCD&trade; and TXT files:

```python
from readimc import IMCMCDFile, IMCTXTFile
```

## Loading Fluidigm&reg; TXT files

Fluidigm&reg; TXT files can be loaded as follows:

```python
with IMCTXTFile("/path/to/file.txt") as f:
    print(f.channel_names)  # metals
    print(f.channel_labels)  # targets
```

### Reading IMC&trade; acquisitions

The acquisition contained in a Fluidigm&reg; TXT file can be read as follows:

```python
with IMCTXTFile("/path/to/file.txt") as f:
    img = f.read_acquisition()  # numpy array, shape: (c, y, x), dtype: float32
```

```{note}
Fluidigm&reg; TXT files only contain a single IMC&trade; acquisition.
```

## Loading Fluidigm&reg; MCD&trade; files

Fluidigm&reg; MCD&trade; files can be loaded as follows:

```python
with IMCMCDFile("/path/to/file.mcd") as f:
    num_slides = len(f.slides)
```

```{note}
Although uncommon, a single Fluidigm&reg; MCD&trade; file can contain multiple slides. Each slide can have zero or more panorama images and zero or more IMC&trade; acquisitions.
```

### Extracting metadata

Basic metadata on slides, panoramas and acquisitions can be accessed through properties:

```python
with IMCMCDFile("/path/to/file.mcd") as f:
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

For a full list of available properties, please consult the API documentation of the `Slide`, `Panorama` and `Acquisition` classes (additional metadata is available through their `metadata` properties).

The complete metadata embedded in Fluidigm&reg; MCD&trade; files is accessible through `IMCMCDFile.xml` (in proprietary Fluidigm&reg; XML format) and can be converted to a text representation as follows:

```python
from xml.etree import ElementTree as ET

with IMCMCDFile("/path/to/file.mcd") as f:
    xml_as_str = ET.tostring(
        f.xml,  # ET.Element
        encoding="unicode",
        xml_declaration=True,
        default_namespace=f.xmlns,
    )
```

### Reading slide images

Fluidigm&reg; MCD&trade; files can store slide images uploaded by the user (e.g., photographs) or acquired by the instrument. For [supported image file formats](https://imageio.readthedocs.io/en/stable/formats.html), these images can be read as follows:

```python
with IMCMCDFile("/path/to/file.mcd") as f:
    slide = f.slides[0]  # first slide
    img = f.read_slide(slide)  # numpy array or None
```

### Reading panorama images

Fluidigm&reg; MCD&trade; files can contain zero or more panorama images acquired by the instrument, which can be read as follows:

```python
with IMCMCDFile("/path/to/file.mcd") as f:
    panorama = f.slides[0].panoramas[0]  # first panorama of first slide
    img = f.read_panorama(panorama)  # numpy array
```

```{note}
`Slide.panoramas` only exposes panoramas for which panorama images are available. The raw metadata accessible through `IMCMCDFile.xml` may contain additional panorama entries of type `"Default"` that represent "virtual" panoramas and do not correspond to actual images.
```

### Reading IMC&trade; acquisitions

Fluidigm&reg; MCD&trade; files can contain zero or more IMC&trade; acquisitions, which can be read as follows:

```python
with IMCMCDFile("/path/to/file.mcd") as f:
    acquisition = f.slides[0].acquisitions[0]  # first acquisition of first slide
    img = f.read_acquisition(acquisition)  # numpy array, shape: (c, y, x), dtype: float32
```

### Reading before/after-ablation images

The IMC&trade; instrument may be configured to acquire an optical image before/after each IMC&trade; acquisition. If available, these before/after-ablation images can be read as follows:

```python
with IMCMCDFile("/path/to/file.mcd") as f:
    acquisition = f.slides[0].acquisitions[0]  # first acquisition of first slide
    before_ablation_img = f.read_before_ablation_image(acquisition)  # numpy array or None
    after_ablation_img = f.read_after_ablation_image(acquisition)  # numpy array or None
```