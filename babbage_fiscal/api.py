import logging

from flask import Blueprint, request, abort
from .tasks import load_fdp_task
from .config import get_connection_string, _set_connection_string

FDPLoaderBlueprint = Blueprint('FDPLoader', __name__)


@FDPLoaderBlueprint.route('/')
def load():
    package = request.args.get('package')
    callback = request.args.get('callback')
    logging.info('Requested load of "%s" with callback "%s"\n' % (package, callback))
    if package is not None and callback is not None:
        load_fdp_task.delay(package, callback, get_connection_string())
        return ""
    else:
        abort(400)


def configure_loader_api(connection_string = None):
    if connection_string is not None:
        _set_connection_string(connection_string)
    return FDPLoaderBlueprint
