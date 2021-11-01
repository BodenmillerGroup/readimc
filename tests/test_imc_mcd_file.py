import numpy as np
import pytest

from hashlib import md5
from pathlib import Path
from xml.etree import ElementTree as ET

from readimc import IMCMcdFile


class TestIMCMcdFile:
    damond_mcd_file_path = Path("data/Damond2019/20170814_G_SE.mcd")

    @classmethod
    def setup_class(cls):
        if cls.damond_mcd_file_path.exists():
            cls.damond_mcd_file = IMCMcdFile(cls.damond_mcd_file_path)
            cls.damond_mcd_file.open()
        else:
            cls.damond_mcd_file = None

    @classmethod
    def teardown_class(cls):
        if cls.damond_mcd_file is not None:
            cls.damond_mcd_file.close()
            cls.damond_mcd_file = None

    def test_xml(self, imc_test_data_mcd_file: IMCMcdFile):
        mcd_xml = ET.tostring(
            imc_test_data_mcd_file.xml,
            encoding="us-ascii",
            method="xml",
            xml_declaration=False,
            default_namespace=imc_test_data_mcd_file.xmlns,
        )
        mcd_xml_digest = md5(mcd_xml).digest()
        assert mcd_xml_digest == b"D]\xfa\x15a\xb8\xe4\xb2z8od\x85c\xa9\xf9"

    def test_xmlns(self, imc_test_data_mcd_file: IMCMcdFile):
        mcd_xmlns = imc_test_data_mcd_file.xmlns
        assert mcd_xmlns == "http://www.fluidigm.com/IMC/MCDSchema_V2_0.xsd"

    def test_slides(self, imc_test_data_mcd_file: IMCMcdFile):
        assert len(imc_test_data_mcd_file.slides) == 1

        slide = imc_test_data_mcd_file.slides[0]
        assert slide.id == 0
        assert slide.description == "Slide"
        assert slide.width_um == 75000.0
        assert slide.height_um == 25000.0
        assert len(slide.panoramas) == 1
        assert len(slide.acquisitions) == 3

        panorama = next(p for p in slide.panoramas if p.id == 1)
        assert panorama.description == "Panorama_001"
        assert panorama.x1_um == 31020.0
        assert panorama.y1_um == 13486.0
        assert panorama.width_um == 193.0
        assert panorama.height_um == 162.0

        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        assert acquisition.description == "ROI_001"
        assert acquisition.start_x_um == 31080.0
        assert acquisition.start_y_um == 13449.0
        assert acquisition.width_um == 60.501000000000204
        assert acquisition.height_um == 58.719999999999345
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

    def test_read_acquisition(self, imc_test_data_mcd_file: IMCMcdFile):
        slide = imc_test_data_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = imc_test_data_mcd_file.read_acquisition(acquisition=acquisition)
        assert img.dtype == np.float32
        assert img.shape == (5, 60, 60)

    def test_read_slide(self, imc_test_data_mcd_file: IMCMcdFile):
        slide = imc_test_data_mcd_file.slides[0]
        img = imc_test_data_mcd_file.read_slide(slide)
        assert img.dtype == np.uint8
        assert img.shape == (669, 2002, 4)

    def test_read_panorama(self, imc_test_data_mcd_file: IMCMcdFile):
        slide = imc_test_data_mcd_file.slides[0]
        panorama = next(p for p in slide.panoramas if p.id == 1)
        img = imc_test_data_mcd_file.read_panorama(panorama)
        assert img.dtype == np.uint8
        assert img.shape == (162, 193, 4)

    def test_read_before_ablation_image(
        self, imc_test_data_mcd_file: IMCMcdFile
    ):
        slide = imc_test_data_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = imc_test_data_mcd_file.read_before_ablation_image(acquisition)
        assert img is None

    def test_read_after_ablation_image(
        self, imc_test_data_mcd_file: IMCMcdFile
    ):
        slide = imc_test_data_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = imc_test_data_mcd_file.read_after_ablation_image(acquisition)
        assert img is None

    @pytest.mark.skipif(
        not damond_mcd_file_path.exists(), reason="data not available"
    )
    def test_xml_damond(self, imc_test_data_mcd_file: IMCMcdFile):
        mcd_xml = ET.tostring(
            imc_test_data_mcd_file.xml,
            encoding="us-ascii",
            method="xml",
            xml_declaration=False,
            default_namespace=imc_test_data_mcd_file.xmlns,
        )
        mcd_xml_digest = md5(mcd_xml).digest()
        assert mcd_xml_digest == b"D]\xfa\x15a\xb8\xe4\xb2z8od\x85c\xa9\xf9"

    @pytest.mark.skipif(
        not damond_mcd_file_path.exists(), reason="data not available"
    )
    def test_xmlns_damond(self):
        mcd_xmlns = self.damond_mcd_file.xmlns
        assert mcd_xmlns == "http://www.fluidigm.com/IMC/MCDSchema.xsd"

    @pytest.mark.skipif(
        not damond_mcd_file_path.exists(), reason="data not available"
    )
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
        assert panorama.description == "TuningTape"
        assert panorama.x1_um == 28961.0
        assert panorama.y1_um == 6460.0
        assert panorama.width_um == 1472.9184890671672
        assert panorama.height_um == 1526.6011674842225

        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        assert acquisition.description == "TT_G01"
        assert acquisition.start_x_um == 29195.563447789347
        assert acquisition.start_y_um == 6091.267354770278
        assert acquisition.width_um == 51.0
        assert acquisition.height_um == 50.0
        assert acquisition.num_channels == 3
        assert tuple(acquisition.channel_metals) == ("Eu", "Eu", "Lu")
        assert tuple(acquisition.channel_masses) == (151, 153, 175)
        assert tuple(acquisition.channel_labels) == ("151Eu", "153Eu", "175Lu")
        assert tuple(acquisition.channel_names) == ("Eu151", "Eu153", "Lu175")

    @pytest.mark.skipif(
        not damond_mcd_file_path.exists(), reason="data not available"
    )
    def test_read_acquisition_damond(self):
        slide = self.damond_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = self.damond_mcd_file.read_acquisition(acquisition=acquisition)
        assert img.dtype == np.float32
        assert img.shape == (3, 50, 51)

    @pytest.mark.skipif(
        not damond_mcd_file_path.exists(), reason="data not available"
    )
    def test_read_slide_damond(self):
        slide = self.damond_mcd_file.slides[0]
        img = self.damond_mcd_file.read_slide(slide)
        assert img.dtype == np.uint8
        assert img.shape == (930, 2734, 3)

    @pytest.mark.skipif(
        not damond_mcd_file_path.exists(), reason="data not available"
    )
    def test_read_panorama_damond(self):
        slide = self.damond_mcd_file.slides[0]
        panorama = next(p for p in slide.panoramas if p.id == 1)
        img = self.damond_mcd_file.read_panorama(panorama)
        assert img.dtype == np.uint8
        assert img.shape == (4096, 3951, 4)

    @pytest.mark.skipif(
        not damond_mcd_file_path.exists(), reason="data not available"
    )
    def test_read_before_ablation_image_damond(self):
        slide = self.damond_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = self.damond_mcd_file.read_before_ablation_image(acquisition)
        assert img is None

    @pytest.mark.skipif(
        not damond_mcd_file_path.exists(), reason="data not available"
    )
    def test_read_after_ablation_image_damond(self):
        slide = self.damond_mcd_file.slides[0]
        acquisition = next(a for a in slide.acquisitions if a.id == 1)
        img = self.damond_mcd_file.read_after_ablation_image(acquisition)
        assert img is None
