from setuptools import setup, find_packages
setup(
    name="yaixmutils",
    version="1.0.1",
    description="YAIXM utilities",
    url="https://github.com/ahsparrow/yaixmutils",
    author="Alan Sparrow",
    author_email="yaixmutils@freeflight.org.uk",
    license="GPL",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Text Processing",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ],
    keywords=['airspace', 'aixm', 'yaixm'],
    install_requires=["yaixm", "PyYAML", "pyparsing", "pygeodesy"],
    dependency_links=["git+https://github.com/ahsparrow/yaixm.git#egg=yaixm-1.3.1"],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            "yaixm_release = yaixmutils.cli:release",
            "yaixm_convert_obstacle = yaixmutils.cli:convert_obstacle",
            "yaixm_convert_tnp = yaixmutils.cli:convert_tnp"
        ]
    }
)
