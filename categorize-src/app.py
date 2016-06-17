#!flask/bin/python
"""
Copyright (C) 2016 TopCoder Inc., All Rights Reserved.

It provides a REST API to categorize the input documents.

@author TCSCODER
@version 1.0
"""

import requests, json, logging, logging.config, os
from flask import Flask, request, jsonify, abort
from sklearn.externals import joblib
from classifier import CrowdClassifier


# setup logging
with open('conf/logging.json', 'rt') as fd:
    loggingConfig = json.load(fd)

logging.config.dictConfig(loggingConfig)
logger = logging.getLogger(__name__)

# load configuration
with open('conf/config.json', 'rt') as fd:
    appConfig = json.load(fd)


# the flask app
app = Flask(__name__)


chile_classifier = CrowdClassifier(1, [1, 1, 0.5, 0.25, 0.25], 'spanish')
chile_classifier.load(os.path.join(appConfig['trained_models_dir'], 'chile'))

palo_alto_classifier = CrowdClassifier(5, [1, 1, 0.5, 0.25, 0.25], 'english')
palo_alto_classifier.load(os.path.join(appConfig['trained_models_dir'], 'palo_alto'))


def get_value(doc, key):
    '''
    Extract the value from the document by key
    Args:
        doc: the document dictionary
        key: the dictionary key
    '''

    value = doc.get(key)
    if value is None:
        return None
    elif len(value) == 0:
        return None
    else:
        return value[0]


def split_category(categories):

    names = ['main_category', 'subcategory1', 'subcategory2', 'subcategory3', 'subcategory4']
    result = {}
    prefixes = ['primary_', 'secondary_']
    for i, category_items in enumerate(categories):
        prefix = prefixes[i]
        for idx, v in enumerate(category_items):
            result[prefix + names[idx]] = v

    return result


@app.route('/api/v1/categorize/<data_type>', methods=['POST'])
def categorize(data_type):
    '''
    The REST API to categorize the input documents
    '''

    data = request.get_json()
    # print(data)

    results = map(lambda x: {'id': x['id'], 'content': x['content']}, data['document'])
    contents = map(lambda x: x['content'], data['document'])

    # predict the contents
    if data_type == 'paloalto':
        predicted = palo_alto_classifier.predict(contents)
    elif data_type == 'chile':
        predicted = chile_classifier.predict(contents)
    else:
        abort(404)

    for i in range(0, len(predicted)):
        results[i].update(split_category(predicted[i]))

    # return the results
    return jsonify({'document': results})


if __name__ == '__main__':
    app.run(host='0.0.0.0')