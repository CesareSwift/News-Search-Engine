import pandas as pd
import csv

dict1 = {'0','1','2','3','4','5','6','7','8','9','f'}
def clearBlankLine(path1 ,path2):
    file = open(path1, 'r', encoding='utf-8')
    file2 = open(path2, 'a+', newline='', encoding='utf-8')
    for line in file.readlines():
        if line[0] in dict1:
            file2.write(line)


if __name__== '__main__':
    path1 = R'D:\data_process\all-the-news-2-1\all-the-news-2-1.csv'
    path2 = R'D:\data_process\all-the-news-2-1\pre.csv'
    clearBlankLine(path1 ,path2)