from setuptools import setup
# TODO: include package data (templates)
setup(
    name='syrup',
    version='0.0.1',
    py_modules=['syrup'],
    install_requires=[
        'click',
        'requests',
        'Pillow',
    ],
    entry_points='''
        [console_scripts]
        syrup=syrup:cli
    ''',
)