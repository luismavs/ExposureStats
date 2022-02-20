from pathlib import Path
from exposurestats.data_source import DataSource
from exposurestats.config import Config, get_config
import yaml


def testread_one_sidecar():

    cfg = get_config('./config.yaml')

    print(cfg)

#    file_path = Path('/Users/luis/Pictures/Lisboa 2020-/2021/07/31 - Dornes/Exposure Software/Exposure X6/P8011007.JPG.exposurex6')
    
    with open ('.config.yaml', 'rt') as f:
        cfg_ = yaml.safe_load(f)
    
    file_path = Path(cfg_['test_image'])

    ds = DataSource(cfg)
    ds.read_one_sidecar(file_path)

    assert True

if __name__ == '__main__':

    testread_one_sidecar()