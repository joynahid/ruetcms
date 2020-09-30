from flask import *
from firebase_admin import firestore
from app.app_auth.auth import Authenticate
import os

blog = Blueprint('blog', __name__, template_folder='templates', static_folder='/static')

db = firestore.client()

@blog.route('/post/<entry_uid>')
def post(entry_uid):
    post = db.collection('articles').document(entry_uid).get().to_dict()
    return render_template('eachentry.html', post = post, entry_uid = entry_uid)

@blog.route('/')
def blogview():
    return render_template('blog.html')

@blog.route('/post', methods = ['GET','POST'])
def blogpost():
    # print(request.form['title'])

    if request.method == 'POST' and 'tags' in request.form and 'title' in request.form and 'text' in request.form:
        text = request.form['text']
        title = request.form['title']
        tags = request.form['tags']
        author = request.form['author']

        oid = os.environ['BLOGPOST_ID']
        uid = ''
        for i in oid:
            if i.isdigit():
                uid+=i

        uid = int(uid) + 1
        uid = str(uid)

        os.environ['BLOGPOST_ID'] = uid

        Tags = tags.split(',')

        db.collection('articles').document(uid).set({
            'title': title,
            'text': text,
            'author': author,
            'tags': Tags
        })

        return True

    if Authenticate(): return render_template('postentry.html', user = session['userHandle'])

    flash('Please login first', 'danger')
    return redirect(url_for('app_auth.login'))

@blog.route('/retrieveposts')
def retposts():
    docs = db.collection('articles').stream()

    data = {}

    for doc in docs:
        rdoc = doc.to_dict()
        data.update({doc.id:rdoc})
    
    return jsonify(data)