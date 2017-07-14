from setuptools import setup, find_packages

__version__ = '0.0.5'

setup(
    name='babbage_fiscal',
    version=__version__,
    description="API and Bi-directional converter babbage/fdp",
    long_description="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ],
    keywords='schema jsontableschema jts fdp fiscal data babbage',
    author='OpenSpending',
    author_email='info@openspending.org',
    url='https://github.com/openspending/babbage.fiscal-data-package',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'test']),
    namespace_packages=[],
    package_data={},
    include_package_data=True,
    zip_safe=False,
    test_suite='nose.collector',
    install_requires=[
        'babbage >= 0.1.1',
        'awesome-slugify',
        'sqlalchemy',
        'click',
        'datapackage',
        'jsontableschema',
        'celery>=3.1.25,<4',  # Version >4 removes support for SQLAlchemy.
                              # They re-added the support on https://github.com/celery/kombu/pull/687.
                              # When that's released, we can use versions >4
        'elasticsearch>=1.0.0,<2.0.0',
        'os-package-registry>=0.0.3',
        'jsontableschema-sql',
        'os-api-cache'
    ],
    dependency_links=[
        'git+git://github.com/akariv/jsontableschema-sql-py.git@feature/auto-index#egg=jsontableschema-sql'
    ],
    tests_require=[
        'tox',
    ],
    entry_points={
      'console_scripts': [
        'bb-fdp-cli = babbage_fiscal:cli',
      ]
    },
)
