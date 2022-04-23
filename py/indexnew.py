import re
from collections import defaultdict, OrderedDict
from decimal import *
import csv
from nltk.stem import PorterStemmer
from nltk.stem.porter import PorterStemmer
import sys

csv.field_size_limit(sys.maxsize)

def tokenisation(data):

    part = r'\w+'
    return [word.replace('_',' ') for word in re.findall(part,data)]


def stoppingremove(data):
    stop_words = []
    path4 = R'../englishST.txt'
    with open(path4) as f:
        lines = f.readlines()
    for line in lines:
        stop_words.append(line.replace('\n',''))
    data3 = []
    f.close() 
    data2 = " ".join([word.lower() for word in data if word.lower() not in stop_words])
    for word in data2.split():
        data3.append(word)
    return data3


def normalisation(data):
    porter_stemmer = PorterStemmer()
    data4 = [porter_stemmer.stem(i) for i in data]
    return data4

def preprocessing(data):
    data = tokenisation(data)
    data = stoppingremove(data)
    data = normalisation(data)
    return data

def store_index(index, frequent, path):
    i = 0
    with open(path, 'w+', encoding = 'utf-8') as f:
        for term in index.keys():
            if int(i) == len(index):
                break
            if len(index[term]) == 0:
                continue
            f.write(term + ':' + str(frequent[term])+'\n')
            dict1 = index[term]
            for documentid in dict1.keys():
                position_l = dict1[documentid]
                f.write('\t' + str(documentid) + ': '\
                     +','.join(str(i) for i in position_l)\
                          +'\n')
            f.write('\n')
            i += 1
    return

def indexer(news_list, init_num):
    index  = defaultdict(lambda: defaultdict(list))
    frequent = {}
    i = init_num
    for news in news_list:
        line = news['title'] + news['article']
        if line == '':
            continue
        pre = preprocessing(line)
        for position in range(len(pre)):
            if pre[position] not in frequent:
                frequent[pre[position]] = 0
            frequent[pre[position]] += 1
            index[pre[position]][i] += [position + 1]
        i += 1

    index = OrderedDict(sorted(index.items()))
    return index, frequent