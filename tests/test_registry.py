import pytest

from babbage.cube import Cube

from babbage_fiscal import config, loader, model_registry
import babbage_fiscal.db_utils
from .test_common import SAMPLE_PACKAGES, NUM_RECORDS

MODEL_NAME, SAMPLE_PACKAGE = SAMPLE_PACKAGES['md']


@pytest.mark.usefixtures('load_sample_package_to_db')
@pytest.mark.usefixtures('elasticsearch')
class TestRegistry(object):
    def test_list_cubes_correct_values(self):
        """
        Simple loading of one valid fdp into DB and testing correct CM values
        """
        cm = model_registry.ModelRegistry()
        models = list(cm.list_models())
        assert len(models) == 1, 'no dataset was loaded'
        assert models[0] == MODEL_NAME, 'dataset with wrong name'

    def test_get_cube_model_correct_values(self):
        cm = model_registry.ModelRegistry()
        model = cm.get_model(MODEL_NAME)
        owner, name = MODEL_NAME.split(':')
        expected = babbage_fiscal.db_utils.model_name(owner, name)

        assert model['fact_table'] == expected, 'bad model'

    def test_get_cube_correct_values(self):
        cm = model_registry.ModelRegistry()
        model = cm.get_model(MODEL_NAME)
        cube = Cube(config.get_engine(), model['fact_table'], model)
        facts = cube.facts(page_size=5)
        assert facts['total_fact_count'] == NUM_RECORDS, 'wrong number of records'

    def test_has_cube_correct_values(self):
        cm = model_registry.ModelRegistry()

        assert cm.has_model(MODEL_NAME)
        assert not cm.has_model(MODEL_NAME+'1')

    def test_no_such_cube(self):
        cm = model_registry.ModelRegistry()
        with pytest.raises(KeyError):
            cm.get_model('bla')

    def test_get_package_correct_values(self):
        cm = model_registry.ModelRegistry()
        package = cm.get_package(MODEL_NAME)

        assert package['owner']+':'+package['name'] == MODEL_NAME, 'wrong model name'

    def test_no_such_package(self):
        cm = model_registry.ModelRegistry()
        with pytest.raises(KeyError):
            cm.get_package('bla')


@pytest.fixture
def load_sample_package_to_db():
    fdp_loader = loader.FDPLoader()
    fdp_loader.load_fdp_to_db(SAMPLE_PACKAGE)
