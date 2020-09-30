from flask import *
from firebase_admin import firestore
from app.app_auth.auth import Authenticate
import os, random

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

        time = firestore.SERVER_TIMESTAMP
        doc = db.collection('articles').order_by('timestamp',direction = firestore.Query.DESCENDING).limit(1).stream()

        uid = None

        for i in doc:
            if i.id:
                uid = int(i.id) + 1

        Tags = tags.split(',')

        if uid == None: uid=1

        db.collection('articles').document(str(uid)).set({
            'title': title,
            'text': text,
            'author': author,
            'tags': Tags,
            'timestamp' : time
        })

        return make_response({'status': 200})

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