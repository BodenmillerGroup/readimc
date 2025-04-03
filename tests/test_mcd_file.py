from hashlib import md5
from pathlib import Path

import numpy as np
import pytest
import shutil
import tempfile
from typing import List, Tuple, Union

from readimc import MCDFile


class TestMCDFile:
    damond_mcd_file_path = Path("data/Damond2019/20170814_G_SE.mcd")

    @classmethod
    def setup_class(cls):
        if cls.damond_mcd_file_path.exists():
            cls.damond_mcd_file = MCDFile(cls.damond_mcd_file_path)
            cls.damond_mcd_file.open()
        else:
            cls.damond_mcd_file = None

    @classmethod
    def teardown_class(cls):
        if cls.damond_mcd_file is not None:
            cls.damond_mcd_file.close()
            cls.damond_mcd_file = None

    def test_schema_xml(self, imc_test_data_mcd_file: MCDFile):
        digest = md5(imc_test_data_mcd_file.schema_xml.encode("utf-8")).digest()
        assert digest == b"\xac\xd8@\x0f\x0b\xf4p\x89\xdd!\xe7o\x19\xa6\x8d\x97"

    def test_slides(self, imc_test_data_mcd_file: MCDFile):
        assert len(imc_test_data_mcd_file.slides) == 1

        slide = imc_test_data_mcd_file.slides[0]
        assert slide.id == 0
        assert slide.description == "Slide"
        assert slide.width_um == 75000.0
        assert slide.height_um == 25000.0
        assert len(slide.panoramas) == 1
        assert len(slide.acquisitions) == 3

        panorama = next(p for p in slide.panoramas if p.id == 1)
        assert panorama.slide == slide
        assert panorama.id == 1
        assert panorama.description == "Panorama_001"
        assert panorama.width_um == 193.0
        assert panorama.height_um == 162.0
        assert panorama.points_um == (
            (31020.0, 13486.0),
            (31213.0, 13486.0),
            (31213.0, 13324.0),
            (31020.0, 13324.0),
        )
        assert len(panorama.acquisitions) == 0

        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        assert acquisition.slide == slide
        assert acquisition.panorama is None
        assert acquisition.id == 1
        assert acquisition.description == "ROI_001"
        assert acquisition.width_px == 60
        assert acquisition.height_px == 60
        assert acquisition.pixel_size_x_um == 1.0
        assert acquisition.pixel_size_y_um == 1.0
        assert acquisition.width_um == 60.0
        assert acquisition.height_um == 60.0
        assert acquisition.num_channels == 5
        assert tuple(acquisition.channel_metals) == (
            "Ag",
            "Pr",
            "Sm",
            "Eu",
            "Yb",
        )
        assert tuple(acquisition.channel_masses) == (107, 141, 147, 153, 172)
        assert tuple(acquisition.channel_labels) == (
            "107Ag",
            "Cytoker_651((3356))Pr141",
            "Laminin_681((851))Sm147",
            "YBX1_2987((3532))Eu153",
            "H3K27Ac_1977((2242))Yb172",
        )
        assert tuple(acquisition.channel_names) == (
            "Ag107",
            "Pr141",
            "Sm147",
            "Eu153",
            "Yb172",
        )
        assert acquisition.roi_points_um == (
            (31080.0, 13449.0),
            (31140.0, 13449.0),
            (31140.0, 13389.0),
            (31080.0, 13389.0),
        )
        assert acquisition.roi_coords_um == (
            (31080.0, 13449.0),
            (31139.799043811327, 13450.084762417044),
            (31140.501, 13390.28),
            (31080.701956188677, 13389.195237582955),
        )

    def test_read_acquisition(self, imc_test_data_mcd_file: MCDFile) -> None:
        # 1. Test the standard read without channels or region
        slide = imc_test_data_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        
        img_full: np.ndarray = imc_test_data_mcd_file.read_acquisition(acquisition=acquisition)
        assert acquisition != None
        assert img_full.dtype == np.float32
        assert img_full.shape == (5, 60, 60)

        # 2. Test with specified channels
        channels: List[int] = [0, 2]
        img_channels: np.ndarray = imc_test_data_mcd_file.read_acquisition(
            acquisition=acquisition, channels=channels
        )
        assert img_channels.dtype == np.float32
        assert img_channels.shape == (2, 60, 60)

        # 3. Test with specified region
        region: Tuple[int, int, int, int] = (10, 10, 50, 50)
        img_region: np.ndarray = imc_test_data_mcd_file.read_acquisition(
            acquisition=acquisition, region=region
        )
        assert img_region.dtype == np.float32
        assert img_region.shape == (5, 40, 40)

        # 4. Test with invalid region
        invalid_region_1: Tuple[int, int, int, int] = (0, 0, 1000, 1000)
        with pytest.raises(ValueError, match="Region is larger than the image"):
            imc_test_data_mcd_file.read_acquisition(acquisition=acquisition, region=invalid_region_1)

        # 5. Test for ValueError when no acquisition is provided
        with pytest.raises(ValueError, match="acquisition must be specified"):
            imc_test_data_mcd_file.read_acquisition(acquisition=None)

        # 6. Test for ValueError when invalid channel indices are provided
        with pytest.raises(ValueError, match="Invalid channel indices"):
            imc_test_data_mcd_file.read_acquisition(
                acquisition=acquisition, channels=[999]  # Out-of-bounds index
        )

        # 7. Test for ValueError when an invalid region tuple is provided
        with pytest.raises(ValueError, match="region must be a tuple of integers"):
            imc_test_data_mcd_file.read_acquisition(acquisition=acquisition, region=(0, 0, 10, "invalid"))  # Type mismatch

        # 8. Test for ValueError when region bounds are out of order
        invalid_region_2: Tuple[int, int, int, int] = (50, 50, 10, 10)  # Invalid region
        with pytest.raises(ValueError, match="region must be \\(x_min, y_min, x_max, y_max\\)"):
            imc_test_data_mcd_file.read_acquisition(acquisition=acquisition, region=invalid_region_2)

        # 10. Test for handling empty acquisition data with a warning
        acquisition.metadata["DataStartOffset"] = "100"
        acquisition.metadata["DataEndOffset"] = "100"
        with pytest.warns(UserWarning, match="contains empty acquisition image data"):
            img_empty: np.ndarray = imc_test_data_mcd_file.read_acquisition(acquisition=acquisition)
            assert img_empty.shape == (5, 60, 60)

        # 12. Test for reading with `strict=False`, allowing recovery from issues
        acquisition.metadata["DataStartOffset"] = "100"
        acquisition.metadata["DataEndOffset"] = "105"  # Corrupted but will try to recover
        img_recover: np.ndarray = imc_test_data_mcd_file.read_acquisition(acquisition=acquisition, strict=False)
        assert img_recover.shape == (5, 60, 60)

        # 13. Test for IOError when invalid data offsets are provided
        acquisition.metadata["DataStartOffset"] = "200"
        acquisition.metadata["DataEndOffset"] = "100"  # Invalid offsets
        with pytest.raises(IOError, match="invalid data offsets or byte size"):
            imc_test_data_mcd_file.read_acquisition(acquisition=acquisition)

    '''def test_memory_mapping_with_temp_file(self, imc_test_data_mcd_file: MCDFile):
        slide = imc_test_data_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        # Ensure a writable temp directory
        temp_dir = Path(tempfile.mkdtemp())  # Create a temporary writable directory
        try:
            img_memmap: np.ndarray = imc_test_data_mcd_file.read_acquisition(
                acquisition=acquisition, create_temp_file=temp_dir
            )

            # Assertions
            assert img_memmap.dtype == np.float32
            assert img_memmap.shape == (5, 60, 60)
            assert not img_memmap.flags["WRITEABLE"]  # Memory-mapped arrays are read-only
        finally:
            shutil.rmtree(temp_dir)  # Cleanup the temp directory after the test'''

    def test_read_acquisition_empty_data(self, imc_test_data_mcd_file: MCDFile):
        slide = imc_test_data_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        acquisition.metadata["DataStartOffset"] = "100"
        acquisition.metadata["DataEndOffset"] = "100"
        with pytest.warns(UserWarning, match="contains empty acquisition image data"):
            img = imc_test_data_mcd_file.read_acquisition(acquisition=acquisition)
            assert img.shape == (5, 60, 60)

    def test_read_slide(self, imc_test_data_mcd_file: MCDFile):
        slide = imc_test_data_mcd_file.slides[0]
        img = imc_test_data_mcd_file.read_slide(slide)
        assert img is not None
        assert img.dtype == np.uint8
        assert img.shape == (669, 2002, 4)

    def test_read_panorama(self, imc_test_data_mcd_file: MCDFile):
        slide = imc_test_data_mcd_file.slides[0]
        panorama = next(p for p in slide.panoramas if p.id == 1)
        img = imc_test_data_mcd_file.read_panorama(panorama)
        assert img.dtype == np.uint8
        assert img.shape == (162, 193, 4)

    def test_read_before_ablation_image(self, imc_test_data_mcd_file: MCDFile):
        slide = imc_test_data_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = imc_test_data_mcd_file.read_before_ablation_image(acquisition)
        assert img is None

    def test_read_after_ablation_image(self, imc_test_data_mcd_file: MCDFile):
        slide = imc_test_data_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = imc_test_data_mcd_file.read_after_ablation_image(acquisition)
        assert img is None

    @pytest.mark.skipif(not damond_mcd_file_path.exists(), reason="data not available")
    def test_schema_xml_damond(self, imc_test_data_mcd_file: MCDFile):
        digest = md5(imc_test_data_mcd_file.schema_xml.encode("utf-8")).digest()
        assert digest == b"\xac\xd8@\x0f\x0b\xf4p\x89\xdd!\xe7o\x19\xa6\x8d\x97"

    @pytest.mark.skipif(not damond_mcd_file_path.exists(), reason="data not available")
    def test_slides_damond(self):
        assert len(self.damond_mcd_file.slides) == 1

        slide = self.damond_mcd_file.slides[0]
        assert slide.id == 1
        assert slide.description == "compensationslide1000"
        assert slide.width_um == 75000.0
        assert slide.height_um == 25000.0
        assert len(slide.panoramas) == 8
        assert len(slide.acquisitions) == 41

        panorama = next(p for p in slide.panoramas if p.id == 1)
        assert panorama.slide == slide
        assert panorama.id == 1
        assert panorama.description == "TuningTape"
        assert panorama.width_um == 1472.9184890671672
        assert panorama.height_um == 1526.6011674842225
        assert panorama.points_um == (
            (28961.0, 6460.0),
            (30433.682653484964, 6486.356736527695),
            (30461.0, 4960.0),
            (28988.317346515036, 4933.643263472244),
        )
        assert len(panorama.acquisitions) == 5

        acquisition = next(a for a in panorama.acquisitions if a.id == 1)
        assert acquisition.slide == slide
        assert acquisition.panorama == panorama
        assert acquisition.id == 1
        assert acquisition.description == "TT_G01"
        assert acquisition.width_px == 51
        assert acquisition.height_px == 50
        assert acquisition.pixel_size_x_um == 1.0
        assert acquisition.pixel_size_y_um == 1.0
        assert acquisition.width_um == 51.0
        assert acquisition.height_um == 50.0
        assert acquisition.num_channels == 3
        assert tuple(acquisition.channel_metals) == ("Eu", "Eu", "Lu")
        assert tuple(acquisition.channel_masses) == (151, 153, 175)
        assert tuple(acquisition.channel_labels) == ("151Eu", "153Eu", "175Lu")
        assert tuple(acquisition.channel_names) == ("Eu151", "Eu153", "Lu175")
        assert acquisition.roi_points_um == (
            (29195.563447789347, 6091.267354770278),
            (29245.675268795687, 6091.269356041085),
            (29245.67326752488, 6041.381177047424),
            (29195.781085989598, 6041.606820330908),
        )
        assert acquisition.roi_coords_um is None

    @pytest.mark.skipif(not damond_mcd_file_path.exists(), reason="data not available")
    def test_read_acquisition_damond(self):
        slide = self.damond_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = self.damond_mcd_file.read_acquisition(acquisition=acquisition)
        assert img.dtype == np.float32
        assert img.shape == (3, 50, 51)

    @pytest.mark.skipif(not damond_mcd_file_path.exists(), reason="data not available")
    def test_read_slide_damond(self):
        slide = self.damond_mcd_file.slides[0]
        img = self.damond_mcd_file.read_slide(slide)
        assert img.dtype == np.uint8
        assert img.shape == (930, 2734, 3)

    @pytest.mark.skipif(not damond_mcd_file_path.exists(), reason="data not available")
    def test_read_panorama_damond(self):
        slide = self.damond_mcd_file.slides[0]
        panorama = next(p for p in slide.panoramas if p.id == 1)
        img = self.damond_mcd_file.read_panorama(panorama)
        assert img.dtype == np.uint8
        assert img.shape == (4096, 3951, 4)

    @pytest.mark.skipif(not damond_mcd_file_path.exists(), reason="data not available")
    def test_read_before_ablation_image_damond(self):
        slide = self.damond_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = self.damond_mcd_file.read_before_ablation_image(acquisition)
        assert img is None

    @pytest.mark.skipif(not damond_mcd_file_path.exists(), reason="data not available")
    def test_read_after_ablation_image_damond(self):
        slide = self.damond_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = self.damond_mcd_file.read_after_ablation_image(acquisition)
        assert img is None
