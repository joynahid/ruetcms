from datetime import datetime
from requests_html import HTMLSession
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app, auth
import sys

session = HTMLSession()
cred = credentials.Certificate("./firebasedb/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def insertVjInfo(id):
    id = str(id)
    selfid = ''
    for i in id:
        if i.isdigit():
            selfid+=i
    
    selfid = int(selfid)
    uri = f'https://vjudge.net/contest/{selfid}#rank'
    selfdoc = session.get(uri)

    selfdoc.html.render()

    title = selfdoc.html.find('title')[0].text
    author = selfdoc.html.find('#contest-manager > a')[0].text
    query = '#contest-rank-table > thead:nth-child(2) > tr:nth-child(1) > th'
    numOfProblems = len(selfdoc.html.find(query)) - 4

    fetchRank = selfdoc.html.find('#contest-rank-table > tbody > tr')
    ranks = []

    for person in fetchRank:
        p = person.text.split('\n')

        data = {
            'serial' : int(p[0]),
            'vj' : p[1].split(' ')[0],
            'solved' : int(p[2]),
            'penalty' : int(p[3].split(' ')[0]),
        }

        ranks.append(data)
    
    ret = {
        'title' : title,
        'author' : author,
        'numOfProblems': numOfProblems,
        'ranks' : ranks
    }

    print(ret)

    db.collection('vjudgeContests').document(str(selfid)).set(ret)

if __name__ == '__main__':
    globals()[sys.argv[1]](sys.argv[2])