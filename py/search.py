from gc import get_count
import math
import threading
from queue import Queue

from numpy import mean
from py.preprocessing import preprocess,preprocess_query,Proximity_Query_Process, preprocess_query_for_rank
import logging
from . import MongoInterface
import py.search_cache as cache
import pickle
import time

# ******* this is the data structure of news **********

# news = {
#     "key word":"leaf",
#     "genre":"2016-10:2017:02",
#     "count": 35,     # 35 doc has been found
#     "pages": 3,        # 35 need at least 3 pages to show. 3 pages means show all documents in three pieces, "more" can be click for another twice
#     "cur_page": 2     # current page is 3, from 1 to max page number
#     "allnews":[
#         {
#             "name":"name1"
#             "content":"content1"
#              "Artist":["AAA"]
#              "URL" : "http"
#               "date": "2020"
#              "highlight": {
#                   "name":[(1,3), (4,6)]               # 表示搜出来的歌名，歌名索引为1到3，3到6（两个元组表示有2个单词）的字母高亮
#                   "content":[(5,6),(7,8),(9,11))]     # 表示搜出来的歌词，歌词索引为5到6，7到8,9到11（三个元组表示有3个单词）的字母高亮
#              }
#         },
#         {
#             "name":"name2",
#             "content":"content2"
#             "Artist" :["BBB"]
#              "URL" : "http"
#              "date": "2020"
#              "highlight": {
#                   "name":[(1,3), (4,6)]               # 表示搜出来的歌名，歌名索引为1到3，3到6（两个元组表示有2个单词）的字母高亮
#                   "content":[(5,6),(7,8),(9,11))]     # 表示搜出来的歌词，歌词索引为5到6，7到8,9到11（三个元组表示有3个单词）的字母高亮
#         }
#     ]
# }

# constant
LEFT_DISPLAY_WORDS = 30 # show 10 words on the left of the key words in the news
RIGHT_DISPLAY_WORDS = 70 # show 20 words on the left of the key words in the news
DISPLAY_WORDS = LEFT_DISPLAY_WORDS + RIGHT_DISPLAY_WORDS + 1
TIME_LIMIT = 1 # the max searching time, if searching time exceed this value, TFIDF will not be calculated completely
MAX_DOC_SHOW = 12 # the max doc number to show on the web
RANK_BY_TFIDF = 0
RANK_BY_BM25 = 1

# global value
ttds_db = MongoInterface.MongoDB()
ttds_cache = cache.cache()
doc_info_dict = {}
rank_method = RANK_BY_BM25
index_cache = {}
# g_count = 0

display_soc = []     # docs showing on the web. Based on TFIDF score, select 10 most related doc to display on the web
doc_full_result = [] # full doc results
rank_score = [] # full rank score
news_results = {}
total_doc_number = -1 # total_doc_number
g_query = "" # user input a query
g_date = "2016-01;2030:12"

# configue log
logging.basicConfig(level=logging.DEBUG,#log level configue
            filename='log_search.log',  # write log in log_new.log
            filemode='w',## log mode，w is write mode, the old log will be overwrite
            # a is add mode, the new log will be after the old log
            format=
            '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
            # log format
            )

# para: none
# get a dict, the key of this dict is all doc number in our database, value is the length of the doc
# *******************************************************************************************
def get_all_doc_number_thread(info_queue):
    global doc_info_dict
    if doc_info_dict == {} and info_queue.empty() == 1:
        doc_len_dict = pickle.load(open("py/search_cache/doc_len_dict.pkl", 'rb'), encoding='utf-8')
        info_queue.put(doc_len_dict)


# ******************************************************************************
# *************************** interact with database part **********************
# ******************************************************************************

def Set_search_date():
    global g_date
    data_split = g_date.split(";")
    logging.info("set date: "+ data_split[0]+ " : "+data_split[1])
    if len(data_split[0]) !=0 and len(data_split[1]) !=0:
        ttds_db.set_search_date(data_split[0], data_split[1])

# para: a list, word is a item in the list
# return a dict, the key is doc number, the value is a list, the list is the location of this item in the doc.
def find_word_in_database(words):
    result_index = {}
    global index_cache
    for word in words:
        if word in index_cache:
            result_index[word] = index_cache[word]
        else:
            index_cache[word] = ttds_db.get_dictionary_by_word(word)[word]
            result_index[word] = index_cache[word]
    return result_index

# ***************    get news information( news title and news article)    ***********************
# para: list, a list of doc number
# return a dict, every element is a dict.
# in this dictkey. "name" is the title of the news, key "content" is the article of the news.
# *****************************************************************************************
def get_news_informaiton(doc_list):
    return ttds_db.get_news_by_id(doc_list)

# ******************************************************************************
# ****************************** search part ***********************************
# ******************************************************************************

# ************ Boolean_search function **************
# temp_Proximity_position is a dictionary
# key is the position of the word in the phrase, value is a list of position in doc
# Proximity_distance is the distance requirement between two words
def find_position_distance(temp_Proximity_position,Proximity_distance):
    if Proximity_distance != -1: # Proximity search
        return_flag=0
        for p in range(len(temp_Proximity_position)-1):
            q = p+1
            break_flag=0
            for P in range(len(temp_Proximity_position[p])):
                for Q in range(len(temp_Proximity_position[q])):
                    if (temp_Proximity_position[p][P]-temp_Proximity_position[q][Q])<=Proximity_distance and \
                        (temp_Proximity_position[p][P]-temp_Proximity_position[q][Q])>=-Proximity_distance:
                        break_flag=1
                        return_flag+=1
                        break
                if break_flag == 1:
                    break
        # only if all words meet the position condition between each pair, return 1
        if return_flag==len(temp_Proximity_position)-1:
            return 1
    else:   # parse search
        p = 0
        temp_location = {}
        for q in range(1, len(temp_Proximity_position)):
            for P in range(len(temp_Proximity_position[p])):
                if temp_Proximity_position[p][P] + q in temp_Proximity_position[q]:
                    if temp_Proximity_position[p][P] not in temp_location:
                        temp_location[temp_Proximity_position[p][P]] = 1
                    elif temp_Proximity_position[p][P] in temp_location:
                        temp_location[temp_Proximity_position[p][P]] += 1
        
        # only if all positions of the first word in parse meet the condition, return 1
        for i in temp_location:
            if temp_location[i] == len(temp_Proximity_position)-1:
                return 1
    return 0

def phrase_search(phrase, Proximity_distance):
    doc_search = []
    inverted_index_dict = find_word_in_database(phrase)

    doc_common = inverted_index_dict[phrase[0]].keys()
    # if just search one word, return now
    if len(inverted_index_dict) == 1:
        return doc_common
    
    # doc_common means a list for the document number where all words in the phrase coexist
    for m in range(len(inverted_index_dict)):
        doc_common = doc_common & inverted_index_dict[phrase[m]].keys()
    
    for n in doc_common:
        temp_Proximity_position={}
        
        for m in range(len(inverted_index_dict)):
            temp_Proximity_position[m] = [int(position) for position in inverted_index_dict[phrase[m]][n]]
        
        # In document n if The distance between words in the phrase is equal to Proximity_distance
        # find_position_distance method return 1
        if find_position_distance(temp_Proximity_position, Proximity_distance)==1 and n not in doc_search:
            doc_search.append(n)
    return doc_search

def Boolean_search(query, info_queue):
    # rank_flag = 0, if find AND OR NOT in queries, it means Boolean search
    # rank_flag = 1, if not find, it means Phrase search or Proximity search, all words will be put in a list(or_data)
    and_data, or_data, not_data, Proximity_distance = preprocess_query(query, rank_flag = 0)

    doc_search = []
    # AND: Intersect search results
    if and_data != [] and and_data != [[]]:
        doc_search = phrase_search(and_data[0], Proximity_distance)
        for i in range(1, len(and_data)):
            doc_search = list(set(doc_search).intersection(phrase_search(and_data[i], Proximity_distance)))
    logging.info("or_data")
    logging.info(or_data)
    # OR: Union search results
    if or_data != [] and or_data != [[]]:
        for phrase in or_data:
            doc_search = list(set(doc_search).union(phrase_search(phrase, Proximity_distance)))

    global doc_info_dict
    if doc_info_dict == {}:
        doc_info_dict = info_queue.get()
        info_queue.put(doc_info_dict)

    # NOT: Subtract search results
    if not_data != [] and not_data != [[]]:
        if doc_search == []:
            doc_search = doc_info_dict.keys()
        for phrase in not_data:
            doc_search = list(set(doc_search).difference(phrase_search(phrase, Proximity_distance)))

    return doc_search

# ****************************************************************
# ************************* rank part ****************************
# ****************************************************************

# get temp score to rank the results
def get_temp_score_by_tf(sum_data, tf):
    doc_common_list = tf[sum_data[0]].keys()
    if len(sum_data) > 1:
        for word in range(1, len(sum_data)):
            doc_common_list = list(set(doc_common_list).intersection(tf[sum_data[word]].keys()))
    temp_score =dict.fromkeys(doc_common_list,0)
    for doc in temp_score:
        for word in tf:
            temp_score[doc] = temp_score[doc] + tf[word][doc]
    temp_score = dict(sorted(temp_score.items(),key = lambda x:x[1],reverse = True))

    return temp_score


# caculate TFIDF
def calculate_TFIDF(TFIDF_queue, query, time_start, doc_search):
    # this flag is to remember whether calculate_TFIDF is interuptted beacuse of time limit
    interrupt_flag = False

    time_end=time.time()
    if time_end-time_start > TIME_LIMIT:
        logging.info('break from TFIDF without calculating anythin, time cose: ' + str(time_end-time_start) +'s')
        interrupt_flag = True
        TFIDF_queue.put(([], False))

    sum_data = preprocess_query_for_rank(query)

    # caculate tf
    # number of times term t appeared in document d

    inverted_index_dict = find_word_in_database(sum_data)
    tf = {}
    for term in sum_data:
        tf[term] = {}
        for element in inverted_index_dict[term]:
            tf[term].update({element:len(inverted_index_dict[term][element])})

    time_end=time.time()
    if time_end-time_start > TIME_LIMIT and interrupt_flag == False:
        temp_score = get_temp_score_by_tf(sum_data, tf)
        time_end=time.time()
        logging.info('break from TFIDF, rank doc based on tf, time cost: ' + str(time_end-time_start) +'s')
        interrupt_flag = True
        TFIDF_queue.put((temp_score, False))
    
    #number of documents term t appeared in, t is the key, number is the value
    df={}

    #caculate df
    for i in sum_data:
        df[i] = len(tf[i])

    global doc_info_dict
    N=len(doc_info_dict)
    
    #caculate w_td
    w_td = {}
    for i in sum_data:
        temp={}
        for j in [doc for doc in tf[i] if doc in doc_search]:
            temp[j] = (1 + math.log(tf[i][j], 10)) * math.log(N/df[i], 10)
        w_td[i]=temp
    #caculate score
    score=dict.fromkeys(doc_search, 0)
    for i in w_td:
        for j in w_td[i]:
            if w_td[i][j] == 0:
                continue
            score[j] += w_td[i][j]
    sorted_score = dict(sorted(score.items(),key = lambda x:x[1],reverse = True))
    TFIDF_queue.put((sorted_score, True))

# caculate BM25
def BM25_rank(BM25_queue, query, time_start, doc_search):
    global doc_info_dict
    interrupt_flag = False
    b = 0.75
    k1 = 1.5
    k3 = 1.5
    N = len(doc_info_dict)
    avg_Length = mean(list(doc_info_dict.values()))
    sum_data = preprocess_query_for_rank(query)
    # caculate tf
    # number of times term t appeared in document d

    inverted_index_dict = find_word_in_database(sum_data)
    tf = {}
    for term in sum_data:
        tf[term] = {}
        for element in inverted_index_dict[term]:
            tf[term].update({element:len(inverted_index_dict[term][element])})

    time_end=time.time()
    if time_end-time_start > TIME_LIMIT and interrupt_flag == False:
        temp_score = get_temp_score_by_tf(sum_data, tf)
        time_end=time.time()
        logging.info('break from BM25, rank doc based on tf, time cost: ' + str(time_end-time_start) +'s')
        interrupt_flag = True
        BM25_queue.put((temp_score, False))

    #number of documents term t appeared in, t is the key, number is the value
    df={}
    #caculate df
    for i in sum_data:
        df[i] = len(tf[i])
    score=dict.fromkeys(doc_search, 0)
    # BM25
    for word in sum_data:
        for doc in score:
            score[doc] += math.log((N - df[word] + 0.5)/(df[word] + 0.5), 10) * \
                (((k3 + 1) * tf[word][doc])/(k1 * ((1 - b) + b * (doc_info_dict[doc]/avg_Length)) + tf[word][doc])) *\
                    ((k3 + 1)*tf[word][doc]/(k3 + tf[word][doc]))
    sorted_score = dict(sorted(score.items(),key = lambda x:x[1],reverse = True))
    BM25_queue.put((sorted_score, True))



# ****************************************************************
# **************** back to front end part ************************
# ****************************************************************

def find_word_position(text, position, end = 0):
    for i in range(position, len(text)-1):
        if text[i].isalpha() == 0 and text[i+1].isalpha() == 1 and end == 0:
            return i+1
        if text[i].isalpha() == 0 and end == 1:
            return i
    return len(text)

# find words from the raw text. This function is used to highlight the key words in the web
# para: words is a list of string. news_name is a string, news_content is a string
# return: highlight_location is a dict, key is "name" and "content". value is a list of position.
def find_highlight_locations(words, news_name, news_content):
    highlight_location = {"name":[], "content":[]}
    for word in words:
        word_begin = 0
        # highlight name
        while(1):
            word_begin = news_name.find(word, word_begin)
            word_end = word_begin + len(word)
            if word_begin == 0 or (word_begin > 0 and news_name[word_begin-1].isalpha() == 0 ):
                word_end = find_word_position(news_name, word_begin, 1)
                if (preprocess(news_name[word_begin: word_end], 0, 1) == word or preprocess(news_name[word_begin: word_end], 0, 0)==word)\
                    and (word_begin, word_end) not in highlight_location["name"]:
                    highlight_location["name"].append((word_begin, word_end))
            elif word_begin == -1:
                break
            word_begin += (word_end - word_begin + 1)
        word_begin = 0
        # highlight content
        while(1):
            word_begin = news_content.find(word, word_begin)
            word_end = word_begin + len(word)
            if word_begin == 0 or (word_begin > 0 and news_content[word_begin-1].isalpha() == 0 ):
                word_end = find_word_position(news_content, word_begin, 1)
                if (preprocess(news_content[word_begin: word_end], 0, 1) == word or preprocess(news_content[word_begin: word_end], 0, 0)==word)\
                    and (word_begin, word_end) not in highlight_location["content"]:
                    highlight_location["content"].append((word_begin, word_end))
            elif word_begin == -1:
                break
            word_begin += (word_end - word_begin + 1)
    return highlight_location

# extract a snippet of news to display on the web
# para: news_list is a list, every element is a dict, key is "name" and "content"
def extract_snippet_news(news_list, query):

    query, _ = Proximity_Query_Process(query)
    
    query = query.replace("AND", "").replace("OR", "").replace("NOT", "")

    query_list_1 = preprocess(query, 0, 1).split() # do not remove stop words
    query_list_2 = preprocess(query, 0, 0).split() # do not remove stop words, do not stemming
    query_for_highlight = list(set(query_list_1).union(set(query_list_2)))

    pre_query = preprocess(query).split() # remove stop words and stemming

    for news in news_list:
        news_len = len(news["content"])
        display_location = LEFT_DISPLAY_WORDS
        temp_location = 0
        # find which part to show (a location that first key word occurs).
        if len(pre_query) > 0:
            while(temp_location < len(news["content"])):
                temp_location = news["content"][temp_location:].lower().find(pre_query[0]) + temp_location
                word_end = find_word_position(news["content"], temp_location, 1)
                if temp_location == 0 or (temp_location > 0 and news["content"][temp_location-1].isalpha() == 0) and \
                    (preprocess(news["content"][temp_location: word_end], 0, 1) == pre_query[0] or preprocess(news["content"][temp_location: word_end], 0, 0)==pre_query[0]):
                    display_location = temp_location
                    break
                else:
                    temp_location = temp_location + len(pre_query[0])

        # Extract news snippets
        if display_location >= LEFT_DISPLAY_WORDS and display_location < news_len - RIGHT_DISPLAY_WORDS:
            news["content"] = news["content"][find_word_position(news["content"], display_location-LEFT_DISPLAY_WORDS):\
                find_word_position(news["content"], display_location + RIGHT_DISPLAY_WORDS)] + "..."
        elif display_location >= LEFT_DISPLAY_WORDS and display_location >= news_len - RIGHT_DISPLAY_WORDS:
            news["content"] = news["content"][find_word_position(news["content"], display_location-LEFT_DISPLAY_WORDS):] + "..."
        elif display_location < LEFT_DISPLAY_WORDS and display_location < news_len - RIGHT_DISPLAY_WORDS:
            news["content"] = news["content"][:find_word_position(news["content"], DISPLAY_WORDS)] + "..."

        news["highlight"] = find_highlight_locations(query_for_highlight, news["name"].lower(), news["content"].lower())


def get_more_doc(count):
    global rank_score
    global doc_full_result
    count = count * MAX_DOC_SHOW
    display_soc = []
    for doc_number in rank_score:
        if str(doc_number) in doc_full_result:
            if count == 0:
                display_soc.append(str(doc_number))
            else:
                count = count -1
        if len(display_soc) == MAX_DOC_SHOW:  # only display MAX_DOC_SHOW docs on the web
            break
    return display_soc

def get_data_to_front_end(display_soc, count = 0):
    global doc_full_result
    global g_date
    news_results = {}

    news_results["key word"] = g_query
    news_results["genre"]  = g_date
    news_results["count"]  = total_doc_number
    news_results["pages"] = max(math.ceil(total_doc_number / MAX_DOC_SHOW), 1)
    news_results["cur_page"]  = min(max(count, 1), news_results["pages"])

    t0 = time.time()
    news_results["allsongs"] = get_news_informaiton(display_soc)
    logging.info("get news inforamtion cost time: "+str(time.time()-t0))
    
    t0 = time.time()
    extract_snippet_news(news_results["allsongs"], g_query)
    logging.info("extract_snippet_news cost time: "+str(time.time()-t0))

    logging.info(news_results)

    logging.info("function searchResult return")
    return news_results

def get_more_results(count):
    logging.info("get the"+ str(count) + "page of doc results")
    display_soc = get_more_doc(count)
    print("count = ",count ," display_soc: ", display_soc)
    news_results = get_data_to_front_end(display_soc, count)
    return news_results

# ****************************************************************
# **********  search main function (interact with hello.py) ******
# ****************************************************************

def search_init(query, date):
    global doc_full_result
    global rank_score
    global index_cache
    global g_query
    global g_date
    global total_doc_number
    doc_full_result = []
    rank_score = []
    total_doc_number = -1
    # clear index cache everytime
    index_cache = {}
    # init query and date
    g_query = query
    g_date = date
    # set search date
    Set_search_date()

def search_thread(result_queue, query):
    time_start=time.time()

    info_queue = Queue()
    doc_info_load_thread = threading.Thread(target = get_all_doc_number_thread, args=(info_queue,))
    doc_info_load_thread.start()

    # begin search
    t0 = time.time()
    doc_search = Boolean_search(query, info_queue)
    logging.info("search complete, search time cost: " + str(time.time()-t0))

    # keep doc result in a global variable
    global doc_full_result
    global total_doc_number
    doc_full_result = doc_search
    total_doc_number = len(doc_full_result)

    if rank_method == RANK_BY_TFIDF:
        TFIDF_queue = Queue()
        thread_TFIDF = threading.Thread(target = calculate_TFIDF, args=(TFIDF_queue, query, time_start, doc_search))  # TFIDF score
        thread_TFIDF.start()
    else:
        BM25_queue = Queue()
        thread_BM25 = threading.Thread(target = BM25_rank, args=(BM25_queue, query, time_start, doc_search))  # TFIDF score
        thread_BM25.start()

    # if time limit occurs, two score will return ,the first one is used to rank the result and show
    # the second ont is to update the cache. we use final_result to check whether two result will return
    for count in range(2):
        logging.info("wait for BM25 run count :" + str(count))
        t0 = time.time()
        if rank_method == RANK_BY_TFIDF:
            score, final_result = TFIDF_queue.get()
        else:
            score, final_result = BM25_queue.get()
        if count == 0:
            logging.info("rank time cost:" + str(count))
        # keep rank score result in a global variable
        global rank_score
        if rank_score == []:
            rank_score = score

        display_soc = []
        if score != []:
            display_soc = get_more_doc(0)
        else:
            display_soc = doc_search[0: min(MAX_DOC_SHOW, len(doc_search))] # this means TFIDF was not been calculated because of time limit
        # queue is empty, which means search is faster than cache
        if count == 0 and result_queue.empty() == 1:
            logging.info("search complete by searching, not from cache")
            result_queue.put((display_soc, total_doc_number))
        # save search result in cache, it means TFIDF has been calculated completely, this thread can be stopped 
        if final_result == True:
            logging.info("save chache")
            ttds_cache.save_cache(query, (display_soc, total_doc_number))
            break

def clear_g_count():
#     global g_count
    logging.info("clear_g_count")
#     g_count = 0

#search news by date
# count = 0 means first call search_main, count > 0 means users click "more"
def search_main(query, date):

    t0 = time.time()
    logging.info("function searchResult")
    logging.info(query)
    # search init, clear cache
    search_init(query, date)

    search_result_queue = Queue()
    thread_search = threading.Thread(target=search_thread, args=(search_result_queue, query))   # search reusult
    thread_cache = threading.Thread(target=ttds_cache.cache_thread, args=(search_result_queue, query))  # find reusult in cache
    thread_search.start()
    thread_cache.start()

    logging.info("wait for results")
    t0 = time.time()
    global total_doc_number
    (display_soc, total_doc_number) = search_result_queue.get()
    logging.info("get results, time cost:"+str(time.time()-t0))

    logging.info(display_soc)
    t0 = time.time()
    news_results = get_data_to_front_end(display_soc)
    logging.info("test time 2:"+str(time.time()-t0))
    logging.info("the total search time: "+ str(time.time() - t0))

    return news_results