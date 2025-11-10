from setuptools import setup, find_packages

setup(
    name="geocode_selenium",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "selenium",
        "webdriver_manager",
    ],
)
