import email.utils
import traceback
import hashlib
import logging
import json
import requests

from datapackage import DataPackage
from jsontableschema_sql import Storage
from os_api_cache import get_os_cache

from .callbacks import *
from .model_registry import ModelRegistry
from .config import get_engine
from .fdp_utils import fdp_to_model
from .db_utils import database_name, table_name_for_package
from .row_processor import RowProcessor


def noop(*args, **kw):
    pass


class FDPLoader(object):
    """
    Utility class for loading FDPs to the DB
    """

    def __init__(self, engine=None):
        if engine is None:
            self.engine = get_engine()
        else:
            self.engine = engine
        self.package = None
        self.model = None
        self.model_name = None
        self.dpo = None
        self.datapackage_name = None
        self.fullname = None
        self.registry = ModelRegistry()
        self.last_package_descriptor = None
        self.last_loading_success = None
        self.callback = noop

    def check_hashes(self, resource):
        logging.info('Checking hashes of currently loaded data')

        current_schema_hash = self.last_package_descriptor\
                                .get('resources', ({},))[0]\
                                .get('_schema_hash')
        logging.info('Loaded resource descriptor hash is %s', current_schema_hash)

        new_schema_hash = dict((k, v)
                               for k, v in resource.descriptor.items()
                               if not k.startswith('_'))
        new_schema_hash['_model'] = self.dpo.descriptor.get('model', {})
        new_schema_hash = json.dumps(new_schema_hash, sort_keys=True, ensure_ascii=True)
        new_schema_hash = new_schema_hash.encode('ascii')
        new_schema_hash = hashlib.md5(new_schema_hash).hexdigest()
        logging.info('Loading resource descriptor hash is %s', new_schema_hash)

        current_data_hash = self.last_package_descriptor \
            .get('resources', ({},))[0] \
            .get('_data_hash')
        logging.info('Loaded resource data hash is %s', current_data_hash)

        new_data_hash = None
        remote_url = resource.remote_data_path
        if remote_url:
            response = requests.head(remote_url)
            new_data_hash = response.headers.get('etag')
        logging.info('Loading resource data hash is %s', new_data_hash)

        resource.descriptor['_schema_hash'] = new_schema_hash
        resource.descriptor['_data_hash'] = new_data_hash

        ret = (current_schema_hash != new_schema_hash) or\
              (current_data_hash != new_data_hash) or\
              (not self.last_loading_success)

        if ret:
            logging.info('Looks like stuff changed, loading data')
        else:
            logging.info('Looks like nothing major changed, skipping data load')

        return ret

    def status_update(self, **kwargs):
        if self.model_name is not None:
            try:
                _name, _, _package, _model, _dataset, \
                _author, _loading_status, _loaded = \
                    self.registry.get_raw(self.model_name)
                if self.last_package_descriptor is None:
                    self.last_package_descriptor = _package
                if self.last_loading_success is None:
                    self.last_loading_success = _loading_status == STATUS_DONE
            except KeyError:
                _name = self.model_name
                _package = {}
                _model = {}
                _dataset = ''
                _author = ''
                _loading_status = None
                _loaded = False
                self.last_package_descriptor = {}
                self.last_loading_success = False

            if self.model is not None:
                _model = self.model
            if self.dpo is not None:
                _package = self.dpo.descriptor
            if self.datapackage_name is not None:
                _dataset = self.datapackage_name
            if self.fullname is not None:
                _author = self.fullname
            status = kwargs.get('status')
            if status is not None:
                _loading_status = status
                _loaded = status == STATUS_DONE
            self.registry.save_model(_name, self.package, _package,
                                     _model, _dataset, _author,
                                     _loading_status, _loaded)
        self.callback(**kwargs)

    def load_fdp_to_db(self, package, callback=noop):
        """
        Load an FDP to the database, create a babbage model and save it as well
        :param package: URL for the datapackage.json
        :param callback: callback to use to send progress updates
        """

        self.callback = callback
        self.package = package

        # Load and validate the datapackage
        self.status_update(status=STATUS_LOADING_DATAPACKAGE)
        self.dpo = DataPackage(package, schema='fiscal')
        self.status_update(status=STATUS_VALIDATING_DATAPACKAGE)
        self.dpo.validate()
        self.status_update(status=STATUS_LOADING_RESOURCE)
        resource = self.dpo.resources[0]
        schema = resource.descriptor['schema']

        # Use the cube manager to get the table name
        self.datapackage_name = self.dpo.descriptor['name']
        datapackage_owner = self.dpo.descriptor['owner']
        datapackage_author = self.dpo.descriptor['author']

        # Get the full name from the author field, and rewrite it without the email
        self.fullname, email_addr = email.utils.parseaddr(datapackage_author)
        email_addr = email_addr.split('@')[0] + '@not.shown'
        self.dpo.descriptor['author'] = '{0} <{1}>'.format(self.fullname, email_addr)
        self.dpo.descriptor.setdefault('private', True)

        self.model_name = "{0}:{1}".format(datapackage_owner, self.datapackage_name)
        table_name = table_name_for_package(datapackage_owner, self.datapackage_name)

        try:
            all_fields = set()
            field_translation = {}
            # Process schema - slugify field names
            for field in schema['fields']:
                name = database_name(field['name'], all_fields)
                all_fields.add(name)
                translated_field = {
                    'name': name,
                    'type': field['type']
                }
                field_translation[field['name']] = translated_field

            storage_schema = {
                'fields': [
                    {
                        'type': f['type'],
                        'name': field_translation[f['name']]['name'],
                        'format': f.get('format', 'default')
                    }
                    for f in schema['fields']
                    ],
                # Babbage likes just one primary key
                'primaryKey': '_id'
            }

            # Add Primary key to schema
            storage_schema['fields'].insert(0, {
                'name': '_id',
                'type': 'integer'
            })

            # Create Babbage Model
            self.status_update(status=STATUS_CREATING_BABBAGE_MODEL)
            self.model = fdp_to_model(self.dpo, table_name, resource, field_translation)

            if self.check_hashes(resource):
                # Create indexes
                indexes = set()
                primary_keys = schema.get('primaryKey', [])
                for dim in self.dpo.descriptor.get('model', {}).get('dimensions',{}).values():
                    attributes = dim.get('attributes', {})
                    for attribute in attributes.values():
                        source = attribute.get('source')
                        if source in primary_keys:
                            indexes.add((field_translation[source]['name'],))
                        labelfor = attribute.get('labelfor')
                        if labelfor is not None:
                            labelfor = attributes.get(labelfor, {})
                            labelfor_source = labelfor.get('source')
                            if labelfor_source in primary_keys:
                                indexes.add((field_translation[labelfor_source]['name'],
                                             field_translation[source]['name'],))
                indexes = list(indexes)
                logging.error('INDEXES: %r', indexes)
                #
                # if dim['label'] in primary_keys:
                #     key_field = dim['attributes'][dim['key_attribute']]['label']
                #     key_field = field_translation[key_field]['name']
                #     indexes.append((key_field,))
                #
                #     label_field = dim['attributes'].get(dim.get('label_attribute'), {}).get('label')
                #     if label_field is not None:
                #         label_field = field_translation[label_field]['name']
                #         if label_field != key_field:
                #             indexes.append((key_field, label_field))

                # Load 1st resource data into DB
                # We use the prefix name so that JTS-SQL doesn't load all table data into memory
                storage = Storage(self.engine, prefix=table_name)
                faux_table_name = ''
                if faux_table_name in storage.buckets:
                    self.status_update(status=STATUS_DELETING_TABLE)
                    storage.delete(faux_table_name)
                self.status_update(status=STATUS_CREATING_TABLE)
                indexes_fields = None
                if indexes:
                    indexes_fields = [indexes]
                storage.create(faux_table_name, storage_schema, indexes_fields=indexes_fields)

                self.status_update(status=STATUS_LOADING_DATA_READY)
                row_processor = RowProcessor(resource.iter(), self.status_update,
                                             schema, self.dpo.descriptor)
                storage.write(faux_table_name, row_processor.iter())

                cache = get_os_cache()
                if cache is not None:
                    logging.info('Clearing cache for context=%s', self.model_name)
                    cache.clear(self.model_name)

            response = {
                'model_name': self.model_name,
                'babbage_model': self.model,
                'package': self.dpo.descriptor
            }
            self.status_update(status=STATUS_DONE, data=response)

        except Exception as e:
            logging.exception('LOADING FAILED')
            self.status_update(status=STATUS_FAIL, error=traceback.format_exc())
            return False

        return True
