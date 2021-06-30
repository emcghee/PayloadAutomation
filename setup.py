import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="payload_automation",
    version="1.0.1",
    author="Faultline",
    author_email="@BinaryFaultline",
    description="A set of libraries to help automate payload development, testing, opsec checking, and deployment for Cobalt Strike",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/emcghee/PayloadAutomation",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPLv3 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'javaobj-py3>=0.4.1',
        'pepy>=1.2.0',
        'ptyprocess>=0.5',
        'pexpect',
        'magicfile',
	'PyYAML==5.4.1'
    ],
)
