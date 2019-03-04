from setuptools import setup, find_packages
# TODO: include package data (templates)
setup(
    name='syrup',
    version='0.0.1',
    packages=find_packages(),
    package_data={
        '': ['templates/*']
    },
    install_requires=[
        'click',
        'requests',
        'Pillow',
    ],
    entry_points='''
        [console_scripts]
        syrup=syrup.__main__:cli
    ''',
    zip_safe=True,
)