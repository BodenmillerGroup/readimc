import numpy as np

from readimc import TXTFile


class TestTXTFile:
    def test_num_channels(self, imc_test_data_txt_file: TXTFile):
        assert imc_test_data_txt_file.num_channels == 5

    def test_channel_metals(self, imc_test_data_txt_file: TXTFile):
        assert tuple(imc_test_data_txt_file.channel_metals) == (
            "Ag",
            "Pr",
            "Sm",
            "Eu",
            "Yb",
        )

    def test_channel_masses(self, imc_test_data_txt_file: TXTFile):
        assert tuple(imc_test_data_txt_file.channel_masses) == (
            107,
            141,
            147,
            153,
            172,
        )

    def test_channel_labels(self, imc_test_data_txt_file: TXTFile):
        assert tuple(imc_test_data_txt_file.channel_labels) == (
            "107Ag",
            "Cytoker_651((3356))Pr141",
            "Laminin_681((851))Sm147",
            "YBX1_2987((3532))Eu153",
            "H3K27Ac_1977((2242))Yb172",
        )

    def test_channel_names(self, imc_test_data_txt_file: TXTFile):
        assert tuple(imc_test_data_txt_file.channel_names) == (
            "Ag107",
            "Pr141",
            "Sm147",
            "Eu153",
            "Yb172",
        )

    def test_read_acquisition(self, imc_test_data_txt_file: TXTFile):
        img = imc_test_data_txt_file.read_acquisition()
        assert img.dtype == np.float32
        assert img.shape == (5, 60, 60)
