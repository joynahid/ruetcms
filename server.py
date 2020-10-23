from dotenv import load_dotenv
load_dotenv()
from flask import *
import requests, json, os, time
from firebase_admin import firestore
import firebase_admin
from app.app_machine import vjudge_driver
import subprocess
from app.app_auth.auth import app_auth, db, Authenticate
from app.app_analyzer.analyzer import generateFavorite, generateContestPerformanceCombined
from app.blog.blog import blog
from network.clist_api import clistApi
from datetime import datetime as dt

app = Flask(__name__, template_folder='templates')
app.config.from_pyfile('config.py')

# Blueprints
app.register_blueprint(app_auth)
app.register_blueprint(blog, url_prefix = '/blog')

# Index Page
@app.route('/')
def index():
    if Authenticate():
        return render_template('home.html', vjContest = vjudge_driver.vjInfoQuery(db), user=session['userHandle'])

    return render_template('home.html', vjContest = vjudge_driver.vjInfoQuery(db))

def req(api_method):
    response = requests.get(f'https://codeforces.com/api/{api_method}')
    return jsonify(response.text)

# Ranklist Generator (VJUDGE + CODEFORCES)
@app.route('/generate_ranklist', methods=['GET','POST'])
def generate_ranklist():
    if not Authenticate():
        return redirect(url_for('app_auth.login'))

    if request.args.get('listcf') or request.args.get('listvj'):
        start_time = time.time()

        vjcontests = list(map(int,request.args.get('listvj').strip().split()))
        cfcontests = []

        if request.args.get('listcf'):
            cfcontests = list(map(int,request.args.get('listcf').strip().split()))

        contests = {
            'vjudge': vjcontests,
            'codeforces' : cfcontests
        }

        res = generateFavorite(vjcontests,cfcontests)

        flash(f'Ranklist generated successfully! ({round((time.time() - start_time),2)} seconds)', 'success')
        return render_template('list.html', res = res, arr= contests, user = session['userHandle'])
    
    return "Invalid Request"

# Manager Page
@app.route('/manager', methods=['GET', 'POST'])
def manager():
    if request.method == 'GET' and request.args.get('cids'):
        if not Authenticate():
            flash('You must login first', 'warning')
            return redirect(url_for('app_auth.login', next = url_for('manager')))

        cids = request.args.get('cids')
        cids = cids.split(' ')

        ins_id = None
        for id in cids:
            if id:
                ins_id = id
                vjudge_driver.insert(id, db)
                break
        
        flash(f'Successfully inserted {ins_id} into Database. +1 for your contribution was added','success')
        return render_template('manager.html', user= session['userHandle'])

    if Authenticate():
        return render_template('manager.html', user= session['userHandle'])
        
    return render_template('manager.html')

# 404 Page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', noauth = 1)

@app.route('/performance', methods= ['GET',  'POST'])
def performance():
    # print(request.args.get('contestid'))
    if request.args.get('contestid') and request.args.get('weight'):

        res = list(map(int,request.args.get('contestid').strip().split()))
        reswt = list(map(int,request.args.get('weight').strip().split()))

        # print(res, reswt)

        if len(res)!=len(reswt):
            jsonify({'error':'Wrong format! You must give contest ID and weight accordingly'})

        fres = generateContestPerformanceCombined(res,reswt)

        # print(fres)

        return jsonify(fres)
    
    # flash("This is not working right now. I'm working to fix it", 'danger')

    if Authenticate(): return render_template('performance.html', user = session['userHandle'])
    return render_template('performance.html')

import datetime, time

@app.route('/profile/<username>')
def profile(username):
    if Authenticate():
        profile = None

        if session['userHandle']['username'] == username: profile = session['userHandle']
        else: profile  = db.collection('profiles').document(username).get().to_dict()

        if not profile:
            return redirect('/404')

        return render_template('profile.html',user=session['userHandle'], profile = profile)

    profile=db.collection('profiles').document(username).get().to_dict()
    if not profile:
            return redirect('/404')

    return render_template('profile.html', profile=profile)

@app.route('/vj/listdata')
def vjudgeContestListData():
    docs = db.collection('vjudgeContests').stream()

    data = []

    for doc in docs:
        jData = doc.to_dict()
        jData.update({'id': doc.id})
        data.append(jData)
    
    return jsonify(data)

@app.route('/halloffame')
def hallOfFame():
    return render_template('halloffame.html', noauth = 1)

@app.route('/vj/list')
def vjudgeList():
    if Authenticate():
        return render_template('vjudgelist.html', user = session['userHandle'])
    
    return render_template('vjudgelist.html')

@app.route('/api/v1/upcomingcontests')
def upcomingContest():
    try:
        FILTER_CONTEST_SITE = ['codeforces', 'toph', 'topcoder', 'codechef', 'atcoder','leetcode','hackerrank']
        MAX_DURATION = 5*60*60 # Seconds

        processed_list = []

        data = clistApi.contests()

        for each in data['objects']:
            contest_data = {}

            time_now = dt.now()
            contest_start_time = dt.fromisoformat(each['start'])
            time_delta = (contest_start_time - time_now).total_seconds()

            delta_days = int(time_delta)//(24*60*60)
            rem_delta = int(time_delta)%(24*60*60)
            delta_hrs = rem_delta//(60*60)
            rem_delta = rem_delta%(60*60)
            delta_mins = rem_delta//60

            time_msg = ''

            if delta_days:
                time_msg+=str(delta_days) + ' days '
            if delta_hrs:
                time_msg+=str(delta_hrs) + ' hours '
            if delta_mins:
                time_msg+=str(delta_mins) + ' minutes'

            each['start'] = time_msg

            if time_delta < 0: break

            for i in FILTER_CONTEST_SITE:
                if i in each['href']:
                    each['href'] = each['href'].replace(
                        "http://", "https://")

                    if each['duration'] <= MAX_DURATION:
                        contest_data = {
                            'time_delta': time_delta,
                            'start': each['start'],
                            'name': each['event'],
                            'href': each['href'],
                        }

                if contest_data:
                    processed_list.append(contest_data)
                    break

        processed_list = sorted(processed_list, key=lambda i: i['time_delta'])
        processed_list = processed_list

        return jsonify(processed_list)

    except Exception as e:
        print("upcoming contest error", e)


@app.route('/upcoming_contests')
def upcomingContestPage():
    return render_template('upcoming_contests.html', user= session['userHandle'])

if __name__ == '__main__':
    app.run()