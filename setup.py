import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="payload_automation",
    version="1.0.6",
    author="Faultline",
    author_email="jahawkins623@gmail.com",
    description="A set of libraries to help be a bridge between Sleep and Python, helping to automate payload development, testing, opsec checking, beacon tasking, and deployment for Cobalt Strike",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/emcghee/PayloadAutomation",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
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
    download_url = 'https://github.com/emcghee/PayloadAutomation/archive/refs/tags/1.0.1.tar.gz',
)
