# ExposureStats

Display Stats about an Exposure Image Editor Photo Library.

Count by camera, lens, date, ...

Tag images with AI - experimental version.

Working with both X6 and X7 versions.

## To install

Recommended python version is python3.12

```bash
sh install_tools.sh
uv pip install -r requirements.txt
uv pip install -e .
```


## To Run

    streamlit run src/exposurestats/app.py

Or use Docker.

## Screenshot

![plot](./data/screenshot.png)

## Configuration

Environment variable **DEFAULT_PATH** pointing to the Exposure library path. See template.env.

## Docker Deployment

For running ExposureStats in a Docker environment, please refer to the detailed instructions in [docker/README.md](https://github.com/luismavs/ExposureStats/blob/main/docker/README.md).

## Tests

Tests need an env var **test_image** set to a test file.

## Comments

Notebook folder has an older version, jupyter + seaborn based.

To install requirements for notebooks

```bash
# this is probably outdated
sh install_nbs.sh
```