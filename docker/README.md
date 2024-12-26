# Docker

<p align="center">
  <img src="../data/docker.png" alt="Nutri-Score Logo" width="500">
</p>

Docker is an operating system level virtualization solution for delivering software in packages called containers.

We assume users have Docker correctly installed on their computer if they wish to use this feature. Docker is available for Linux as well as MacOS and Windows. For more details visit: https://www.docker.com/

## Running ExposureStats with Docker

### Quick Start

To run `ExposureStats` with docker, take the following steps:

```bash
# Clone the repository and change to directory
git clone git@github.com:luismavs/ExposureStats.git
cd ExposureStats

# Set the DEFAULT_PATH environment variable in your terminal

# 1.On Linux/macOS:
export DEFAULT_PATH=/your/actual/path/to/library

# 2.On Windows (PowerShell):
$env:DEFAULT_PATH="/your/actual/path/to/library"

# Build & run the docker image
docker-compose -f docker/compose.yaml up --build

```

## Environment Variables

Before running, make sure to set the `DEFAULT_PATH` on the terminal from the upper method or:

- Create a `.env` file based on `template.env`
- Set the DEFAULT_PATH to your Exposure library path
- Set test_image for running tests (Optional)

## Accessing the Application

Once running, you can access the Streamlit interface at: http://localhost:8501
