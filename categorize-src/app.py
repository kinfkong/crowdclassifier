#!flask/bin/python
"""
Copyright (C) 2016 TopCoder Inc., All Rights Reserved.

It provides a REST API to categorize the input documents.

@author TCSCODER
@version 1.0
"""

import json, logging.config, os
from flask import Flask, request, jsonify, abort
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

# load the classifiers
chile_classifier = CrowdClassifier(1, [1, 1, 0.5, 0.25, 0.25], 'spanish', 'log')
chile_classifier.load(os.path.join(appConfig['trained_models_dir'], 'chile'))

palo_alto_classifier = CrowdClassifier(5, [1, 1, 0.5, 0.25, 0.25], 'english', 'modified_huber')
palo_alto_classifier.load(os.path.join(appConfig['trained_models_dir'], 'palo_alto'))


def get_value(doc, key):
    """
    Extract the value from the document by key
    :param doc: the document dictionary
    :param key: the dictionary key
    :return:
    """

    value = doc.get(key)
    if value is None:
        return None
    elif len(value) == 0:
        return None
    else:
        return value[0]


def show_category(categories):
    """
    Converts the category names from array to readable name.
    :param categories: the category arrays
    :return: the category label
    """
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
    """
    The REST API to categorize the input documents
    :param data_type: paloalto or chile
    :return: categories of the documents
    """

    data = request.get_json()

    results = map(lambda x: {'id': x['id'], 'content': x['content']}, data['document'])
    contents = map(lambda x: x['content'], data['document'])

    # predict the contents
    predicted = None
    if data_type == 'paloalto':
        predicted = palo_alto_classifier.predict(contents)
    elif data_type == 'chile':
        predicted = chile_classifier.predict(contents)
    else:
        abort(404)

    for i in range(0, len(predicted)):
        results[i].update(show_category(predicted[i]))

    # return the results
    return jsonify({'document': results})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
