import nltk
import numpy as np
import pandas as pd

def match_file(file, filelist):
    score = []
    for i, meta_file in enumerate(filelist):
        if meta_file == 'NaN' or pd.isnull(meta_file):
            score = np.append(score, 1000)
        else:
            score = np.append(score, nltk.edit_distance(file, meta_file))

    match = np.argmin(score)
    return match
