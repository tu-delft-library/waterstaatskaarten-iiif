# Import packages
import nltk
import numpy as np
import pandas as pd

# Function to match data set of strings to a specific string using edit distance
def match_file(file, filelist):
    score = []
    # Loop through data set of strings
    for i, meta_file in enumerate(filelist):
        # Check if value in string equals NaN, if so a penalty of 1000 is given
        if meta_file == 'NaN' or pd.isnull(meta_file):
            score = np.append(score, 1000)
        else:
            # Calculate edit distance between specific string and string from list
            score = np.append(score, nltk.edit_distance(file, meta_file))

    # Get index of the lowest edit distance value
    match = np.argmin(score)
    # Return the index
    return match
