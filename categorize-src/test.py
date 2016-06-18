import os, json
from sklearn.feature_extraction.text import CountVectorizer
import nltk, string
from nltk import word_tokenize
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import CountVectorizer
from load_data import load_data
from sklearn.feature_extraction.text import TfidfTransformer

# load configuration
with open('conf/config.json', 'rt') as fd:
    appConfig = json.load(fd)

stemmers = {}
stemmers['english'] = SnowballStemmer('english', ignore_stopwords=True)
stemmers['spanish'] = SnowballStemmer('spanish', ignore_stopwords=True)

punctuations = list(string.punctuation)
x = 0


def stem_tokens(tokens, stemmer):
    stemmed = []
    for item in tokens:
        stemmed.append(stemmer.stem(item))
    return stemmed


def english_tokenize(text):
    tokens = word_tokenize(text, 'english')
    stems = stem_tokens(tokens, stemmers['english'])
    stems = [i for i in stems if i not in punctuations]
    return stems


def spanish_tokenize(text):
    tokens = word_tokenize(text, 'spanish')
    stems = stem_tokens(tokens, stemmers['spanish'])
    stems = [i for i in stems if i not in punctuations]
    if 'quien' in stems:
        global x
        x += 1
    return stems


chile_data = load_data(appConfig['chile_data_file'])
count_vect = CountVectorizer(tokenizer=spanish_tokenize, ngram_range=(1, 3))
print(count_vect)
X_train_counts = count_vect.fit_transform(chile_data['data'])
print(count_vect.vocabulary_.get('mayor'))
tfidf_transformer = TfidfTransformer()
X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
print(X_train_tfidf[0])




