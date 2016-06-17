import os, json
from classifier import CrowdClassifier
from load_data import load_data


# load configuration
with open('conf/config.json', 'rt') as fd:
    appConfig = json.load(fd)


#import nltk
#nltk.download('all')


chile_data = load_data(appConfig['chile_data_file'])
palo_alto_data = load_data(appConfig['palo_alto_data_file'])

chile_clf = CrowdClassifier(1, [1, 1, 0.5, 0.25, 0.25], 'spanish')
chile_clf = chile_clf.fit(chile_data['data'], chile_data['categories'])
chile_clf.dump(os.path.join(appConfig['trained_models_dir'], 'chile'))


palo_alto_clf = CrowdClassifier(5, [1, 1, 0.5, 0.25, 0.25], 'english')
palo_alto_clf = palo_alto_clf.fit(palo_alto_data['data'], palo_alto_data['categories'])
palo_alto_clf.dump(os.path.join(appConfig['trained_models_dir'], 'palo_alto'))




