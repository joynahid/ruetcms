from flask import *
import requests, json, os, time
from firebase_admin import firestore
import firebase_admin
from app.app_machine import vjudge_driver
import subprocess
from app.app_auth.auth import app_auth, db, Authenticate

app = Flask(__name__, template_folder='templates')
app.config.from_pyfile('config.py')

print(app.config['SECRET_KEY'])

# Blueprints
app.register_blueprint(app_auth)

# Index Page
@app.route('/')
def index():
    if Authenticate():
        return render_template('home.html', vjContest = vjudge_driver.vjInfoQuery(db), user=session['userHandle'])

    return redirect(url_for('app_auth.login'))

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
    if not Authenticate():
        flash('You must login first', 'warning')
        return redirect(url_for('app_auth.login', next = url_for('manager')))

    if request.method == 'GET':
        if request.args.get('cids'):
            cids = request.args.get('cids')
            cids = cids.split(' ')

            for id in cids:
                if id:
                    vjudge_driver.insert(id, db)
                    # subprocess.run(f'python ./app/app_machine/insert.py insertVjInfo {id}', shell = True)
            
            flash('Successfully Inserted into Database. Thanks for your contribution','success')

    return render_template('manager.html', user = session['userHandle'])

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

    if not Authenticate():
        flash('You must login first', 'warning')
        return redirect(url_for('app_auth.login'))
    
    return render_template('performance.html', user = session['userHandle'])

import datetime, time

@app.route('/profile/<username>')
def profile(username):
    if 'userHandle' not in session:
        session['userHandle'] = db.collection('profiles').document(username).get().to_dict()
    return render_template('profile.html', user=session['userHandle'])

@app.route('/vj/listdata')
def vjudgeContestListData():
    if Authenticate():
        docs = db.collection('vjudgeContests').stream()

        data = []

        for doc in docs:
            jData = doc.to_dict()
            jData.update({'id': doc.id})
            data.append(jData)
        
        return jsonify(data)
    
    return 'No Worries'

@app.route('/fame')
def hallOfFame():
    return render_template('halloffame.html')

@app.route('/vj/list')
def vjudgeList():
    if Authenticate():
        return render_template('vjudgelist.html', user = session['userHandle'])
    
    return redirect(url_for('app_auth.login'))

if __name__ == '__main__':
    app.run(host='192.168.43.88')