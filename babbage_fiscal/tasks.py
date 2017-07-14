import logging
import traceback

import sys
from celery import Celery

from .callbacks import STATUS_LOADING_DATA
from .config import get_engine, _set_connection_string
from .loader import FDPLoader
from .callbacks import do_request, STATUS_INITIALIZING, STATUS_FAIL, STATUS_DONE

app = Celery('fdp_loader')
app.config_from_object('babbage_fiscal.celeryconfig')

root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stderr)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


class ProgressSender(object):

    def __init__(self, callback, package):
        self.count = 0
        self.callback = callback
        self.package = package
        self.error = None

    def __call__(self, status=STATUS_LOADING_DATA, count=None, data=None, error=None):
        if error is not None:
            self.error = error
        if count is None:
            count = self.count
        else:
            self.count = count
        logging.info('CALLBACK: %s %s (%s / %s)',
                     '/'.join(self.package.split('/')[4:]),
                     status, count, error)
        do_request(self.callback, self.package, status,
                   progress=count, error=error, data=data)


@app.task
def load_fdp_task(package, callback, connection_string=None):
    send_progress = ProgressSender(callback, package)
    if connection_string is not None:
        _set_connection_string(connection_string)
    try:
        logging.info("Starting to load %s" % package)
        send_progress(status=STATUS_INITIALIZING)
        success = FDPLoader(get_engine()).load_fdp_to_db(package, send_progress)
        logging.info("Finished to load %s" % package)

    except:
        exc = traceback.format_exc()
        send_progress(status=STATUS_FAIL, error=str(exc))
        success = False
        print("Failed to load %s: %s" % (package, exc))

    if not success:
        raise RuntimeError(send_progress.error)
