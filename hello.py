from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
import py.search
import py.predict
#import predict
app = Flask(__name__)

@app.route('/search', methods=['GET', 'POST'])
def search_page2():
    if request.method == 'POST':

        keyword = request.form.get('name')
        if keyword== 'query':
            k2 = request
            k2=str(k2)
            k3=(k2.split("="))[1]
            if '%' in k3:
                k3=k3.strip('%20')
                query=(k3.split("' ["))[0]
            else:
                query = (k3.split("' ["))[0]


            result=py.predict.text_generation(query)
            res2 = {"items": []}
            for i in result.values():
                res2["items"].append({"name": i})

            return res2
        else:
            keyword = request.form.get('keyword')
            enddate= request.form.get('end')
            stadate = request.form.get('star')
            
            if len(stadate) == 0:
                stadate = "January 1, 2000"
            if len(enddate) == 0:
                enddate = "December 30, 3000"

            month = {'January':'1','February':'2','March':'3','April':'4','May':'5',
                     'June':'6','July':'7','August':'8','September':'9','October':'10','November':'11','December':'12'}
            date=stadate.split(' ')[2]+'-'+month[stadate.split(' ')[0]]+';'+enddate.split(' ')[2]+'-'+month[enddate.split(' ')[0]]

            return redirect(url_for('result_page', keyword=keyword,date=date))
    return render_template('search.html')

@app.route('/result/?<string:keyword>/<date>', methods=['GET', 'POST'])
def result_page(keyword,date):
    if request.method == 'POST':
        num = request.form.get('number')
        print(num+"----------------------------")
        #print("more results-----------------------------------------------")
        #search.clear_g_count()
        result=py.search.get_more_results(int(num))
        #print(result)
        return result

    #print(request.form.get('suggest')+"oh noyees=======================================")
    #print(date,'in date')
    return render_template('result.html', songs=py.search.search_main(keyword,date))



