try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Serialize python objects to a dict',
    'author': 'Marky Egebäck',
    'url': 'https://github.com/egeback/pytodict',
    'download_url': 'https://github.com/egeback/pytodict',
    'author_email': 'marky@egeback.se',
    'version': '0.3',
    'install_requires': ['nose2', 'unittest2'],
    'packages': ['pytodict'],
    'scripts': [],
    'name': 'Python to_dict',
}

setup(**config)
