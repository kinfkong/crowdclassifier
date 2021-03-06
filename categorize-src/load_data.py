"""
Copyright (C) 2016 TopCoder Inc., All Rights Reserved.

Load the pre-categorized data to memory

@author TCSCODER
@version 1.0
"""

import json
import logging.config

import pyexcel
import pyexcel.ext.xls

# setup logging
with open('conf/logging.json', 'rt') as fd:
    loggingConfig = json.load(fd)

logging.config.dictConfig(loggingConfig)
logger = logging.getLogger(__name__)

# load configuration
with open('conf/config.json', 'rt') as fd:
    appConfig = json.load(fd)

# the category names for normalization
CATEGORY_NAME_MAPPINGS = {
    'bike lanes and pedestrain paths': 'Bike Lanes and Pedestrian Paths',
    'Bike lanes and pedestrian paths': 'Bike Lanes and Pedestrian Paths',
    'Carpools': 'Carpool',
    'carpools': 'Carpool',
    'Effective traffic calming measure': 'Effective traffic calming measures',
    'ineffective traffic calming measure': 'ineffective traffic calming measures',
    'Incentives to reduce priavte transit': 'incentives to reduce private transit',
    'More bike parking': 'More bike parkings',
    'more bike share locations': 'More bike-share locations',
    'public shttles': 'public shuttles',
    'Real time app to track public transit': 'Real-time app to track public transit',
    'Resident only parking': 'resident-only parking',
    'self driving cars': 'self-driving cars',
    'Shuttles types': 'Shuttle types',
    'students shuttles': 'student shuttles'
}


def normalize_category(category, category_dict):
    """
    Normalize the categories.
    :param category:  the category to normalize
    :param category_dict: the dictionary of categories
    :return: the category that normalized
    """
    if category is None:
        return None

    result = category.strip()
    if not result:
        return None
    result = result.replace('\n', ' ').replace('\r', '')
    result = ' '.join(result.split())
    if result.lower() in category_dict:
        result = category_dict[result.lower()]
    else:
        category_dict[result.lower()] = result

    if result in CATEGORY_NAME_MAPPINGS:
        result = CATEGORY_NAME_MAPPINGS[result]
    return result


def get_column_value(row, column_idx, row_len):
    """
    Get column value from the row array
    :param row: the row to parse
    :param column_idx: the column index
    :param row_len: the row len
    :return: the value
    """

    if column_idx < row_len:
        return row[column_idx]
    else:
        return None


def load_data(data_file):
    """
    Loads the data to memory.
    :param data_file: the data file name.
    :return: the document array
    """

    sheet = pyexcel.get_sheet(file_name=data_file)
    header_row = True
    contents = []

    category_dict = {}
    categories_items = []

    for row in sheet.row:
        if header_row:
            header_row = False
            continue

        row_len = len(row)
        if row_len < 2:
            break

        categories_item = []
        for i in range(2, 7):
            category = normalize_category(get_column_value(row, i, row_len), category_dict)
            categories_item.append(category)

        contents.append(row[1])
        categories_items.append(categories_item)

    return {
        'data': contents,
        'categories': categories_items
    }

