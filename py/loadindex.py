from re import I
import pprint
import sys
import csv
csv.field_size_limit(sys.maxsize)

def get_database(db_name):
    from pymongo import MongoClient
    import pymongo

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    #CONNECTION_STRING = "mongodb+srv://ttds_cw3:ttds_cw3@cluster0.ljnhy.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    from pymongo import MongoClient
    #client = MongoClient(CONNECTION_STRING)
    client = MongoClient('127.0.0.1', 27017)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client[db_name]

# Read inverted index
def loadindex(ttds_db, index_path, Frist=True):
    index = {}
    i = -1
    with open(index_path, 'r', encoding='utf-8') as f:
        #lines = f.readlines()
        line = f.readline()
        #for line in lines: 
        while line:
            try:
                if (line[0] != '\t' and  line[0] != '\n'):
                    word = line[:line.find(':')]
                    #print(word)
                    i += 1
                    if int(i)%10000 == 0 and i != 0:
                        print(i, word)
                        if Frist and int(i) == 10000:
                            insert_indexes(ttds_db, index, "index")
                        else:
                            insert_indexes(ttds_db, index, "index", False)
                        index = {}
                        index[word] = {}
                    else:
                        index[word] = {}
                        
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
                print("error")
                break
        insert_indexes(ttds_db, index, "index", False)
    #return index

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

def insert_news(ttds_db, csv_path):
    import csv
    import re
    news = {}
    csv_reader = csv.reader(open(csv_path))
    collection_name = ttds_db["news"]
    print("*********** Processing on NEWS *************")
    i = 0
    for line in csv_reader:
        if i%10000 == 0:
            print("DONE:" + str(i)) 
        news[str(i)] = {}
        
        news[str(i)]['date'] = line[1]
        authors = line[2].split(', ')
        if authors[0] == "":
            news[str(i)]['authors'] = []
        else:
            news[str(i)]['authors'] = authors
        news[str(i)]['title'] = line[3]
        news[str(i)]['article'] = line[4]
        news[str(i)]['url'] = line[5]
        #pprint.pprint(news)
        news_info = news[str(i)]
        news_info["_id"] = i
        collection_name.insert_one(news_info)

        i += 1

def insert_word_index(collection_name, words, init_num):
    i = init_num
    for word in words:
        #pprint.pprint(word)
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
            dict1,dict2 = separate(word[1])
            word_list.append((word[0], dict1))
            word_list.append((word[0], dict2))
            i = insert_word_index(collection_name, word_list, i)
            print('separate doc number: ' + str(i))
    return i

 
def insert_indexes(ttds_db, index_csv, index_name, first=True):
    collection_name = ttds_db[index_name]
    if first:
        i = 0
    else:
        last_index = collection_name.find().sort('_id',-1).limit(1)
        for index in last_index:
            #pprint.pprint(news)
            i = index['_id'] + 1
    print('start number: ' + str(i))
    for word in index_csv.items():
        word_list = [word]
        i = insert_word_index(collection_name, word_list, i)

if __name__ == '__main__':
    news_path = sys.argv[1]
    index_path = port = sys.argv[2]
    db_name = 'ttds'
    ttds_db = get_database(db_name)
    #ttds_db['news'].drop()
    '''
    index_csv = loadindex('index.txt')
    insert_index(ttds_db, index_csv, "index_lyrics")
    print("***************** DONE INDEX LYRIC ********************")

    index_csv = loadindex('index_name.txt')
    insert_index(ttds_db, index_csv, "index_names")
    print("***************** DONE INDEX NAME ********************")

    lyrics_csv = load_lyrics('output_lyric.csv')
    insert_lyrics(ttds_db, lyrics_csv)
    print("***************** DONE LYRICS ********************")

    artists_csv = load_artist('artists-data.csv')
    insert_artist(ttds_db, artists_csv)
    print("***************** DONE ARTISTS ********************")

    #update_lyrics_genre(ttds_db)

    '''

    insert_news(ttds_db, news_path)

    # insert the first index file
    loadindex(ttds_db, index_path)
    #index_csv = {}
    #index_csv['000000000000000011'] = {'1999':[0,12]}
    #print("***************** DONE INDEX 0 ********************")
    '''
    # insert the following index files
    index_csv = loadindex('dataset/indexes/index1.txt', False)
    insert_indexes(ttds_db, index_csv, "index", False)
    print("***************** DONE INDEX ********************")
    '''
