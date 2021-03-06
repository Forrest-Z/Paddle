# Copyright (c) 2016 PaddlePaddle Authors. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Movielens 1-M dataset.

TODO(yuyang18): Complete comments.
"""

import zipfile
from common import download
import re
import random
import functools

__all__ = [
    'train', 'test', 'get_movie_title_dict', 'max_movie_id', 'max_user_id',
    'age_table', 'movie_categories', 'max_job_id', 'user_info', 'movie_info'
]

age_table = [1, 18, 25, 35, 45, 50, 56]


class MovieInfo(object):
    def __init__(self, index, categories, title):
        self.index = int(index)
        self.categories = categories
        self.title = title

    def value(self):
        return [
            self.index, [CATEGORIES_DICT[c] for c in self.categories],
            [MOVIE_TITLE_DICT[w.lower()] for w in self.title.split()]
        ]

    def __str__(self):
        return "<MovieInfo id(%d), title(%s), categories(%s)>" % (
            self.index, self.title, self.categories)

    def __repr__(self):
        return self.__str__()


class UserInfo(object):
    def __init__(self, index, gender, age, job_id):
        self.index = int(index)
        self.is_male = gender == 'M'
        self.age = age_table.index(int(age))
        self.job_id = int(job_id)

    def value(self):
        return [self.index, 0 if self.is_male else 1, self.age, self.job_id]

    def __str__(self):
        return "<UserInfo id(%d), gender(%s), age(%d), job(%d)>" % (
            self.index, "M"
            if self.is_male else "F", age_table[self.age], self.job_id)

    def __repr__(self):
        return str(self)


MOVIE_INFO = None
MOVIE_TITLE_DICT = None
CATEGORIES_DICT = None
USER_INFO = None


def __initialize_meta_info__():
    fn = download(
        url='http://files.grouplens.org/datasets/movielens/ml-1m.zip',
        module_name='movielens',
        md5sum='c4d9eecfca2ab87c1945afe126590906')
    global MOVIE_INFO
    if MOVIE_INFO is None:
        pattern = re.compile(r'^(.*)\((\d+)\)$')
        with zipfile.ZipFile(file=fn) as package:
            for info in package.infolist():
                assert isinstance(info, zipfile.ZipInfo)
                MOVIE_INFO = dict()
                title_word_set = set()
                categories_set = set()
                with package.open('ml-1m/movies.dat') as movie_file:
                    for i, line in enumerate(movie_file):
                        movie_id, title, categories = line.strip().split('::')
                        categories = categories.split('|')
                        for c in categories:
                            categories_set.add(c)
                        title = pattern.match(title).group(1)
                        MOVIE_INFO[int(movie_id)] = MovieInfo(
                            index=movie_id, categories=categories, title=title)
                        for w in title.split():
                            title_word_set.add(w.lower())

                global MOVIE_TITLE_DICT
                MOVIE_TITLE_DICT = dict()
                for i, w in enumerate(title_word_set):
                    MOVIE_TITLE_DICT[w] = i

                global CATEGORIES_DICT
                CATEGORIES_DICT = dict()
                for i, c in enumerate(categories_set):
                    CATEGORIES_DICT[c] = i

                global USER_INFO
                USER_INFO = dict()
                with package.open('ml-1m/users.dat') as user_file:
                    for line in user_file:
                        uid, gender, age, job, _ = line.strip().split("::")
                        USER_INFO[int(uid)] = UserInfo(
                            index=uid, gender=gender, age=age, job_id=job)
    return fn


def __reader__(rand_seed=0, test_ratio=0.1, is_test=False):
    fn = __initialize_meta_info__()
    rand = random.Random(x=rand_seed)
    with zipfile.ZipFile(file=fn) as package:
        with package.open('ml-1m/ratings.dat') as rating:
            for line in rating:
                if (rand.random() < test_ratio) == is_test:
                    uid, mov_id, rating, _ = line.strip().split("::")
                    uid = int(uid)
                    mov_id = int(mov_id)
                    rating = float(rating) * 2 - 5.0

                    mov = MOVIE_INFO[mov_id]
                    usr = USER_INFO[uid]
                    yield usr.value() + mov.value() + [[rating]]


def __reader_creator__(**kwargs):
    return lambda: __reader__(**kwargs)


train = functools.partial(__reader_creator__, is_test=False)
test = functools.partial(__reader_creator__, is_test=True)


def get_movie_title_dict():
    __initialize_meta_info__()
    return MOVIE_TITLE_DICT


def __max_index_info__(a, b):
    if a.index > b.index:
        return a
    else:
        return b


def max_movie_id():
    __initialize_meta_info__()
    return reduce(__max_index_info__, MOVIE_INFO.viewvalues()).index


def max_user_id():
    __initialize_meta_info__()
    return reduce(__max_index_info__, USER_INFO.viewvalues()).index


def __max_job_id_impl__(a, b):
    if a.job_id > b.job_id:
        return a
    else:
        return b


def max_job_id():
    __initialize_meta_info__()
    return reduce(__max_job_id_impl__, USER_INFO.viewvalues()).job_id


def movie_categories():
    __initialize_meta_info__()
    return CATEGORIES_DICT


def user_info():
    __initialize_meta_info__()
    return USER_INFO


def movie_info():
    __initialize_meta_info__()
    return MOVIE_INFO


def unittest():
    for train_count, _ in enumerate(train()()):
        pass
    for test_count, _ in enumerate(test()()):
        pass

    print train_count, test_count


if __name__ == '__main__':
    unittest()
