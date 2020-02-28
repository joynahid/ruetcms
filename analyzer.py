import re
import math
import random
import csv
import pyrebase
from flask import *
import requests
import re
import pyrebase
import json
from flaskext.mysql import MySQL

app = Flask(__name__)

app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'ruetcms'

mysql = MySQL(app)

config = {
    "apiKey": "AIzaSyDyksjnMlbJ3oCEYa7WpTsNWG7YPepBOzc",
    "authDomain": "ruet-cms.firebaseapp.com",
    "databaseURL": "https://ruet-cms.firebaseio.com",
    "projectId": "ruet-cms",
    "storageBucket": "ruet-cms.appspot.com",
    "messagingSenderId": "99846446489",
    "appId": "1:99846446489:web:75dc39f7f83153219a8708",
    "serviceAccount": "path/to/ruet-cms-firebase-adminsdk-28ojp-8dda964f7e.json"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
bucket = firebase.storage()

def getVjudgeInfo(vjudgeid):

    vjudgeInfo ={}

    with open(f'path/to/the/uploads/vjudge_rank_{vjudgeid}.csv', mode = 'r') as vjudgeList:
        csvreader = csv.DictReader(vjudgeList)
        row = 0

        con = mysql.connect()
        cursor = con.cursor()

        for each in csvreader:
            if row == 0:
                lenth = len(each)-5
                row+=1
            else:
                vhandle = each["Team"].strip()
                start = vhandle.find( '(' )
                if start != -1:
                    vhandle = vhandle[:start-1]

                cursor.execute(f'SELECT handle_vjudge, username FROM ojinfo, accounts WHERE accounts.id = ojinfo.id AND handle_vjudge = "{vhandle}"')
                ret = cursor.fetchone()
                if ret == None: continue

                username = ret[1]
                time = each["Penalty"]

                hour = int(time[0]+time[1])
                minute = int(time[3]+time[4])
                second = int(time[6]+time[7])

                penalty = hour*60*60 + minute*60 + second

                data = {
                    username : {
                        'person' : username,
                        # 'rank' : int(each['Rank']),
                        'solved' : int(each['Score']),
                        'penalty' : penalty,
                    }
                }

                vjudgeInfo.update(data)

        return vjudgeInfo


def getCfContestInfo(arr):
    con = mysql.connect()
    cursor = con.cursor()
    cursor.execute('SELECT username, handle_cf FROM accounts, ojinfo WHERE accounts.id = ojinfo.id')
    res = cursor.fetchall()
    cursor.close()

    # db.child('contests').child('codeforces').remove()

    shandles=''

    cf = {}
    cfInfo = {}

    for i in res:
        cf.update({i[1] : i[0]})
        shandles= shandles+ ';' + str(i[1])

    for each in arr:
        row = req(f'contest.standings?contestId={each}&handles={shandles}', False)

        for i in row['result']['rows']:
            data={
                cf[i['party']['members'][0]['handle']] :{
                    'solved': int(i['points']),
                    'penalty': int(i['penalty'])*60,
                    'person' : cf[i['party']['members'][0]['handle']],
                    # 'rank' : i['rank']
                }
            }

            if cf[i['party']['members'][0]['handle']] in cfInfo:
                cfInfo[cf[i['party']['members'][0]['handle']]]['solved']+= data[cf[i['party']['members'][0]['handle']]]['solved']
                cfInfo[cf[i['party']['members'][0]['handle']]]['penalty']+= data[cf[i['party']['members'][0]['handle']]]['penalty']

            else: cfInfo.update(data)

    return cfInfo

def generateFavorite(vjcontests, cfcontests):

    data = getCfContestInfo(cfcontests)

    for each in vjcontests:
        genVjList = getVjudgeInfo(each)

        for i in genVjList:
            tmpdata={
                i : {
                    'solved': genVjList[i]['solved'],
                    'penalty': genVjList[i]['penalty']*60,
                    'person' : i
                }
            }

            if i in data:
                data[i]['solved'] += genVjList[i]['solved']
                data[i]['penalty'] += genVjList[i]['penalty']

            else: data.update(tmpdata)
    
    datas = []
    for i in data:
        data[i]
        datas.append(data[i])

    datas = sorted(datas, key = lambda i: (i['solved'], -i['penalty']),reverse = True)
    
    for i in range(len(datas)):
        datas[i].update({'position': i+1})

    print(datas)

    return datas

def req(api_method, renew=False):
    print('requesting- ', api_method)
    try:
        if renew:
            raise

        with open(f'./cache/{api_method}.json', 'r') as cache:
            return json.loads(cache.read())
    except:
        response = requests.get(f'https://codeforces.com/api/{api_method}')
        with open(f'./cache/{api_method}.json', 'w') as cache:
            cache.write(response.text)
        return json.loads(response.text)

def generateContestPerformance(contestId):

    con = mysql.connect()
    cursor = con.cursor()
    cursor.execute('SELECT id,handle_cf FROM ojinfo')
    res = cursor.fetchall()
    cursor.close()

    shandles=''
    contestant = []
    cf = {}
    cfInfo = {}

    for i in res:
        cf.update({i[1] : i[0]})
        shandles= shandles+ ';' + str(i[1])

    # print(cf)

    rows = req(f'contest.standings?contestId={contestId}&handles={shandles}', False)

    numOfProblems = len(rows['result']['problems'])

    for i in rows['result']['rows']:
        problems = [0 for x in range(numOfProblems)]
        solved = [0 for x in range(numOfProblems)]
        
        ind=0
        for j in i['problemResults']:
            if j['points']:
                solved[ind] = 1
                problems[ind]=(j['bestSubmissionTimeSeconds'] + j['rejectedAttemptCount']*20)
                ind+=1
       
        data = {
            'id' : cf[i['party']['members'][0]['handle']],
            'solve' : solved,
            'penalty' : problems
        }

        contestant.append(data)
        
    n= len(contestant)

    dummy = {
        'id' : 0,
        'penalty' : [0 for i in range(numOfProblems)],
        'solve' : [0 for i in range(numOfProblems)]
    }

    res= {}

    for i in range(numOfProblems):
        for j in range(n): dummy['solve'][i] |= contestant[j]['solve'][i]
        if dummy['solve'][i] == 0: continue

        dummy['penalty'][i] = 1000000000

        for j in range(n):
            if contestant[j]['solve'][i]:
                dummy['penalty'][i] = min(contestant[j]['penalty'][i], dummy['penalty'][i])

    # print(dummy)

    con = mysql.connect()
    cursor = con.cursor()
    cursor.execute('SELECT id,username FROM accounts')
    userdata = cursor.fetchall()
    cursor.close()
    
    USERNM = {}

    for i in userdata:
        USERNM.update({i[0]:i[1]})

    for i in range(n):
        total_solve=0
        total_penalty=0
        b_sol=0
        b_pen=0

        for j in range(numOfProblems):
            b_sol+= dummy['solve'][j]

            if contestant[i]['solve'][j] == 0: continue
            b_pen += dummy['penalty'][j]
            total_solve+=1
            total_penalty+=contestant[i]['penalty'][j]

        data = {
            contestant[i]['id']:{
                'id' : USERNM[contestant[i]['id']],
                'capability': (total_solve / b_sol) * 100.00,
                'time': (total_penalty / b_pen) * 100.00
            }
        }
        res.update(data)

    finalres= []

    for i in res:
        finalres.append({
            'id': res[i]['id'],
            'capability':res[i]['capability'],
            'time':res[i]['time']
        })

    finalres = sorted(finalres, key = lambda i: (i['capability'], -i['time']),reverse = True)

    # print(finalres)

    return finalres
    

# generateContestPerformance(1303)
# generateFavorite([356330],[1303])
# generateFavorite([],[1303])

def eloprobablity(ra,rb):
    return 1.00/(1+pow(10.0, (rb-ra)/1000.00))
 
def getSeed(rating,currentRating,pos,n):
    ret=1.00
    for i in range(n):
        if i!=pos:
            ret+=eloprobablity(currentRating[i], rating)
    return ret
 
def getRating(rank,currentRating,pos,n):
    tmpgeomean=math.sqrt(rank[pos]*getSeed(currentRating[pos],currentRating,pos,n))
    lo=1
    hi=8000
    while hi-lo>1:
        mid=int(hi+lo)/2
        if getSeed(mid,currentRating,pos,n)<tmpgeomean:
            hi=mid
        else:
            lo=mid
    lo-=currentRating[pos]
    lo/=2
    lo=int(lo)
    return lo+currentRating[pos]

def calculate_rating(currentRating, rank, n, names):
    ret=[]
    for i in range(n):
        ret.append(getRating(rank,currentRating,i,n))

    return ret

def anaalyze(id):
    if doc == False: return False

    doc= BeautifulSoup(doc, 'html.parser')
    soup = doc.prettify()

    heads = doc.find('thead')
    heads= heads.find_all('th')

    ranks=[]
    rating=[random.randint(1,1200) for i in range(10000)]
    names=[]

    alldata= {}

    for tag in heads:
        res= tag.find('div')

    data = doc.find_all('tbody')

    for tr in data:
        info = tr.find_all('tr')

        for td in info:
            user = td.find_all('td')

            name=''
            rank=0
            solve=0
            penalty=''

            for dat in user:
                res= str(dat)

                if res.find('rank meta')!=-1:
                    rank=int(dat.text)
                elif res.find('team meta')!=-1:
                    name=dat.text
                elif res.find('solved meta')!=-1:
                    solve=int(dat.text)
                elif res.find('penalty meta')!=-1:
                    penalty=dat.text.replace(' ','').strip()
            if rank!=0:
                ranks.append(rank)
                names.append(name)

    ret = calculate_rating(rating,ranks, int(len(ranks)),names)
    alldata['name']=names
    alldata['prevRating']= rating
    alldata['ranks']=ranks
    alldata['curRating']=ret

    return alldata

# getvjudgeList(356330)

# ids = db.child('contests').child('vjudge').child('contestinfo').get()
# for i in ids.val():
#     print(i)

# d = map(int,input('Give Contest Ids').strip())

# generateFavorite([356330])