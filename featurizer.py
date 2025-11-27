import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class LogFeaturizer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=50)

    def fit(self, logs):
        texts = [f"{l['method']} {l['url']}" for l in logs if l]
        self.vectorizer.fit(texts)

    def transform(self, logs):
        texts = [f"{l['method']} {l['url']}" for l in logs if l]
        tfidf = self.vectorizer.transform(texts).toarray()
        status = np.array([[int(l['status'])] for l in logs if l])
        return np.hstack((tfidf, status))
