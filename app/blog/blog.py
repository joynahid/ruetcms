from flask import Blueprint, url_for, render_template, request, make_response, redirect, flash, jsonify, session
from firebase_admin import firestore
from app.app_auth.auth import Authenticate
import os
import random

blog = Blueprint('blog', __name__, template_folder='templates',
                 static_folder='/static')

db = firestore.client()


@blog.route('/post/<entry_uid>')
def post(entry_uid):
    post = db.collection('articles').document(entry_uid).get().to_dict()
    return render_template('eachentry.html', post=post, entry_uid=entry_uid)


@blog.route('/')
def blogview():
    return render_template('blog.html')


@blog.route('/post', methods=['GET', 'POST'])
def blogpost():
    if request.method == 'POST' and 'tags' in request.form and 'title' in request.form and 'text' in request.form:
        text = request.form['text']
        title = request.form['title']
        tags = request.form['tags']
        author = request.form['author']

        time = firestore.SERVER_TIMESTAMP
        doc = None

        try:
            db.collection('articles').order_by(
                'timestamp', direction=firestore.Query.DESCENDING).limit(1).stream()
        except: pass

        uid = None

        make_data = {
            'title': title,
            'text': text,
            'author': author,
            'timestamp': time
        }

        if request.form['uid']:
            uid = request.form['uid']
            make_data.update({
                'isEdited': True,
                'id': uid
            })
        else:
            # new post
            try:
                for i in doc:
                    if i.id:
                        uid = int(i.id) + 1
            except:
                pass

            Tags = tags.split(',')

            if uid == None:
                uid = 1

            make_data.update({
                'tags': Tags,
                'id': uid
            })

        print(make_data)

        db.collection('articles').document(str(uid)).set(make_data)

        return make_response({'status': 200})

    if Authenticate():
        print('edit it', request.args.get('post_id'))

        edit_post_id = request.args.get('post_id')

        if edit_post_id:
            article = db.collection('articles').document(
                str(edit_post_id)).get().to_dict()
            try:
                article['tags'] = str(article['tags'])
                article['tags'] = article['tags'][2:len(article['tags'])-2]

                article['tags'].replace('\'', '')

                article.update({'edit_id': edit_post_id})
            except:
                article['tags'] = ''

            return render_template('postentry.html', user=session['userHandle'], article=article)

        return render_template('postentry.html', user=session['userHandle'])

    flash('Please login first', 'danger')
    return redirect(url_for('app_auth.login'))


@blog.route('/retrieveposts')
def retposts():
    docs = db.collection('articles').order_by(
        'id', direction=firestore.Query.DESCENDING).stream()

    data = []

    for doc in docs:
        rdoc = doc.to_dict()

        print(doc.id)

        # print(rdoc)
        data.append(rdoc)

    return jsonify(data)


@blog.route('/retrieveindividualposts')
def retindposts():
    docs = db.collection('articles').where(
        'author', '==', request.args.get('author')).stream()

    data = []

    for doc in docs:
        rdoc = doc.to_dict()

        print(doc.id)

        # print(rdoc)
        data.append(rdoc)

    return jsonify(data)
