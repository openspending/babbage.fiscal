import os

import pytest
from click.testing import CliRunner

from sqlalchemy.engine.reflection import Inspector

from babbage_fiscal.cli import cli
from babbage_fiscal import model_registry, config

from .test_common import SAMPLE_PACKAGES

MODEL_NAME, SAMPLE_PACKAGE = SAMPLE_PACKAGES['md']


class TestCLI(object):
    def test_load_fdp_cmd_success(self, cli_runner, elasticsearch_address):
        """
        Simple invocation of the load-fdp command
        """
        cli_runner.invoke(cli,
                          args=['load-fdp', '--package', SAMPLE_PACKAGE],
                          env={'OS_ELASTICSEARCH_ADDRESS': elasticsearch_address})
        cm = model_registry.ModelRegistry()

        assert len(list(cm.list_models())) > 0, 'no dataset was loaded'

    def test_create_tables_cmd_success(self, cli_runner, elasticsearch_address):
        """
        Simple invocation of the create-tables command
        """
        cli_runner.invoke(cli,
                          args=['create-tables'],
                          env={'OS_ELASTICSEARCH_ADDRESS': elasticsearch_address})
        engine = config.get_engine()
        inspector = Inspector.from_engine(engine)
        assert 'models' not in inspector.get_table_names()


@pytest.fixture(scope='module')
def cli_runner():
    return CliRunner()
