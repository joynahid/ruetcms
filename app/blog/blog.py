from flask import Blueprint, url_for, render_template, request, make_response, redirect, flash, jsonify, session, Markup, escape
from firebase_admin import firestore
from app.app_auth.auth import Authenticate
from app.blog.clearence.text_factory import textFactory
import os
import random

blog = Blueprint('blog', __name__, template_folder='templates',
                 static_folder='/static')

db = firestore.client()


@blog.route('/post/<entry_uid>')
def post(entry_uid):
    post = db.collection('articles').document(entry_uid).get().to_dict()

    txtProcess = textFactory(post['text'])
    post['text'] = txtProcess.htmlify()

    post['title'] = post['title']
    post['text'] = Markup(post['text'])

    if Authenticate():
        return render_template('eachentry.html', user=session['userHandle'], post=post, entry_uid=entry_uid)

    return render_template('eachentry.html', post=post, entry_uid=entry_uid)

@blog.route('/')
def blogview():
    return render_template('blog.html')

@blog.route('/post', methods=['GET', 'POST'])
def blogpost():
    if request.method == 'POST' and 'tags' in request.form and 'title' in request.form and 'text' in request.form:
        text = request.form['text']
        title = request.form['title'].title()
        tags = request.form['tags']
        author = request.form['author']

        time = firestore.SERVER_TIMESTAMP
        doc = None

        try:
            doc = db.collection('articles').order_by(
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
                'id': int(uid)
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
                'id': int(uid)
            })

        print(make_data)

        db.collection('articles').document(str(uid)).set(make_data)

        return make_response({'status': 200})

    if Authenticate():
        edit_post_id = request.args.get('post_id')

        if edit_post_id:
            article = db.collection('articles').document(
                str(edit_post_id)).get().to_dict()

            if article:
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

@blog.route('/post/delete/<id>')
def delete_post(id):
    if Authenticate():
        docs = db.collection('articles').where(u'id',u'==',int(id)).stream()

        print(docs)
        print(session['userHandle']['username'])

        for doc in docs:
            data = doc.to_dict()

            print(data)

            if data['author'] == session['userHandle']['username']:
                doc.reference.delete()
                flash('Deleted','success')
                return redirect(request.referrer)
    
    return 'failed'


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
