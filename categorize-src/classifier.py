"""
Copyright (C) 2016 TopCoder Inc., All Rights Reserved.

Classifiers the text documents. It provides method to train(fit) or predict.

@author TCSCODER
@version 1.0
"""

import json
import nltk
import string

from nltk import word_tokenize
from nltk.stem.snowball import SnowballStemmer
from sklearn.externals import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

# load configuration
with open('conf/config.json', 'rt') as fd:
    appConfig = json.load(fd)

# set the nltk data path if necessary
if appConfig['nltk_data_path']:
    nltk.data.path.append(appConfig['nltk_data_path'])


# create the stemmers
stemmers = dict()
stemmers['english'] = SnowballStemmer('english', ignore_stopwords=True)
stemmers['spanish'] = SnowballStemmer('spanish', ignore_stopwords=True)

punctuations = list(string.punctuation)


def stem_tokens(tokens, stemmer):
    """
    stem the tokens
    :param tokens: the tokens to stem
    :param stemmer: the stemmer
    :return: the stemmed tokens
    """
    stemmed = []
    for item in tokens:
        stemmed.append(stemmer.stem(item))
    return stemmed


def english_tokenize(text):
    """
    the text to tokenize for english.
    :param text: the text
    :return: the tokens array
    """
    tokens = word_tokenize(text, 'english')
    stems = stem_tokens(tokens, stemmers['english'])
    stems = [i for i in stems if i not in punctuations]
    return stems


def spanish_tokenize(text):
    """
    the text to tokenize for spanish.
    :param text: the text
    :return: the tokens array
    """
    tokens = word_tokenize(text, 'spanish')
    stems = stem_tokens(tokens, stemmers['spanish'])
    stems = [i for i in stems if i not in punctuations]
    return stems


class CrowdClassifier:
    """
    The classifier for text classification.
    """

    def __init__(self, category_level, level_scores, language, loss):
        """
        Initialize the classifier
        :param category_level: the category level, 1 for chile, and 5 for palo alto
        :param level_scores: the scores
        :param language: the language, english or spanish
        :param loss: the SVM loss parameter
        """
        self.classifiers = []
        self.category_level = 0
        self.level_scores = []
        for i in range(0, category_level):
            tokenize = english_tokenize
            if language == 'spanish':
                tokenize = spanish_tokenize

            internal_classifier = SGDClassifier(loss=loss, penalty='l2', alpha=0.0001, n_iter=10, random_state=42)

            clf = Pipeline([('vect', CountVectorizer(ngram_range=(1, 1), tokenizer=tokenize)),
                                 ('tfidf', TfidfTransformer(use_idf=True)),
                                 ('clf', internal_classifier),
                                 ])

            self.classifiers.append(clf)

        self.category_level = category_level
        self.level_scores = level_scores

    def fit(self, contents, categories):
        """
        Fit the contents to the categories. This is the trainning method.
        :param contents: the contents.
        :param categories: the categories
        :return: the classifier.
        """
        for i in range(0, self.category_level):
            level_categories = []
            level_contents = []
            for idx, content in enumerate(contents):
                category_label = self._get_category_label(categories[idx], i)
                level_categories.append(category_label)
                level_contents.append(content)
            # train the level classifier
            self.classifiers[i].fit(level_contents, level_categories)
        return self

    def dump(self, filename):
        """
        Persist the classifiers.
        :param filename: the filename to save the classifiers.
        """
        for idx, clf in enumerate(self.classifiers):
            joblib.dump(clf, filename + '.level_%d' % (idx + 1))

    def load(self, filename):
        """
        Loads the classifiers from file.
        :param filename: the filename.
        """
        self.classifiers = []
        for i in range(0, self.category_level):
            clf = joblib.load(filename + '.level_%d' % (i + 1))
            self.classifiers.append(clf)

    def predict(self, contents):
        """
        Predicts the contents.
        :param contents: the contents to predict.
        :return: the predicted result (categories)
        """
        result = []
        probabilities = {}
        for idx, clf in enumerate(self.classifiers):
            predicts = clf.predict_proba(contents)
            for i in range(0, len(contents)):
                if i not in probabilities:
                    probabilities[i] = {}
                for idx2, class_label in enumerate(clf.classes_):
                    probabilities[i][class_label] = predicts[i][idx2]

        for i in range(0, len(contents)):
            result.append(self._predict(probabilities[i]))
        return result

    def _predict(self, probabilities):
        """
        This is the helper method for predict a single content.
        :param probabilities: the probabilities of each classifier.
        :return: the predicted result
        """
        child_categories = []
        for i in range(0, self.category_level):
            child_categories.append({})
            for category_label in self.classifiers[i].classes_:
                main_category = self._get_categories(category_label)[0]
                if main_category not in child_categories[i]:
                    child_categories[i][main_category] = []
                child_categories[i][main_category].append(category_label)

        # find the primary category
        max_score = -1
        primary_category_label = None

        for i in range(0, self.category_level):
            for category_label in self.classifiers[i].classes_:
                if probabilities[category_label] < 1e-9:
                    continue
                total_score = 0
                main_category = self._get_categories(category_label)[0]
                candidates = child_categories[i][main_category]
                for actual_label in candidates:
                    probability = probabilities[actual_label]
                    if probability < 1e-9:
                        continue
                    score = self._cal_score(category_label, None, actual_label, i)
                    total_score += score * probability
                if total_score > max_score:
                    max_score = total_score
                    primary_category_label = category_label

        # find the secondary category
        max_score = -1
        secondary_category_label = None
        for i in range(0, self.category_level):
            for category_label in self.classifiers[i].classes_:
                if probabilities[category_label] < 1e-9 and secondary_category_label:
                    continue
                if category_label == primary_category_label:
                    continue
                total_score = 0
                main_category = self._get_categories(category_label)[0]
                main_category2 = self._get_categories(primary_category_label)[0]
                candidates = list(set(child_categories[i][main_category] + child_categories[i][main_category2]))
                for actual_label in candidates:
                    probability = probabilities[actual_label]
                    if probability < 1e-9:
                        continue
                    score = self._cal_score(primary_category_label, category_label, actual_label, i)
                    total_score += score * probability
                if total_score > max_score:
                    max_score = total_score
                    secondary_category_label = category_label

        return [self._get_categories(primary_category_label), self._get_categories(secondary_category_label)]

    def _cal_score(self, primary_category_label, secondary_category_label, actual_category_label, max_level):
        """
        This is a helper method to calculate the score for a predict result.
        :param primary_category_label: the primary category
        :param secondary_category_label: the secondary category
        :param actual_category_label: the actual category
        :param max_level: the max level we concerned
        :return: the score
        """
        primary_categories = self._get_categories(primary_category_label)
        if not secondary_category_label:
            secondary_categories = None
        else:
            secondary_categories = self._get_categories(secondary_category_label)
        actual_categories = self._get_categories(actual_category_label)
        total_score = 0
        ignored_primary = False
        ignored_secondary = False
        for i in range(0, max_level + 1):
            if primary_categories and i < len(primary_categories):
                pv = primary_categories[i]
            else:
                pv = None
            if actual_categories and i < len(actual_categories):
                av = actual_categories[i]
            else:
                av = None
            if secondary_categories and i < len(secondary_categories):
                sv = secondary_categories[i]
            else:
                sv = None
            primary_equal = pv == av
            secondary_equal = (secondary_categories is not None) and sv == av
            if not primary_equal:
                ignored_primary = True
            if not secondary_equal:
                ignored_secondary = True

            if not ignored_primary:
                total_score += self.level_scores[i]

            if ignored_primary and (not ignored_secondary):
                total_score += 0.5 * self.level_scores[i]

        return total_score

    @staticmethod
    def _get_category_label(category_obj, level):
        """
        Gets the category label
        :param category_obj: the category object. (array representation)
        :param level: the level
        :return: the category (string representation)
        """
        result = ''
        for i in range(0, level + 1):
            if i < len(category_obj):
                level_label = category_obj[i]
                if not level_label:
                    level_label = '$'
            else:
                # place holder
                level_label = '$'
            if not result:
                result = level_label
            else:
                result = result + '###' + level_label
        return result

    @staticmethod
    def _get_categories(category_label):
        """
        Converts the category from string representation to array representation.
        :param category_label: the category label
        :return: the category (in array representation)
        """
        if not category_label:
            return None
        return map(lambda x: x if x != '$' else None, category_label.split('###'))
