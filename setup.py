from setuptools import setup, find_namespace_packages

def _parse_requirements(file_path):
    with open(file_path, 'r') as stream:
        file = stream.readlines()
    return file

setup(
    name="exposurestats",
    version="1.0.0",
    description="Photo Statistics fo Exposure Image Editor",
    classifiers=[
        "Programming Language :: Python :: 3.8",
    ],
    keywords="photography",
    url="https://github.com/luismavs/ExposureStats",
    author="Luís Seabra",
    author_email="luismavseabra@gmail.com",
    install_requires=_parse_requirements("requirements.txt"),
    license="MIT",
    python_requires=">=3.8",
    zip_safe=False,
)