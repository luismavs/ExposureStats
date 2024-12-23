# ExposureStats

Streamlit App to display Exposure Image Editor Photo Stats.
Should work both with X6 and X7 versions.

## To install

Recommended python version is python3.12

    sh install_tools.sh
    uv pip install -r requirements.txt
    uv pip install -e .

To install requirements for notebooks
    
    # this is probably outdated
    sh install_nbs.sh

## To Run

    streamlit run exposurestats/src/exposurestats/app.py

## Screenshot

![plot](./data/screenshot.png)

## Configuration
Environment variable **DEFAULT_PATH** pointing the Exposure library path. See template.env.


## Tests

Tests need an env var **test_image** set to a test file.

## Comments

Notebook folder has an older version, jupyter + seaborn based. 


## To Do

- Package/Deploy as a container?

