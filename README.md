# ExposureToolsSuite

2025-10-26 update: My goal with this project is to host a set of Python tools I use to manage my Exposure X7 library. Hope you find them useful. The project was born from my curiosity to show stats for lens usage in my personal library.

# ExposureStats

Display Stats about an Exposure Image Editor Photo Library.

Count by camera, lens, date, ...

Tag images with AI - experimental version.

Working with both X6 and X7 versions.

## To install

Recommended python version is 3.13

```bash
# install uv
uv sync --locked
```

## To Run

Execute `uv run streamlit run src/exposurestats/app.py`.

Or use Docker. At this stage, it is still probably best to use streamlit locally to simplify interaction with your local file system.

## Screenshot

![plot](./data/screenshot.png)

## Configuration

Environment variable **DEFAULT_PATH** pointing to the Exposure library path. See template.env.

## Docker Deployment

For running ExposureStats in a Docker environment, please refer to the detailed instructions in [docker/README.md](https://github.com/luismavs/ExposureStats/blob/main/docker/README.md).

## Tests

Tests need an env var **test_image** set to a test file.

## Development Tooling

Install taskfile

<https://taskfile.dev/docs/installation>

## Comments

Notebook folder has an older version, jupyter + seaborn based.

To install requirements for notebooks

```bash
# this is probably outdated
sh install_nbs.sh
```
