import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="automation-FAULTLINE", # Replace with your own username
    version="0.0.1",
    author="Faultline",
    author_email="@BinaryFaultline",
    description="A set of libraries to help automate payload development, testing, and deployment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="TBD",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPLv3 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)