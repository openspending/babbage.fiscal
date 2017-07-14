# Babbage Fiscal Data Package Support

[![Gitter](https://img.shields.io/gitter/room/openspending/chat.svg)](https://gitter.im/openspending/chat)
[![Build Status](https://travis-ci.org/openspending/babbage.fiscal-data-package.svg?branch=master)](https://travis-ci.org/openspending/babbage.fiscal-data-package)
[![Coverage Status](https://coveralls.io/repos/openspending/babbage.fiscal-data-package/badge.svg?branch=master&service=github)](https://coveralls.io/github/openspending/babbage.fiscal-data-package?branch=master)

This module is intended to provide support for loading OKFN's Fiscal Data Packages into a DB, 
while creating an internal model compatible with ``babbage``.
 
## Usage

This section is intended to be used by end-users of the library.

### Installation

To get started (under development):

```
$ pip install babbage_fiscal
```

### Testing

To run the tests, make sure you have an ElasticSearch running locally on
http://localhost:9200 and run:

```
$ tox
```

### Command-line interface

You can use the library using a simple command line interface:

```bash
$ export FISCAL_PACKAGE_ENGINE=<database-connection-string>
$ bb-fdp-cli load-fdp --package <path--or-url-of-datapackage.json>
```

For example:
```bash
$ bb-fdp-cli load-fdp --package https://raw.githubusercontent.com/openspending/fiscal-data-package-demos/update-to-reflect-new-specs/boost-moldova/datapackage.json
```

### Python API

You can access the same functionality using a Python interface:

```python
from babbage_fiscal import FDPLoader

FDPLoader().load_fdp_to_db(package, engine)

# engine is an SQLAlchemy engine. 
# if not supplied, will create one based on the FISCAL_PACKAGE_ENGINE env variable
```

### API interface

The package also provides a Flask Blueprint, which exposes one endpoint with the following parameters:

 - ``package``: URL for ``datapackage.json``  
 - ``callback``: URL to call once load is complete
 
Example usage:
```python
from flask import Flask
from babbage_fiscal import FDPLoaderBlueprint

app = Flask('demo')
app.register_blueprint(FDPLoaderBlueprint, url_prefix='/loader')

app.run()
```

## Design Overview

Internally the loader uses the following packages

 - ``datapackage`` to parse the provided data-package and load its resources 
 - ``jts-sql`` to load the data into the database

The internal ``ModelRegistry`` class is used for managing the babbage models in the 
provided database. All models are stored in a dedicated table (''models'').

In order to avoid contention, all other resource data is stored in dedicated tables, whose names 
get prefixed by a constant value (current;y 'fdp_')

