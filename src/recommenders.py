import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares
from implicit.nearest_neighbours import bm25_weight, ItemItemRecommender


class MainRecommender:
    """Рекоммендации, которые можно получить из ALS

    Input
    -----
    user_item_matrix: pd.DataFrame
        Матрица взаимодействий user-item
    """

    def __init__(self, data, weighting=True):
        # your_code. Это не обязательная часть. Но если вам удобно что-либо посчитать тут - можно это сделать
        self.data = data
        self.user_item_matrix = self.prepare_matrix(data)  # pd.DataFrame
        self.id_to_itemid, self.id_to_userid, self.itemid_to_id, self.userid_to_id = self.prepare_dicts(
            self.user_item_matrix)
        if weighting:
            self.user_item_matrix = bm25_weight(self.user_item_matrix.T).T
        self.model = self.fit(self.user_item_matrix)
        self.own_recommender = self.fit_own_recommender(self.user_item_matrix)

    @staticmethod
    def prepare_matrix(data):
        # your_code
        user_item_matrix = pd.pivot_table(data,
                                          index='user_id', columns='item_id',
                                          values='quantity',
                                          aggfunc='count',
                                          fill_value=0
                                          )
        user_item_matrix[user_item_matrix > 0] = 1
        user_item_matrix = user_item_matrix.astype(float)
        return user_item_matrix

    @staticmethod
    def prepare_dicts(user_item_matrix):
        """Подготавливает вспомогательные словари"""
        userids = user_item_matrix.index.values
        itemids = user_item_matrix.columns.values
        matrix_userids = np.arange(len(userids))
        matrix_itemids = np.arange(len(itemids))
        id_to_itemid = dict(zip(matrix_itemids, itemids))
        id_to_userid = dict(zip(matrix_userids, userids))
        itemid_to_id = dict(zip(itemids, matrix_itemids))
        userid_to_id = dict(zip(userids, matrix_userids))
        return id_to_itemid, id_to_userid, itemid_to_id, userid_to_id

    @staticmethod
    def fit_own_recommender(user_item_matrix):
        """Обучает модель, которая рекомендует товары, среди товаров, купленных юзером"""
        own_recommender = ItemItemRecommender(K=1, num_threads=4)
        own_recommender.fit(csr_matrix(user_item_matrix).T.tocsr())
        return own_recommender

    @staticmethod
    def fit(user_item_matrix, n_factors=20, regularization=0.01, iterations=15, num_threads=4):
        """Обучает ALS"""
        model = AlternatingLeastSquares(factors=n_factors,
                                        regularization=regularization,
                                        iterations=iterations,
                                        num_threads=num_threads,
                                        random_state=8)
        model.fit(csr_matrix(user_item_matrix).T.tocsr())
        return model

    def get_top_items_from_user(self, user, N=5):
        '''Получить топ-N товаров от юзера'''
        dt = self.data[self.data['user_id'] == user]
        pop = dt.groupby(['item_id'])['quantity'].count().reset_index()
        pop.sort_values('quantity', ascending=False, inplace=True)
        pop = pop[pop['item_id'] != 999999][:N]
        return pop['item_id']

    def get_similar_items_recommendation(self, user, N=5):
        """Рекомендуем товары, похожие на топ-N купленных юзером товаров"""

        # your_code
        lst = []
        item_ls = self.get_top_items_from_user(user, N)
        for item_id in item_ls:
            rec = self.model.similar_items(self.itemid_to_id[item_id], N=2)
            lst.append(rec[1][0])
        res = [self.id_to_itemid[item] for item in lst]
        assert len(res) == N, 'Количество рекомендаций != {}'.format(N)
        return res

    def get_similar_users_recommendation(self, user, N=5):
        """Рекомендуем топ-N товаров, среди купленных похожими юзерами"""

        # your_code
        user_lst = [u[0] for u in self.model.similar_users(self.userid_to_id[user], N=N)]
        res = []
        for u in user_lst:
            item = np.array(self.get_top_items_from_user(self.id_to_userid[u], 1))[0]
            res.append(item)
        assert len(res) == N, 'Количество рекомендаций != {}'.format(N)
        return res
