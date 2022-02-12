from pathlib import Path
from exposurestats.data_source import DataSource
from exposurestats.config import Config, get_config


def test_read_one_image():

    cfg = get_config('./config.yaml')

    print(cfg)

#    file_path = Path('/Users/luis/Pictures/Lisboa 2020-/2021/07/31 - Dornes/Exposure Software/Exposure X6/P8011007.JPG.exposurex6')

    file_path = Path('/Users/luis/Pictures/Lisboa 2020-/2021/09/20 - Grécia/20 - Atenas e Meteora/Exposure Software/Exposure X7/P9220262dxoap.jpg.exposurex7')

    ds = DataSource(cfg)
    ds._read_one_image(file_path)

    assert True

if __name__ == '__main__':

    test_read_one_image()