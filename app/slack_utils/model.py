import os
import re
import unicodedata

import joblib
import spacy
import nltk

nltk.download('stopwords')

from nltk.corpus import stopwords


class Model:
    def __init__(self):
        self._model = joblib.load(os.path.join(
            os.path.dirname(__file__), "sentiment_analysis_model.pkl"))
        self._vectorizer = joblib.load(os.path.join(
            os.path.dirname(__file__), "vectorizer.pkl"))

        self._nlp = spacy.load('en_core_web_sm')
        self._sentiments = {"sad": 0, "happy": 1, "love": 2, "angry": 3,
                            "fear": 4, "surprise": 5, "anxious": 6, "neutarl": 7}
        self._contractions = {
            "aren't": "are not",
            "can't": "cannot",
            "couldn't": "could not",
            "didn't": "did not",
            "doesn't": "does not",
            "don't": "do not",
            "hadn't": "had not",
            "hasn't": "has not",
            "haven't": "have not",
            "he'd": "he had",
            "he'll": "he will",
            "he's": "he is",
            "I'd": "I had",
            "I'll": "I will",
            "I'm": "I am",
            "I've": "I have",
            "isn't": "is not",
            "let's": "let us",
            "mightn't": "might not",
            "mustn't": "must not",
            "shan't": "shall not",
            "she'd": "she had",
            "she'll": "she will",
            "she's": "she is",
            "shouldn't": "should not",
            "that's": "that is",
            "there's": "there is",
            "they'd": "they had",
            "they'll": "they will",
            "they're": "they are",
            "they've": "they have",
            "we'd": "we had",
            "we're": "we are",
            "we've": "we have",
            "weren't": "were not",
            "what'll": "what will",
            "what're": "what are",
            "what's": "what is",
            "what've": "what have",
            "where's": "where is",
            "who's": "who had",
            "who'll": "who will",
            "who're": "who are",
            "who's": "who is",
            "who've": "who have",
            "won't": "will not",
            "wouldn't": "would not",
            "wouldnt": "would not",
            "you'd": "you had",
            "you'll": "you will",
            "you're": "you are",
            "you've": "you have",
            "arent": "are not",
            "cant": "cannot",
            "couldnt": "could not",
            "didnt": "did not",
            "doesnt": "does not",
            "dont": "do not",
            "hadnt": "had not",
            "hasnt": "has not",
            "havent": "have not",
            "Id": "I had",
            "Ill": "I will",
            "Im": "I am",
            "Ive": "I have",
            "isnt": "is not",
            "lets": "let us",
            "mightnt": "might not",
            "mustnt": "must not",
            "shouldnt": "should not",
            "werent": "were not",
            "gonna": "going to",
            "imma": "i am going to"
        }

    def _clean_text(self, text):

        # lower case conversion
        text = text.lower()

        # Decontrating: rewriting text without the contrations. Ex.: I'm = I am; aren't = are not ...
        if type(text) is str:
            for key in self._contractions:
                value = self._contractions[key]
                text = text.replace(key, value)

        # remove emails
        text = re.sub(
            r"([a-zA-Z0-9+._-]+@[a-zA-Z0-9+._-]+\.[a-zA-Z0-9+._-]+)", " ", text)

        # remove hyperlink
        text = re.sub(
            r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", " ", text)

        # remove rt
        text = re.sub(r"RT[\s]+", "", text)

        # Remove empty spaces
        text = " ".join([t.strip() for t in text.split()])

        # Deleting user mention (@user):
        text = re.sub(r"@[A-Za-z0-9]+", "", text)

        # remove accented characters
        text = unicodedata.normalize("NFKD", text).encode(
            "ascii", "ignore").decode("utf-8", "ignore")

        # remove remaining special caracters
        text = re.sub(r"[^A-Za-z\s]", "", text)

        return text

    def _filter_words(self, text):

        # remove stop words
        stop_words = set(stopwords.words("english"))
        text = " ".join([word for word in text.split()
                        if word not in stop_words])

        # convert verbs into root form
        tweet_list = []
        for token in self._nlp(text):
            lemma = str(token.lemma_)
            if lemma == "-PRON-" or lemma == "be":
                lemma = token.text
            tweet_list.append(lemma)
        text = " ".join(tweet_list)

        return text

    def _expression_check(self, prediction_input):

        results = []

        for i, prediction in enumerate(prediction_input):
            sentiment = next(
                (key for key, value in self._sentiments.items() if value == prediction), None)
            if sentiment is not None:
                results.append((i, sentiment))
            else:
                results.append((i, "unknown"))

        return results

    def predict(self, input):
        input = [self._clean_text(text) for text in input]
        input = [self._filter_words(text) for text in input]
        transformed_input = self._vectorizer.transform(input)
        prediction = self._model.predict(transformed_input)
        return self._expression_check(prediction)
