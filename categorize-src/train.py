"""
Copyright (C) 2016 TopCoder Inc., All Rights Reserved.

It trains the text documents.

@author TCSCODER
@version 1.0
"""


import argparse
import json
import os
import sys

from classifier import CrowdClassifier
from load_data import load_data

# load configuration
with open('conf/config.json', 'rt') as fd:
    appConfig = json.load(fd)


def main():
    """
    The main process
    """
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('dataType', help='The data type, "paloalto" or "chile"')
    parser.add_argument('dataFile', help='The data file to train')
    args = parser.parse_args(sys.argv[1:])

    # check file existence
    if not os.path.isfile(args.dataFile):
        print('The file does not exists: ' + args.dataFile)
        sys.exit(-1)

    if args.dataType == 'paloalto':
        palo_alto_data = load_data(args.dataFile)
        palo_alto_clf = CrowdClassifier(5, [1, 1, 0.5, 0.25, 0.25], 'english', 'modified_huber')
        palo_alto_clf = palo_alto_clf.fit(palo_alto_data['data'], palo_alto_data['categories'])
        palo_alto_clf.dump(os.path.join(appConfig['trained_models_dir'], 'palo_alto'))
    elif args.dataType == 'chile':
        chile_data = load_data(args.dataFile)
        chile_clf = CrowdClassifier(1, [1, 1, 0.5, 0.25, 0.25], 'spanish', 'log')
        chile_clf = chile_clf.fit(chile_data['data'], chile_data['categories'])
        chile_clf.dump(os.path.join(appConfig['trained_models_dir'], 'chile'))
    else:
        print('dataType can only be paloalto or chile')
        sys.exit(-1)


if __name__ == '__main__':
    main()
