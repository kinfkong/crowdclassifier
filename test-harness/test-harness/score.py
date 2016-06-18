"""
Copyright (C) 2016 TopCoder Inc., All Rights Reserved.

It will score the user submissions with the input data.

@author TCSCODER
@version 1.0
"""

import sys, argparse, csv, json, re
import logging, logging.config
import pyexcel
import pyexcel.ext.xls
import requests
import concurrent.futures
from recordtype import recordtype

# user submission record type
Submission = recordtype('Submission', [
    'submissionId', 'dataType', 'single', 'endpoint', ('score', 0), 
    ('overallAccuracy', 0), ('mainCategoryAccuracy', 0), 
    ('subCategory1Accuracy', 0), ('subCategory2Accuracy', 0), 
    ('subCategory3Accuracy', 0), ('subCategory4Accuracy', 0)
])


# setup logging
with open('conf/logging.json', 'rt') as fd:
    loggingConfig = json.load(fd)

logging.config.dictConfig(loggingConfig)


def get_column_value(row, columnIdx, rowLen):
    '''
    Get the value of specific column in the row
    Args:
        row: the array containing the row data
        columnIdx: the index of the column
        rowLen: the length of the row
    Returns:
        the value in the row
    '''
    if columnIdx < rowLen:
        return row[columnIdx]
    else:
        return None

def normalize_value(value):
    '''
    Normalize the value by removing all whitespaces and lower the case.
    Args:
        value: the value to normalize
    Returns:
        the normalized vlaue
    '''
    if value is None:
        return None
    result = value.lower()
    # fix typo
    typo_words = {
        'pedestrain': 'pedestrian',
        'pedestrian': 'pedestrian',
        'shttles': 'shuttles',
        'shttle': 'shuttle',
        'priavte': 'private'
    }
    for typo, word in typo_words.iteritems():
        result = re.sub(r'\b%s\b' % typo, word, result)
    result = re.sub(r's\s+', '', result)
    result = re.sub(r's$', '', result)
    result = re.sub(r'\s+', '', result)
    result = result.replace('\n', '').replace('\r', '')
    result = re.sub(r'[^a-zA-Z0-9]', '', result)
    result = result.replace('-', '')
    if not result:
        return None
    return result


def is_value_equal(expectedValue, userValue):
    '''
    Check the two given values are equal or not.
    Args:
        expectedValue: the expected string value
        userValue: the user value to check
    Returns:
        True if they are equal case insensitively (with whitespaces stripped as well), False otherwise
    '''
    if expectedValue is None:
        expectedValue = ""

    if userValue is None:
        userValue = ""

    if not isinstance(userValue, basestring):
        return False
    else:
        return normalize_value(expectedValue) == normalize_value(userValue)

def calculate_scores(submission, expectedDoc, categorizedDoc):
    '''
    Calculate the scores by comparing the categorized document from user and the expected document
    Args:
        submission: the user submission data
        expectedDoc: the expected document
        categorizedDoc: the categorized document from user
    '''
    primaryMainCategoryEqual = is_value_equal(expectedDoc.get('main_category'), categorizedDoc.get('primary_main_category'))
    secondaryMainCategoryEqual = is_value_equal(expectedDoc.get('main_category'), categorizedDoc.get('secondary_main_category'))

    if not submission.single:
        primarySubCategory1Equal = is_value_equal(expectedDoc.get('subcategory1'), categorizedDoc.get('primary_subcategory1'))
        primarySubCategory2Equal = is_value_equal(expectedDoc.get('subcategory2'), categorizedDoc.get('primary_subcategory2'))
        primarySubCategory3Equal = is_value_equal(expectedDoc.get('subcategory3'), categorizedDoc.get('primary_subcategory3'))
        primarySubCategory4Equal = is_value_equal(expectedDoc.get('subcategory4'), categorizedDoc.get('primary_subcategory4'))
        
        secondarySubCategory1Equal = is_value_equal(expectedDoc.get('subcategory1'), categorizedDoc.get('secondary_subcategory1'))
        secondarySubCategory2Equal = is_value_equal(expectedDoc.get('subcategory2'), categorizedDoc.get('secondary_subcategory2'))
        secondarySubCategory3Equal = is_value_equal(expectedDoc.get('subcategory3'), categorizedDoc.get('secondary_subcategory3'))
        secondarySubCategory4Equal = is_value_equal(expectedDoc.get('subcategory4'), categorizedDoc.get('secondary_subcategory4'))

    score = 0.0
    if primaryMainCategoryEqual:  
        score += 1.0

    if not primaryMainCategoryEqual and secondaryMainCategoryEqual:
        score += 0.5

    if not submission.single:
        if primarySubCategory1Equal:
            score += 1.0
        if primarySubCategory2Equal:
            score += 0.5
        if primarySubCategory3Equal: 
            score += 0.25
        if primarySubCategory4Equal:
            score += 0.25
        
        if not primarySubCategory1Equal and secondarySubCategory1Equal:
            score += 0.5
        if not primarySubCategory2Equal and secondarySubCategory2Equal:
            score += 0.25
        if not primarySubCategory3Equal and secondarySubCategory3Equal:
            score += 0.125
        if not primarySubCategory4Equal and secondarySubCategory4Equal:
            score += 0.125

    submission.score += score
    submission.mainCategoryAccuracy += int(primaryMainCategoryEqual)
    submission.overallAccuracy += int(primaryMainCategoryEqual)

    if not submission.single:
        submission.subCategory1Accuracy += int(primarySubCategory1Equal)
        submission.overallAccuracy += int(primarySubCategory1Equal)

        submission.subCategory2Accuracy += int(primarySubCategory2Equal)
        submission.overallAccuracy += int(primarySubCategory2Equal)

        submission.subCategory3Accuracy += int(primarySubCategory3Equal)
        submission.overallAccuracy += int(primarySubCategory3Equal)

        submission.subCategory4Accuracy += int(primarySubCategory4Equal)
        submission.overallAccuracy += int(primarySubCategory4Equal)
    

def process_with_batch_data(submission, postedDocBatch, expectedDocBatch, batchNo, totalBatches, requestTimeout, logger):
    '''
    Send one batch of documents to the submission api endpoint, and verify the results. 
    Args:
        submission: the submission data
        postedDocBatch: a batch of documents to post
        expectedDocBatch: the expected results
        batchNo: the batch number
        totalBatches: the total number of batches
        requestTimeout: the timeout to to receive response from submission's REST api endpoint
        logger: the logger
    '''
    payload = { 'document':  postedDocBatch }

    # post to submission's api endpoint
    endpoint = submission.endpoint
    logger.info('Start to send batch %s/%s data request to %s', batchNo, totalBatches, endpoint)    
    try:
        response = requests.post(endpoint, json=payload, timeout=requestTimeout)

        logger.debug('The response status code for batch %s/%s request is: %s', batchNo, totalBatches, response.status_code)
        logger.debug('The response data for batch %s/%s request is as below:\n%s', batchNo, totalBatches, response.text)
        if response.status_code != requests.codes.ok:
            logger.error('The status code for batch %s/%s request is not 200 from %s', batchNo, totalBatches, endpoint)
            return

        result = response.json()
    except Exception:
        logger.exception('Fail to get response for batch %s/%s request from %s', batchNo, totalBatches, endpoint)
        return


    # validate the json response
    invalidResponseError = 'The returned response is invalid for batch %s/%s request from %s'
    if result.get('document') == None:
        logger.error(invalidResponseError, batchNo, totalBatches, endpoint)
        return

    categorizedDocs = result['document']
    if isinstance(categorizedDocs, list) == False:
        logger.error(invalidResponseError, batchNo, totalBatches, endpoint)
        return

    # convert the result to a dictionary
    categorizedDocMap = {}
    for doc in categorizedDocs:
        docId = doc.get('id')
        if docId is not None:
            categorizedDocMap[docId] = doc

    # calculate the scores
    for expectedDoc in expectedDocBatch:
        docId = expectedDoc.get('id')

        categorizedDoc = categorizedDocMap.get(docId)
        if categorizedDoc is not None:
            calculate_scores(submission, expectedDoc, categorizedDoc)


def calculate_accuracy(value, total):
    '''
    Calculate the accuracy.
    Args:
        value: the accuracy value
        total: the total value
    Returns:
        the accuracy result in percentage
    '''
    numberFormat = '%.2f%%'
    return numberFormat % (round(value * 100.0 / total, 2))



def process_submission(submission, postedDocBatches, expectedDocBatches, totalDocuments, totalBatches, requestTimeout):
    '''
    Process the submission to calculate the scores. 
    Args:
        submission: the submission data
        postedDocBatches: an array of document batch to send to submission api endpoint
        expectedDocBatches: an array of expected responses
        totalDocuments: the total number of documents
        totalBatches: the total number of batches
        requestTimeout: the timeout to to receive response from submission's REST api endpoint
    '''
    logger = logging.getLogger('submission-' + submission.submissionId)

    # calculate scores
    for idx, postedDocBatch in enumerate(postedDocBatches):
        process_with_batch_data(submission, postedDocBatch, expectedDocBatches[idx], idx + 1, totalBatches, requestTimeout, logger)

    # calculate actual accuracy
    submission.mainCategoryAccuracy = calculate_accuracy(submission.mainCategoryAccuracy, totalDocuments)
    submission.subCategory1Accuracy = calculate_accuracy(submission.subCategory1Accuracy, totalDocuments)
    submission.subCategory2Accuracy = calculate_accuracy(submission.subCategory2Accuracy, totalDocuments)
    submission.subCategory3Accuracy = calculate_accuracy(submission.subCategory3Accuracy, totalDocuments)
    submission.subCategory4Accuracy = calculate_accuracy(submission.subCategory4Accuracy, totalDocuments)    

    if not submission.single:        
        submission.overallAccuracy = calculate_accuracy(submission.overallAccuracy, totalDocuments * 5)
    else:
        submission.overallAccuracy = submission.mainCategoryAccuracy        
    
    logger.info('The processing of the submission is completed successfully.')    
    

def main(argv):
    '''
    The entry point. It will parse the input data spreadsheet file and submission csv file, 
    and send the data documents to each submission in batch. 
    Args:
        argv: the input arguments
    '''
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('dataFile', help='The data file containing the test data to categorize')
    parser.add_argument('submissionsFile', help='The submissions csv file')
    parser.add_argument('--timeout', type=int, default=60, help='The timeout to receive response from submission''s REST api endpoint')
    parser.add_argument('--threads', type=int, default=5, help='The number of threads to process submissions')
    args = parser.parse_args(argv)

    requestTimeout = args.timeout
    maxWorkers = args.threads

    logger = logging.getLogger('main')
    
    # read submission csv
    logger.info('Load submissions csv data.')
    submissions = []
    headerRow = True
    with open(args.submissionsFile, 'rb') as fd:
        csvReader = csv.reader(fd)
        for row in csvReader:
            # skip header row
            if headerRow:
                headerRow = False
                continue

            if len(row) < 3:
                break

            if row[1] == 'chile':
                single = True
            elif row[1] == 'paloalto':
                single = False
            else:
                print 'The dataType must be either paloalto or chile in submissions csv file'
                sys.exit(1)

            sub = Submission(row[0], row[1], single, row[2])
            submissions.append(sub)

    # read spreadsheet data
    logger.info('Load spreadsheet data.')

    batchSize = 10

    # data to be posted to the submission api
    postedDocBatches = []
    postedDocs = []

    # data to compare with the responses from the submission api
    expectedDocBatches = []
    expectedDocs = []

    totalDocuments = 0

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

        postedDoc = {
            'id': '%d' % row[0],
            'content': row[1]
        }

        expectedDoc = {
            'id': '%d' % row[0],
            'content': row[1],
            'main_category': get_column_value(row, 2, rowLen),
            'subcategory1': get_column_value(row, 3, rowLen),
            'subcategory2': get_column_value(row, 4, rowLen),
            'subcategory3': get_column_value(row, 5, rowLen),
            'subcategory4': get_column_value(row, 6, rowLen)
        }

        postedDocs.append(postedDoc)
        expectedDocs.append(expectedDoc)

        if len(postedDocs) == batchSize:
            expectedDocBatches.append(expectedDocs)
            postedDocBatches.append(postedDocs)
            postedDocs = []
            expectedDocs = []
            totalDocuments += batchSize

    # add last batch
    if len(postedDocs) > 0:
        expectedDocBatches.append(expectedDocs)
        postedDocBatches.append(postedDocs)
        totalDocuments += len(postedDocs)

    totalBatches = len(postedDocBatches);
    logger.info('There are %s batch(es) of documents to send to the api endpoint of each submission.', totalBatches)
    for idx, postedDocBatch in enumerate(postedDocBatches):
        logger.debug('The request data for batch %s/%s is:\n%s', idx + 1, totalBatches, json.dumps({ 'document':  postedDocBatch }, indent=4))

    # process submissions with multiple threads
    logger.info('Start to process submissions.')
    futures = []
    submissionCount = len(submissions)
    with concurrent.futures.ThreadPoolExecutor(max_workers=maxWorkers) as executor:
        for sub in submissions:
            future = executor.submit(process_submission, sub, postedDocBatches, expectedDocBatches, totalDocuments, totalBatches, requestTimeout)
            futures.append(future)

        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed = completed + 1
            logger.info('%s of %s submission(s) have been processed.', completed, submissionCount)


    # write result to csv file
    logger.info('Write the results to submission csv file')

    csvHeader = [
        'submission id', 'dataType', 'endpoint', 'score', 'overall accuracy', 'main category accuracy',
        'subcategory 1 accuracy', 'subcategory 2 accuracy', 'subcategory 3 accuracy',
        'subcategory 4 accuracy'
    ]
    with open(args.submissionsFile, 'wb') as fd:
        csvWriter = csv.writer(fd)

        # write header
        csvWriter.writerow(csvHeader)

        # write processed submission data
        for sub in submissions:
            row = [
                sub.submissionId, sub.dataType, sub.endpoint, sub.score, sub.overallAccuracy,
                sub.mainCategoryAccuracy, sub.subCategory1Accuracy,sub.subCategory2Accuracy,
                sub.subCategory3Accuracy, sub.subCategory4Accuracy
            ]
            csvWriter.writerow(row)


if __name__ == '__main__':
   main(sys.argv[1:])