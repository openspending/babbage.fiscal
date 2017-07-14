import os

SAMPLE_PACKAGES = {
    'md': (u'example@example.com:boost-moldova', os.path.abspath('tests/sample-data/md/datapackage.json')),
    'uk': (u'officer@data.gov.uk:ukgov-finances-cra', os.path.abspath('tests/sample-data/uk/datapackage.json')),
}
NUM_RECORDS = 2000
