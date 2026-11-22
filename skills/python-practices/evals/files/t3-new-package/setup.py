from setuptools import setup

setup(
    name="slugtools",
    version="0.1.0",
    packages=["slugtools"],
    install_requires=["unidecode==1.3.8"],
    entry_points={"console_scripts": ["slug=slugtools.cli:main"]},
)
