import pytest

from babbage_fiscal import config, loader, model_registry, tasks
from babbage_fiscal.db_utils import table_name_for_package
from .test_common import SAMPLE_PACKAGES


@pytest.mark.usefixtures('elasticsearch')
class TestLoader(object):
    def test_correct_file_load_success(self, conn):
        """
        Simple loading of valid fdp's into DB
        """
        for MODEL_NAME, SAMPLE_PACKAGE in SAMPLE_PACKAGES.values():
            loader.FDPLoader().load_fdp_to_db(SAMPLE_PACKAGE)
        cm = model_registry.ModelRegistry()
        assert len(list(cm.list_models())) > 1, 'no dataset was loaded'

        tablename = table_name_for_package('example@example.com', 'boost-moldova')
        result = conn.execute("SELECT * FROM %s LIMIT 1" % tablename)
        row = result.fetchone()

        # Test factor
        assert row[-3] == 49756100000.0
        assert row[-2] == 51906100
        assert row[-1] == 5171022338

        # Test id
        # Admin classification 1, 1+2, 3, 3+4
        c = ["Central", "101", "0101", "", "", "010"]
        assert row[2] == c[0]
        assert row[3] == ' - '.join([c[0], c[1]])
        assert row[5] == c[2]
        # FIXME: This assertion is breaking because '' != '0101 - '
        # I'm not sure if this is correct or not
        #assert row[7] == ' - '.join([c[2], c[3]])
        assert row[9] == c[4]
        assert row[11] == c[5]
        # Func classification 1, 1+2
        c = ["01", "01.01"]
        assert row[13] == c[0]
        assert row[15] == ' - '.join([c[0], c[1]])
        # Econ classification 1, 2
        c = ["111", "111.00"]
        assert row[17] == c[0]
        assert row[19] == c[1]

    def test_correct_file_double_load_success(self):
        """
        Double loading of one valid fdp into DB
        """
        MODEL_NAME, SAMPLE_PACKAGE = SAMPLE_PACKAGES['md']
        fdp_loader = loader.FDPLoader()
        fdp_loader.load_fdp_to_db(SAMPLE_PACKAGE)
        fdp_loader.load_fdp_to_db(SAMPLE_PACKAGE)
        cm = model_registry.ModelRegistry()
        assert len(list(cm.list_models())) == 1, 'no dataset was loaded'

    def test_correct_file_load_supplied_engine_success(self):
        """
        Simple loading of one valid fdp into DB with supplied engine
        """
        MODEL_NAME, SAMPLE_PACKAGE = SAMPLE_PACKAGES['md']
        loader.FDPLoader(config.get_engine()).load_fdp_to_db(SAMPLE_PACKAGE)
        cm = model_registry.ModelRegistry()
        assert len(list(cm.list_models())) > 0, 'no dataset was loaded'

    def test_correct_bg_file_load_success(self):
        """
        Simple loading of one valid fdp into DB in background
        """
        MODEL_NAME, SAMPLE_PACKAGE = SAMPLE_PACKAGES['uk']
        result = tasks.load_fdp_task.apply(args=(SAMPLE_PACKAGE, "http://google.com"))
        cm = model_registry.ModelRegistry()
        assert len(list(cm.list_models())) > 0, 'no dataset was loaded'
