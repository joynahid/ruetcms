from flask import *
import requests, json, os, time
from firebase_admin import firestore
import firebase_admin
from app.app_machine import vjudge_driver
import subprocess
from app.app_auth.auth import app_auth, db, Authenticate

app = Flask(__name__, template_folder='templates')
app.config.from_pyfile('config.py')

# Blueprints
app.register_blueprint(app_auth)

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

        from app.app_analyzer.analyzer import generateFavorite

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
    return render_template('404.html')

@app.route('/performance', methods= ['GET',  'POST'])
def performance():
    # print(request.args.get('contestid'))
    if request.args.get('contestid') and request.args.get('weight'):

        from analyzer import generateContestPerformanceCombined

        res = list(map(int,request.args.get('contestid').strip().split()))
        reswt = list(map(int,request.args.get('weight').strip().split()))

        # print(res, reswt)

        fres = generateContestPerformanceCombined(res,reswt)

        # print(fres)

        return jsonify(fres)
    
    flash("This is not working. I'm working to fix it", 'danger')

    if Authenticate(): return render_template('performance.html', user = session['userHandle'])
    return render_template('performance.html')

import datetime, time

@app.route('/profile/<username>')
def profile(username):
    if Authenticate():
        return render_template(
            'profile.html',
            profile = session['userHandle'] if session['userHandle']['username'] == username else db.collection('profiles').document(username).get().to_dict(),
            user=session['userHandle']
        )

    return render_template('profile.html', profile=db.collection('profiles').document(username).get().to_dict())

@app.route('/vj/listdata')
def vjudgeContestListData():
    docs = db.collection('vjudgeContests').stream()

    data = []

    for doc in docs:
        jData = doc.to_dict()
        jData.update({'id': doc.id})
        data.append(jData)
    
    return jsonify(data)

@app.route('/fame')
def hallOfFame():
    return render_template('halloffame.html')

@app.route('/vj/list')
def vjudgeList():
    if Authenticate():
        return render_template('vjudgelist.html', user = session['userHandle'])
    
    return render_template('vjudgelist.html')

if __name__ == '__main__':
    app.run()