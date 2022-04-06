from setuptools import setup, find_namespace_packages

def _parse_requirements(file_path):
    with open(file_path, 'r') as stream:
        file = stream.readlines()
    return file

setup(
    name="exposurestats",
    version="1.1.1",
    description="Photo Statistics for Exposure Image Editor",
    classifiers=[
        "Programming Language :: Python :: 3.10",
    ],
    keywords="photography",
    url="https://github.com/luismavs/ExposureStats",
    author="Luís Seabra",
    author_email="luismavseabra@gmail.com",
    install_requires=['pandas','xmltodict', 'altair', 'streamlit', 'pyyaml', 'watchdog', 'tqdm'],
    license="MIT",
    python_requires=">=3.8",
    zip_safe=False,
)
