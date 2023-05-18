import os
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import sqlite3
import requests
import socket
import json



basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    searchItem = db.Column(db.String(100), nullable=False)
    searchResult = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return f'<Search {self.searchItem}'

def delete(sqlCommand):
    try:
        sqliteConnection = sqlite3.connect('database.db')
        cursor = sqliteConnection.cursor()
        
        cursor.execute(sqlCommand)

        sqliteConnection.commit()

        cursor.close()

    except sqlite3.Error as error:
        print("Failed to delete record from a sqlite table", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()


def apiRequest(searchInput):
    url = "https://newsapi.org/v2/everything?q="+(searchInput)+"&language=en&searchIn=title,description&sortBy=relevancy&pageSize=1&apiKey=6f834625ec594bcf8cfb1319736b815a" 
    try:
        uResponse = requests.get(url)
    except request.ConnectionError:
        return "Connection Error"
    Jresponse = uResponse.text
    data = json.loads(Jresponse)

    result = data['totalResults']

    if (result != 0):
        title = data['articles'][0]['title']
        return title

    return result


def arduinoRequest(searchInput):
        UDP_IP = '10.1.57.106'
        UDP_PORT = 2390
        title = apiRequest(searchInput)
        MESSAGE = (title)
        
        sock = socket.socket(socket.AF_INET, 
                      socket.SOCK_DGRAM)
        sock.connect((UDP_IP, UDP_PORT))
        sock.sendto(bytes(MESSAGE, "utf-8"), (UDP_IP, UDP_PORT))
            
            
            

@app.route('/', methods=['POST', 'GET'])
def index():
    delete("""DELETE FROM Search WHERE ROWID IN (SELECT ROWID FROM Search ORDER BY ROWID DESC LIMIT -1 OFFSET 3)""")
    searches = Search.query.all()

    if request.method == 'POST':
        searchItem = request.form['search']
        searchResult = apiRequest(searchItem)
        if (searchResult != 0):
            search = Search(searchItem=searchItem,
				searchResult=searchResult)
            db.session.add(search)
            db.session.commit()    
        
            latestSearch = Search.query.order_by(-Search.id).first()
            arduinoRequest(latestSearch.searchItem)
        
        return redirect(url_for('index'))
        
    return render_template('index.html', searches = searches)

if __name__ == '__main__':
    app.run(debug=True, port=5500, host='0.0.0.0')


