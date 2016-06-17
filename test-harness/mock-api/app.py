#!flask/bin/python
"""
Copyright (C) 2016 TopCoder Inc., All Rights Reserved.

The mock REST API

@author TCSCODER
@version 1.0
"""

import sys, argparse
import pyexcel
import pyexcel.ext.xls
from flask import Flask, request, jsonify

app = Flask(__name__)
responseMap = {}

@app.route('/api/v1/categorize', methods = ['POST'])
def categorize():
    '''
    The mockup categorize REST API. It will fetch the response from the preloaded responseMap. 
    '''
    data = request.get_json()
    results = []

    for doc in data['document']:
        docId = doc.get('id')
        if docId is not None:
            result = responseMap.get(docId)
            if result is not None:
                results.append(result)

    return jsonify({ 'document': results })


def get_column_value(row, columnIdx, rowLen):
    '''
    Get the value of specific column in the row
    Args:
        row: the row array
        columnIdx: the index of the column
        rowLen: the length of the row array
    '''
    if columnIdx < rowLen:
        return row[columnIdx].strip().lower()
    else:
        return None

if __name__ == '__main__':
    # parse cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('dataFile', help='The data file containing the test data to categorize')
    parser.add_argument('--port', type=int, default=5000, help='The listening port number')
    parser.add_argument('--dataType', default='paloalto', help='The endpoint data type')
    args = parser.parse_args(sys.argv[1:])

    if args.dataType != 'chile' and args.dataType != 'paloalto':
        print 'The dataType must be either chile or paloalto'
        sys.exit(1)

    # load data
    sheet = pyexcel.get_sheet(file_name = args.dataFile)
    headerRow = True
    for row in sheet.row:
        # skip header row
        if headerRow:
            headerRow = False
            continue

        rowLen = len(row)
        if rowLen < 2:
            break

        record = {}
        record['id'] = '%d' % row[0]
        record['content'] = row[1]
        record['primary_main_category'] = get_column_value(row, 2, rowLen)

        if args.dataType == 'paloalto':
            record['primary_subcategory1'] = get_column_value(row, 3, rowLen)
            record['primary_subcategory2'] = get_column_value(row, 4, rowLen)
            record['primary_subcategory3'] = get_column_value(row, 5, rowLen)
            record['primary_subcategory4'] = get_column_value(row, 6, rowLen)

        record['secondary_main_category'] = get_column_value(row, 7, rowLen)

        if args.dataType == 'paloalto':
            record['secondary_subcategory1'] = get_column_value(row, 8, rowLen)
            record['secondary_subcategory2'] = get_column_value(row, 9, rowLen)
            record['secondary_subcategory3'] = get_column_value(row, 10, rowLen)
            record['secondary_subcategory4'] = get_column_value(row, 11, rowLen)

        responseMap[record['id']] = record

    # run server
    app.run(host='0.0.0.0', port=args.port)