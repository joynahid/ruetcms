from flask import *
import datetime, json, time, requests
from firebase_admin import firestore, credentials, auth, initialize_app
import os

app_auth = Blueprint('app_auth', __name__, template_folder='templates', static_folder='/static')

cred = credentials.Certificate(os.environ['SERVICE_CREDENTIALS'])
initialize_app(cred)
db = firestore.client()

API_KEY = os.environ['API_KEY']

def Authenticate():
    print("Authenticating...")
    session_cookie = request.cookies.get('userSession')

    if not session_cookie or 'robot' not in session or 'userHandle' not in session:
        # Session cookie is unavailable. Force user to login.
        return False and redirect(url_for('app_auth.login'))

    try:
        print('Checking Cookiee...')
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
        return True
    except auth.InvalidSessionCookieError as e:
        print(e)
        return False and redirect(url_for('app_auth.logout'))
    except:
        return 'Something went wrong! Sorry for the inconvenience'

def session_login(id_token):
    try:
        decoded_claims = auth.verify_id_token(id_token)

        session['robot'] = decoded_claims

        if time.time() - decoded_claims['auth_time'] < 5 * 60:
            expires_in = datetime.timedelta(days=5)
            willexpire = datetime.datetime.now() + expires_in
            session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)

            print('url', request.args.get('next'))

            url = url_for('index')
            if request.args.get('next'):
                url = request.args.get('next')
            
            response = make_response(redirect(url))
            response.set_cookie('userSession', session_cookie)

            return response
            
        return redirect(url_for('app_auth.login'))
    except auth.InvalidIdTokenError:
        return abort(401, 'Invalid ID token')
    except:
        return abort(401, 'Failed to create a session cookie')

@app_auth.route('/auth/login', methods = ['GET','POST'])
def login():
    if Authenticate():
        return redirect(url_for('index'))

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        userInfo = db.collection('profiles').document(username).get().to_dict()

        if not userInfo:
            flash('Recheck Username','danger')
            return render_template('login.html')

        reqRef = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps(
            {
                "email": userInfo['email'],
                "password": password,
                "returnSecureToken": True
            }
        )  

        reqResponse = requests.post(reqRef, headers = headers, data = data)

        if 'error' in reqResponse.json():
            if reqResponse.json()['error']['message'] == 'EMAIL_NOT_FOUND':
                flash('Invalid Email','danger')
                return render_template('login.html')
            elif reqResponse.json()['error']['message'] == 'INVALID_PASSWORD':
                flash('Wrong Password','danger')
                return render_template('login.html')
            elif reqResponse.json()['error']['message'] == 'USER_DISABLED':
                flash('User is disabled by Admin','danger')
                return render_template('login.html')
            elif 'TOO_MANY_ATTEMPTS_TRY_LATER' in reqResponse.json()['error']['message']:
                flash('Too many attempts. Please try later','danger')

        session.permanent = True

        session['robot'] = reqResponse.json()
        session['userHandle'] = userInfo

        print('user robot', session['userHandle'])

        return session_login(reqResponse.json()['idToken'])

    elif request.method == 'POST':
    	flash('Every field should be filled', 'warning')

    return render_template('login.html')

@app_auth.route('/auth/register', methods = ['GET','POST'])
def register():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and 'cfhandle' in request.form and 'name' in request.form:
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cfhandle = request.form['cfhandle']
        vjhandle = request.form['vjhandle']

        try:
            auth.get_user_by_email(email)
            flash(f'''Already registered with this email''', 'danger')
            return render_template('register.html')
        except:
            pass

        userInfo = db.collection('profiles').document(username).get()

        if userInfo.exists:
            flash(f'''Already registered with this username''', 'danger')
            return render_template('register.html')

        user = auth.create_user(
            email= email,
            email_verified=False,
            password=password,
            display_name=name,
            photo_url='https://picsum.photos/300',
            disabled=False
        )

        db.collection('profiles').document(username).set({
            'username' : username,
            'cf' : cfhandle,
            'vj' : vjhandle,
            'email' : email,
            'name' : name,
        })

        flash(f'''Hi {name}, your registration is successful!''', 'success')

        return redirect(url_for('app_auth.login'))

    return render_template('register.html')

@app_auth.route('/auth/logout')
def logout():
    print('here')
    session['robot'] = ''
    session['userHandle'] = ''
    session['cfProfile']=''
    flash(f'''Good Bye! See ya soon''','success')
    response = make_response(redirect(url_for('app_auth.login')))
    response.set_cookie('userSession', expires=0)
    return response