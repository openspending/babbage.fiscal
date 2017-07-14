import os
import pytest
import flask
from elasticsearch import Elasticsearch
from babbage_fiscal import config
from babbage_fiscal.api import FDPLoaderBlueprint

@pytest.fixture
def app():
    app = flask.Flask(__name__)
    app.register_blueprint(FDPLoaderBlueprint, url_prefix='/loader')
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = True
    return app


@pytest.fixture
def conn():
    _conn = config.get_engine().connect()
    yield _conn
    _conn.close()


@pytest.fixture
def elasticsearch_address():
    return os.environ.get('OS_ELASTICSEARCH_ADDRESS', 'localhost:9200')


@pytest.fixture
def elasticsearch(elasticsearch_address):
    es = Elasticsearch(hosts=[elasticsearch_address])

    def _delete_indices():
        indices = [
            'packages',
        ]

        for index in indices:
            es.indices.delete(index=index, ignore=[400, 404])

    _delete_indices()
    yield es
    _delete_indices()
