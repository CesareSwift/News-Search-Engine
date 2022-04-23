import re
from nltk.stem.porter import PorterStemmer

# ************************************************************************************************
# ********** preprocess part (remove stopwords, punctuation and stemming) ************************
# ************************************************************************************************

def tokenisation(data):
    
    part = r'\w+'
    return [word.replace('_',' ') for word in re.findall(part,data)]


def stoppingremove(data):
    stop_words = []
    path4 = "englishST.txt"
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

# preprocess function, remove punctuation,  stopwords and stemming
def preprocess(data, remove_stop_flag = 1, stemming_flag = 1):

    data = tokenisation(data)  # Remove punctuation

    if remove_stop_flag == 1:
        data = stoppingremove(data)   # remove stopwords

    if stemming_flag == 1:
        data = normalisation(data) # stem
    
    # Concatenate the words in the list into strings with spaces as intervals
    output = (" ".join('%s' %id for id in data))
    
    return output


#*********** query process (process "AND" "OR" "NOT" operator (Boolean queries), process "#" operator (Proximity search))******

# if flag == 0, considering phrase search, it is used for Boolean search, Phrase search and Proximity search
# if flag == 1, ignore phrase search, it is used to caculate TFIDF and generate results.ranked.txt
def preprocess_query(query, rank_flag):
    
    and_data=[]
    or_data=[]
    not_data=[]
    phrase_temp = [] # for keeping phrase as a temp value

    #if Proximity_distance == -1, it means phrase search (defualt value)
    query, Proximity_distance = Proximity_Query_Process(query)

    pre_data = query.split()
    
    end_flag = "OR"
    for i in range(len(pre_data)):
        if pre_data[i] != "AND" and pre_data[i] != "OR" and pre_data[i] != "NOT":
            temp = preprocess(pre_data[i])
            if temp == '':
                continue
            if rank_flag == 0:
                phrase_temp.append(temp)
            elif rank_flag == 1:
                phrase_temp.append(temp)
                or_data.append(phrase_temp)
                phrase_temp = []
        if phrase_temp != [] and pre_data[i] == "AND":
            and_data.append(phrase_temp)
            phrase_temp = []
            end_flag = "AND"
        if phrase_temp != [] and pre_data[i] == "OR":
            or_data.append(phrase_temp)
            phrase_temp = []
            end_flag = "OR"
        if pre_data[i] == "NOT":
            phrase_temp = []
            end_flag = "NOT"
            
    # add the end phrase to data list
    if end_flag == "AND":
        and_data.append(phrase_temp)
    elif end_flag == "OR" and rank_flag == 0:
        or_data.append(phrase_temp)
    elif end_flag == "NOT":
        not_data.append(phrase_temp)

    return and_data, or_data, not_data, Proximity_distance

def preprocess_query_for_rank(query):
    # rank_flag mains preprocessing query for calculating TFIDF
    and_data, or_data, _, _ = preprocess_query(query, rank_flag = 1)
    
    sum_data = []
    
    for i in and_data:
        for j in i:
            if j not in sum_data:
                sum_data.append(j)
    for i in or_data:
        for j in i:
            if j not in sum_data:
                sum_data.append(j)
    
    return sum_data

# check whether it is proximity search query
def Proximity_Query_Process(query):
    Proximity_distance = -1
    simple_index = query.find("#")
    if simple_index == 0:
        begin_index = query.find("(")
        end_index = query.find(")")
        if begin_index > 1 and end_index > begin_index and query[begin_index+1: end_index].find(",") != -1\
            and query[simple_index + 1: begin_index].isdigit() == 1:
            Proximity_distance = int(query[simple_index + 1:begin_index])
            query=query[begin_index+1:end_index].replace(","," ").replace("\"","")
    return query, Proximity_distance