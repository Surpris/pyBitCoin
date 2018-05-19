#-*- coding: utf-8 -*-
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

def appends(str0, adstr):
    """
    Add `adstr` to `str0`.

    <Input>
        str0: a str object
        adstr: a str object which is added to the last of `str0`.
    """
    if str0.endswith(adstr) is True:
        return str0
    else:
        return str0 + adstr

def predict_score(X, y, random_state1=10, test_size=0.3):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state1)
    clf = MLPClassifier(solver="sgd", random_state=5, max_iter=10000, hidden_layer_sizes=(200,))
    _ = clf.fit(X_train, y_train)
    return clf.score(X_test, y_test)
