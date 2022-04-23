#from socket import AF_LINK
from pymongo import MongoClient
#from flask_pymongo import pymongo
import pprint
from bson.objectid import ObjectId
import csv
import time
#from typing import List

class MongoDB():

    # Genre = ""
    # search_flag = SEARCH_NAME

    def __init__(self):
        super().__init__()
        # CONNECTION_STRING = "mongodb+srv://ttds_cw3:ttds_cw3@cluster0.ljnhy.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
        # client = MongoClient(CONNECTION_STRING)
        #client = MongoClient('127.0.0.1', 27017)
        client = MongoClient("mongodb://ttdscw3:3wcsdtt@localhost:27017/ttds")

        self.ttds = client.ttds
        self.news = self.ttds.news
        self.index = self.ttds.index
        self.begin_date = (0,0)
        self.end_date = (3000,0)
        self.news.create_index('_id')
        self.index.create_index('_id')
        self.index.create_index('word')
        
    
    def set_search_date(self, begin_date, end_date):
        if begin_date != None:
            byear = begin_date[:begin_date.find('-')]
            bmonth = begin_date[begin_date.find('-')+1:]
            self.begin_date = (int(byear),int(bmonth))
        if end_date != None:
            eyear = end_date[:begin_date.find('-')]
            emonth = end_date[begin_date.find('-')+1:]
            self.end_date = (int(eyear),int(emonth))

    def insert_news(self, news_list):
        last_news = self.news.find().sort('_id',-1).limit(1)
        for news in last_news:
            #pprint.pprint(news)
            init = news['_id'] + 1
            i = init
        #print(i)
        for news in news_list:
            news_info = news
            news_info["_id"] = i
            self.news.insert_one(news_info)
            i += 1
        
        return init

    def separate(word):
        word1 = {}
        word2 = {}

        i = 0
        for doc in word:
            #print(doc)
            if i <= len(word)/2:
                word1[doc] = {}
                word1[doc] = word[doc]
            else:
                word2[doc] = {}
                word2[doc] = word[doc]
            i += 1
        #print(word1,word2)
        return word1, word2

    def loadindex(self, index_path, Frist=True):
        index = {}
        #i = -1
        with open(index_path, 'r', encoding='utf-8') as f:
            #lines = f.readlines()
            line = f.readline()
            #for line in lines: 
            while line:
                try:
                    if (line[0] != '\t' and  line[0] != '\n'):
                        word = line[:line.find(':')]
                        index[word] = {}
                        #print(word)
                        #i += 1
                    elif (line[0] == '\t'):
                        doc = line[1:line.find(':')]
                        #print(doc)
                        position = line[line.find(':')+2:-1]
                        p = position.split(',')
                        #print(position)
                        index[word][doc] = p
                        #print(index[word])
                    line = f.readline()
                except:
                    break
        if Frist:
            self.insert_indexes(index)
        else:
            self.insert_indexes(index, False)
        return index  

    def insert_word_index(self, collection_name, words, init_num):
        i = init_num
        for word in words:
            try:
                word_info = {}
                word_info["_id"] = i
                word_info["word"] = word[0]
                word_info['dictionary'] = word[1]
                collection_name.insert_one(word_info)
                i += 1
            except:
                print('separate: ' + word[0] + ' doc num = ' + str(i))
                word_list = []
                dict1,dict2 = self.separate(word[1])
                word_list.append((word[0], dict1))
                word_list.append((word[0], dict2))
                i = self.insert_word_index(collection_name, word_list, i)
                print('separate doc number: ' + str(i))
        return i

    def insert_indexes(self, indexes, first=True):
        collection_name = self.index
        for word in indexes:
            dic = self.index.find_one({"word": str(word)})
            if dic == None:
                if first:
                    i = 0
                else:
                    last_index = collection_name.find().sort('_id',-1).limit(1)
                    for index in last_index:
                        i = index['_id'] + 1
                    word_list = [(word, indexes[word])]
                    self.insert_word_index(collection_name, word_list, i)
            else:
                orginal_dict = dic['dictionary']
                orginal_dict.update(indexes[word])
                collection_name.update_one(filter={"word": word }, update = {"$set":{"dictionary": orginal_dict}})

    def in_time(self, date):
        IN_TIME = False
        year = int(date[:date.find('-')])
        month = int(date[date.find('-')+1:date.find('-',date.find('-')+1)])

        if self.begin_date[0] < year and year < self.end_date[0]:
            IN_TIME = True
        elif self.begin_date[0] == year and year == self.end_date[0]:
            if self.begin_date[1] <= month and month <= self.end_date[1]:
                IN_TIME = True
        elif self.begin_date[0] == year:
            if self.begin_date[1] <= month:
                IN_TIME = True
        elif year == self.end_date:
            if month <= self.end_date[1]:
                IN_TIME = True
        return IN_TIME

    
    def get_news_by_id(self, doc_list):
        news_result = []
        for id in doc_list:
            # Given a doc_list which contains the id of news, the news information is returned.
            news_temp = {}
            news = self.news.find_one({"_id": int(id)})
            if self.in_time(news['date']):
                news_temp['name'] = news['title']
                news_temp['content'] = news['article']
                news_temp['Artist'] = news['authors']
                news_temp['URL'] = news['url']
                news_temp['date'] = news['date']
                news_result.append(news_temp)
            else:
                continue
        return news_result

    def get_all_doc(self):
        # Return all the numbers of lyrics
        num = self.news.count_documents({})
        doc_list = []
        for i in range(num):
            doc_list.append(i)
        return doc_list

    def get_dictionary_by_word(self, word):
        #Given the words of a song as a list, return the corresponding inverted index in the same order.

        # for word in words:
        time_start = time.time()
        dics = self.index.find({"word": str(word)}).limit(2)
        dic_temp = {word:{}}
        for dic in dics:
            dic_temp[word].update(dic['dictionary'])
        # for i in range(dic_length):
        #     if i == 0:
        #         dic_temp.update({word:dic2[i]["dictionary"]})
        #     elif i ==1 :
        #         dic_temp[word].update(dic2[i]["dictionary"])
        #     else:
        #         break
        time_end=time.time()
        print('get_dictionary_by_word time cost',time_end-time_start,'s', " word ")
        # dic_temp = {}
        # word = dic['word']
        # dic_temp[word] = dic['dictionary']
        # word_num = dic['_id']
        # while True:
        #     dic = self.index.find_one({"_id": word_num+1})
        #     if dic['word'] == word:
        #         dic_temp[word].update(dic['dictionary'])
        #         word_num += 1
        #     else:
        #         break

        return dic_temp

    # def get_words_tf(self, sum_data):
    #     dic = {}
    #     dic_temp = self.get_dictionary_by_words(sum_data)
    #     for term in sum_data:
    #         dic[term] = {}
    #         for element in dic_temp[term]:
    #             dic[term].update({element:len(dic_temp[term][element])})
    #     return dic

if __name__ == '__main__':
    ttds = MongoDB()
    #ttds.get_news_by_id(['98175'])
    # test.get_lyrics_by_id(id):
    # lyric = ttds.get_lyrics_by_id(['999'])
    # pprint.pprint(lyric)
    # print(ttds.get_dictionary_by_words(['fool']))

    
    # test get_lyrics_by_ids(self, ids)
    # lyric_list = ttds.get_news_by_id([0,1,2])
    # pprint.pprint(lyric_list)
    
    # test get_dictionary_by_word(self, word)
    #dic_list = ttds.get_dictionary_by_word("star")
    #pprint.pprint(dic_list)
    
    # test get_dictionary_by_words(self, words)
    print('START')
    t0 = time.time()
    a = ttds.get_dictionary_by_word("star")
    print(a)
    print(time.time() - t0)
    
    # >>>('0', ['42']) 
    '''
    # test get_all_doc(self)
    doc_list = ttds.get_all_doc()
    pprint.pprint(doc_list)
    
    # test get_artists_by_genre(self, genre)
    artist_list = ttds.get_artists_by_genre('Rock')
    pprint.pprint(artist_list)
    
    # test get_lyrics_by_artist(self, astist)
    lyric_list = ttds.get_lyrics_by_artist('10000 Maniacs')
    pprint.pprint(lyric_list)
    '''
