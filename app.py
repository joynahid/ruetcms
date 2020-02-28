from flask import *
import requests, re, pyrebase,json,bcrypt, os, time
from judge import judge
from werkzeug.utils import *
from flaskext.mysql import MySQL
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_weasyprint import HTML, render_pdf

SESSION_TYPE = 'redis'

UPLOAD_FOLDER = 'path/to/the/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'cpp', 'csv'}

app = Flask(__name__, template_folder='templates')

app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'ruetcms'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'dfer34342rfs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

mysql = MySQL(app)
bcrypt = Bcrypt(app)

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

cfcolor = {
    'specialist': '#38D7FF',
    'pupil': 'green',
    'newbie': '',
    'expert': 'blue',
    'candidate master': 'purple',
    'legendary grandmaster':'red'
}

def Auth():
    if session.get("id") == None:
        return None

    con = mysql.connect()
    cursor = con.cursor()
    cursor.execute(f'''SELECT * FROM accounts WHERE id = {session.get("id")}''')
    all = cursor.fetchone()
    cursor.execute(f'''SELECT * FROM ojinfo WHERE id = {session.get("id")}''')
    alloj = cursor.fetchone()
    cursor.close()

    # print(alloj)

    currentUserInfo = {

    	'personal' : {
	    	'username' : all[1],
	    	'firstname' : all[2],
	    	'lastname' : all[3],
	    	'email' : all[4],
	    },

    	'ojinfo' : {
    		'codeforces': alloj[1],
    		'vjudge': alloj[2],
    	}
    }

    return currentUserInfo

# @app.route('/hello_<name>.pdf')
# def hello_pdf(name):
#     return render_pdf(url_for('hello_html', name=name))

def req(api_method, renew=False):
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


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ranklist Generator (VJUDGE + CODEFORCES)
@app.route('/generate_ranklist', methods=['GET','POST'])
def generate_ranklist():
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

			from analyzer import generateFavorite

			res = generateFavorite(vjcontests,cfcontests)

			flash(f'Ranklist generated successfully! ({(time.time() - start_time)} seconds)', 'success')
			return render_template('list.html', auth = Auth(), res = res, arr= contests)
		return "Invalid Request"

# Manager Page
@app.route('/manager', methods=['GET', 'POST'])
def manager():
    session.pop('_flashes',None)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return render_template('manager.html', auth = Auth(), available_contest = db.child('contests').child('vjudge').get().val())
        file = request.files['file']

        if request.form['filename'] == '':
            flash('No selected file', 'danger')
            return render_template('manager.html', auth = Auth(), available_contest = db.child('contests').child('vjudge').get().val())

        file.filename = 'vjudge_rank_' + request.form['filename'] + '.csv'

        db.child('contests').child('vjudge').set(request.form['filename'])

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Successfully updated.', 'success')
            return render_template('manager.html', auth = Auth(), available_contest = db.child('contests').child('vjudge').get().val())

    auth = Auth()

    if auth == None:
        flash('You must login first', 'warning')
        return redirect(url_for('login'))

    return render_template('manager.html', auth = auth, available_contest = db.child('contests').child('vjudge').get().val())

# def codeforcesManager():
#     session.pop('_flashes',None)

#     if Auth() == False:
#         flash('You must login first!')
#         return redirect(url_for('login'))

#     if request.method == 'GET':
#     	arr = list(map(int,request.args.get().strip().split()))

#     	import analyzer

#     	upDateCfContests(arr)

#     return render_template('codeforces.html')


# 404 Page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

# @app.route('/judgeme')
# def jdge():
#     judge('''#include <bits/stdc++.h>
# 	using namespace std;

# 	int main()
# 	{
# 		int x;
# 		cin >> x

# 		cout << x << endl;

# 		return 0;
# 	}''', '20')
#     return "done"

# CODEFORCES Information grabber
def getcfinfo(handle):
    user = req(f'user.info?handles={handle}', False)
    return user['result'][0]

# def cfCcontestAnalysis():
#     response = req('contest.list?gym=false')

#     # 20 iterations
#     for i in response['result']:
#         if i['type'] == 'CF' and i['phase'] == 'FINISHED':
#             cId = i['id']
#             break

#     sql = '''SELECT handle_cf FROM ojinfo'''
#     con = mysql.connect()
#     cursor = con.cursor()
#     cursor.execute(sql)
#     data = cursor.fetchall()
#     con.commit()
#     cursor.close()
#     handles = []

#     for i in data:
#     	handles.append(i[0])

#     contestant = []

#     # O(n) //time consuming
#     for handle in handles:
#         row = req(f'contest.standings?contestId={cId}&handles={handle}', False)

#         try:
#             data = {
#                 'handle': handle,
#                 'contest': row['result']['contest']['name'],
#                 'rank': row['result']['rows'][0]['rank'],
#             }

#             contestant.append(data)
#         except:
#             continue

#      O(n) // time consuming
#      for i in response['result']['rows']:
#          row = i['party']
#          handle = row['members'][0]['handle']
#          user = getcfinfo(handle)
#          try:
#          	if user['organization'].find('RUET') != -1 or (user['organization'].find('Rajshahi') != -1 and user['organization'].find('Engineering') != -1):
#          		contestant.append({
#          			'handle': user['handle'],
#          			'solved': len(row['problemResults']),
#          			'global-rank': row['rank']
#          			})
#          except: continue

#     return contestant


# Index Page
@app.route('/')
def index():
    if session.get('id'):
        auth = Auth()
        gen = getcfinfo(auth['ojinfo']['codeforces'])
        color = gen['maxRank']

        return render_template('home.html', auth=auth, user=auth['ojinfo']['codeforces'], info=gen, color=cfcolor[color])

    return redirect(url_for('login'))

@app.route('/performance', methods= ['GET',  'POST'])
def performance():

    if request.args.get('contestid'):
        from analyzer import generateContestPerformance
        res = generateContestPerformance(request.args.get('contestid'))

        return jsonify(res)

    auth= Auth()

    if auth == None:
        flash('You must login first', 'warning')
        return redirect(url_for('login'))
    
    return render_template('performance.html', auth=auth)

@app.route('/home')
def home():
    return index()


# Login Page Controller
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''

    if session.get('user'):
        return redirect(url_for('home'))

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        con = mysql.connect()
        cursor = con.cursor()

        validate_username = cursor.execute(f'''SELECT password FROM accounts WHERE username = "{username}"''')

        if not validate_username:
            flash('''User doesn't exist!''', 'danger')
            return render_template('login.html', notification = msg)

        hashed_password = cursor.fetchone()[0]

        con.commit()
        cursor.close()

        if bcrypt.check_password_hash(hashed_password, password):
            con = mysql.connect()
            cursor = con.cursor()

            cursor.execute(f'''SELECT id FROM accounts WHERE username = "{username}"''')
            getid = cursor.fetchone()[0]

            con.commit()
            cursor.close()
            session['id'] = getid
            session['user'] = username

            msg = 'Login Successful'
            return redirect(url_for('home'))
        else:
            flash('''Alas! You've entered wrong password''', 'danger')

    elif request.method == 'POST':
    	flash('Every field should be filled', 'warning')

    return render_template('login.html')


# Registration Controller
@app.route('/register', methods=['GET', 'POST'])
def register():
    session.pop('_flashes', None)
    msg = ''

    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and 'cfhandle' in request.form and 'firstname' in request.form and 'lastname' in request.form:
        username = request.form['username']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        password = request.form['password']
        email = request.form['email']
        cfhandle = request.form['cfhandle']
        vjhandle = request.form['vjhandle']

        hashed_password = bcrypt.generate_password_hash(password)

        con = mysql.connect()
        cursor = con.cursor()

        sql = f'''SELECT username FROM accounts WHERE username = "{username}"'''
        validate_username = cursor.execute(sql)

        if validate_username:
            flash('''User might already exist with this username!''', 'danger')
            return render_template('register.html', notification='')

        sql = f'''INSERT INTO accounts VALUES (NOT NULL, "{username}","{firstname}","{lastname}","{email}","{hashed_password}")'''
        ret = cursor.execute(sql)
        con.commit()

        cursor.execute(f'''SELECT id FROM accounts WHERE username = "{username}"''')
        getid = cursor.fetchone()[0]

        sql = f'''INSERT INTO ojinfo (id,handle_cf, handle_vjudge) VALUES ({getid}, "{cfhandle}", "{vjhandle}")'''
        cursor.execute(sql)
        con.commit()
        cursor.close()

        flash(f'''Hi {firstname}, your registration is successful!''', 'success')

        return redirect(url_for('login', notification=msg))

    return render_template('register.html', notification=msg)


# Logout Controller
@app.route('/logout')
def logout():
    try:
        session.pop('_flashes', None)
        flash(f'''Good Bye {Auth()['personal']['firstname']}''','success')
        session.get('user')
        session.pop('id', None)
        session.pop('user', None)
        return redirect(url_for('login'))
    except:
    	return "Wrong"


# @app.route('/profile', methods=['GET'])
# def profile():
#     username = request.args.get('name')
#     return jsonify(scrape(username))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))