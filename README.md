# TTDS News Search IR Project 2021

This is a group project for the course [TTDS](https://www.inf.ed.ac.uk/teaching/courses/tts/) (Text Technologies for Data Science) at the University of Edinburgh. 



### Summary

The news search engine is a website that provide  users a way of searching relevant news from incomplete news title. Given a query, it returns  the most relevant news. The collection of documents contains 8.8GB news from kaggle. It uses  a multi-level inverted index occupying 5.92GB  on disk. The ranking algorithm uses BM25 for  phrase search. Instead of searching certain type  of news, the website can also perform a search  for all most relevant news to the query using  weighted BM25 algorithm. It also contains advanced search features, such as search based on  date. The website can be reached from this link:  35.184.241.193:5000/search



### Installation

You need to have Python 3 installed.

Create a local environment and install the requirements:env/Scripts/activate

```
env/Scripts/activate
FLASK_APP=hello.py
pip install requirement.txt
flask run
```




