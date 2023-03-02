import numpy as np


def precision_at_k(recommended_list, bought_list, k=5):
    bought_list = np.array(bought_list)
    recommended_list = np.array(recommended_list)
    recommended_list = recommended_list[:k]
    flags = np.isin(recommended_list, bought_list)
    precision = flags.sum() / len(recommended_list)
    return precision


def recall_at_k(recommended_list, bought_list, k=5):
    bought_list = np.array(bought_list)
    recommended_list = np.array(recommended_list)
    flag = np.isin(recommended_list[:k], bought_list)
    recall = flag.sum() / len(bought_list)
    return recall
