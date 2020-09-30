from flask import *
from firebase_admin import firestore
from app.app_auth.auth import Authenticate

blog = Blueprint('blog', __name__, template_folder='templates', static_folder='/static')

db = firestore.client()

@blog.route('/entry/<entry_uid>')
def entry(entry_uid):
    return render_template('eachentry.html', entry_uid = entry_uid)

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
        author = 'admin'

        Tags = tags.split(',')

        db.collection('articles').document('765').set({
            'title': title,
            'text': text,
            'author': author,
            'tags': Tags
        })

        print(title, text, Tags)

    return render_template('postentry.html')