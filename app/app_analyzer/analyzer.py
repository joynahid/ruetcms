import re, json, requests, csv, random, math
import firebase_admin, os
from firebase_admin import firestore

db = firestore.client()

def req(api_method, renew=False):
    print('requesting- ', api_method)
    try:
        if renew:
            raise

        with open(f'./cache/{api_method}.json', 'r') as cache:
            return json.loads(cache.read())
    except:
        response = requests.get(f'https://codeforces.com/api/{api_method}')
        return json.loads(response.text)

user = {}

def getCfContestInfo(arr):
    docs = db.collection(u'profiles').stream()

    shandles=''
    handles=[]
    f= 1
    for doc in docs:

        D = doc.to_dict()

        user[D['cf']] = D['username']
        user[D['vj']] = D['username']
        user['username'] = [D['cf'], D['vj']]

        if f:
            f+=1
            shandles = doc.to_dict()['cf']
        else:
            shandles= shandles + ';'+ doc.to_dict()['cf']

        handles.append(doc.to_dict()['cf'])

    # db.child('contests').child('codeforces').remove()

    if not arr: return {}

    cf = {}
    cfInfo = {}

    for i in handles:
        cf.update({i : i})

    for each in arr:
        row = req(f'contest.standings?contestId={each}&handles={shandles}', False)

        if row['status'] != 'OK': continue

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

vjudge = {}

def generateVjudgeList():
    docs = db.collection('vjudgeContests').stream()

    for doc in docs:
        data = doc.to_dict()

        ins = []
        for each in data['ranks']:
            if each['vj'] in user:
                ins.append(
                    {
                        'person': user[each['vj']],
                        'solved': each['solved'],
                        'penalty' : each['penalty']
                    }
                )
            vjudge.update({
                str(doc.id) : ins
            })

def generateFavorite(vjcontests, cfcontests):

    data = getCfContestInfo(cfcontests)
    generateVjudgeList()

    for each in vjcontests:
        if str(each) not in vjudge: continue
        genVjList = vjudge[str(each)]

        for i in genVjList:
            tmpdata={
                i['person'] : {
                    'solved': i['solved'],
                    'penalty': i['penalty']*60,
                    'person' : i['person']
                }
            }

            if i['person'] in data:
                data[i['person']]['solved'] += i['solved']
                data[i['person']]['penalty'] += i['penalty']

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

# generateFavorite([376797],None)

def generateContestPerformance(contestId):
    docs = db.collection(u'profiles').stream()

    shandles=''
    handles=[]

    USERNM = {}

    f=False
    for doc in docs:
        handle = doc.to_dict()['cf']
        shandles= shandles + ';' + handle if f else '' + handle
        f=True
        USERNM.update({handle : doc.id})
        handles.append(handle)

    cf = {}

    for i in handles:
        cf.update({i : i})

    print(cf)

    contestant = []

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

    print(finalres)
    
    return finalres

# generateContestPerformance(1400)

def generateContestPerformanceCombined(contest, weight):
    data = {}
    sz = len(contest)

    sum=0

    for i in range(sz):
        getOne = generateContestPerformance(contest[i]) # id, capability, time
        sum+=weight[i]
        for j in getOne:
            if j['id'] in data:
                data[j['id']]['capability']+= j['capability']*weight[i]
                data[j['id']]['time']+= j['time']*weight[i]

            else:
                tmp = {
                    j['id'] : {
                        'id' : j['id'],
                        'capability' : j['capability']*weight[i],
                        'time' : j['time']*weight[i]
                    }
                }

                data.update(tmp)

    # print(sum)

    for i in data:
        data[i]['capability']=round(data[i]['capability']/sum,2)
        data[i]['time']=round(data[i]['time']/sum, 2)
    
    # print(data)

    ret = []

    for i in data:
        ret.append(data[i])

    ret = sorted(ret, key = lambda i: (i['capability'], -i['time']),reverse = True)
    
    return ret

# generateContestPerformanceCombined([1303,1295],[50,32])
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