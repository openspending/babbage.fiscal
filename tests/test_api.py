from threading import Semaphore, Thread
import os

from http.server import HTTPServer, BaseHTTPRequestHandler

from flask import Flask, url_for
from flask.ext.testing import TestCase as FlaskTestCase

from babbage_fiscal import config
from babbage_fiscal.api import FDPLoaderBlueprint
from test_common import SAMPLE_PACKAGES

cv = Semaphore(0)

MODEL_NAME, SAMPLE_PACKAGE = SAMPLE_PACKAGES['md']

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200,'OK')
        try:
            cv.release()
            return "OK"
        except Exception, e:
            print e


class MyHTTPServer(Thread):

    def __init__(self):
        super(MyHTTPServer, self).__init__()
        self.server = HTTPServer(("localhost",7878), MyHandler)

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

class TestAPI(FlaskTestCase):

    def create_app(self):
        config._set_connection_string('sqlite:///test.db')
        app = Flask('test')
        app.register_blueprint(FDPLoaderBlueprint, url_prefix='/loader')
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = True
        return app

    def setUp(self):
        super(TestAPI, self).setUp()

    def tearDown(self):
        if os.path.exists('test.db'):
            os.unlink('test.db')

    def test_load_package_success(self):
        th = MyHTTPServer()
        th.start()
        res = self.client.get(url_for('FDPLoader.load',package=SAMPLE_PACKAGE, callback='http://localhost:7878/callback'))
        self.assertEquals(res.status_code, 200, "Bad status code %r" % res.status_code)
        cv.acquire()
        th.stop()

    def test_load_package_bad_parameters(self):
        res = self.client.get(url_for('FDPLoader.load',packadge=SAMPLE_PACKAGE, callback='http://localhost:7878/callback'))
        self.assertEquals(res.status_code, 400, "Bad status code %r" % res.status_code)



