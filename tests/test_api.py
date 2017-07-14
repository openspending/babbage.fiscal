try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
import threading

from flask import url_for
import requests_mock
import pytest

from babbage_fiscal.callbacks import STATUS_DONE, STATUS_FAIL
from .test_common import SAMPLE_PACKAGES

MODEL_NAME, SAMPLE_PACKAGE = SAMPLE_PACKAGES['md']


@pytest.mark.usefixtures('elasticsearch')
class TestAPI(object):
    def test_load_package_success(self, client, wait_for_success):
        url = url_for('FDPLoader.load', package=SAMPLE_PACKAGE, callback=wait_for_success)
        res = client.get(url)
        assert res.status_code == 200

    def test_load_package_bad_parameters(self, client):
        url = url_for('FDPLoader.load', packadge=SAMPLE_PACKAGE, callback='http://example.org/callback')
        res = client.get(url)
        assert res.status_code == 400


@pytest.fixture
def wait_for_success(client):
    '''Returns callback URL and waits for it to receive a POST with status=STATUS_DONE.
    '''
    url = 'http://example.org/callback'
    timeout = 2
    status_done_event = threading.Event()

    def _status_code_callback(request, context):
        '''We use this only as a way to check the "status".'''
        params = urlparse.parse_qs(request.body)
        status = params.get('status', [])
        if STATUS_DONE in status:
            status_done_event.set()

    with requests_mock.Mocker() as m:
        m.post(url, text=_status_code_callback)
        yield url

    status_done_event.wait(timeout)
    assert status_done_event.is_set(), 'Did not receive the "STATUS_DONE" message'
