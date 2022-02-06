# ExposureStats

Streamlit App to display Exposure Image Editor Photo Stats.

## To install

Recommended python version is python3.10

    pip install -r requirements.txt


To install as a local package

    pip install -e .

To install requirements for notebooks

    sh install_nbs.sh

## Screenshot

![plot](./data/screenshot.png)

## Comments

For the moment, reads a config file in the project dir.

Notebook folder has an older version, jupyter + seaborn based. 


## To Do

- Tests

- Package/Deploy as a container?

- Fix the  **key not in dict: '@alienexposure:lens'** error for some jpegs. This way they don't show up.

- Exposure X7 support?

- Bug when selected lens is empty

