import string

def clean_list(*args):
    try:
        temp = list(args)
        cleaned = list(filter(None, temp))
    except Exception:
        pass
    return cleaned

def normalize(s):
    for p in string.punctuation:
        s = s.replace(p, '')

    return s.lower().strip()

def convertArrayToString(array):
    return ','.join(str(element) for element in array)

def convertStringToArray(s):
    return s.split(',')

def prepFullAddressSearch(*args):
    try:
        temp = list(args)
        cleaned = list(filter(None, temp))
    except Exception:
        pass
    return ' '.join(map(str, cleaned))


#
# from nltk import metrics, stem, tokenize
#
# stemmer = stem.PorterStemmer()
#
# def normalize(s):
#     words = tokenize.wordpunct_tokenize(s.lower().strip())
#     return ' '.join([stemmer.stem(w) for w in words])
#
# def fuzzy_match(s1, s2, max_dist=3):
#     return metrics.edit_distance(normalize(s1), normalize(s2)) <= max_dist
