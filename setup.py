import io
import re
from setuptools import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

with io.open('battenberg/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)


install_requires = [
    'Click>=6.0',
    'cookiecutter>=1.6.0',
    # You'll also need to install libgit2 to get this to work.
    # See instructions here: https://www.pygit2.org/install.html
    'pygit2>=1.0'
]

setup(
    name='battenberg',
    version=version,
    description="Providing updates to cookiecutter projects.",
    long_description=readme + '\n\n' + history,
    long_description_content_type="text/markdown",
    author="Zillow",
    url='https://github.com/zillow/battenberg',
    project_urls={
        "Documentation": "https://github.com/zillow/battenberg/README.md",
        "Changelog": "https://github.com/zillow/battenberg/HISTORY.md",
        "Code": "https://github.com/zillow/battenberg",
        "Issue tracker": "https://github.com/zillow/battenberg/issues",
    },
    packages=[
        'battenberg',
    ],
    package_dir={'battenberg': 'battenberg'},
    entry_points={
        'console_scripts': [
            'battenberg=battenberg.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=install_requires,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='battenberg',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12'
    ],
    python_requires=">=3.9",
    extras_require={
        'dev': ['pytest', 'pytest-cov', 'flake8', 'codecov']
    }
)
