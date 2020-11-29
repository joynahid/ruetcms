from flask import Blueprint, url_for, render_template, request, make_response, redirect, flash, jsonify, session, Markup, escape, abort
from firebase_admin import firestore
from app.app_auth.auth import Authenticate
# from app.blog.clearence.text_factory import textFactory
import os
import random
import markdown2
import humanize
import datetime

md = markdown2.Markdown(extras=[
                        'code-friendly', 'fenced-code-blocks', 'spoiler', 'target-blank-links', 'strike'])

blog = Blueprint('blog', __name__, template_folder='templates',
                 static_folder='/static')

db = firestore.client()

@blog.route('/post/<entry_uid>')
def post(entry_uid):
    post = db.collection('articles').document(entry_uid).get().to_dict()

    if not post:
        abort(404)

    post['text'] = md.convert(post['text'][-1])
    post['text'] = Markup(post['text'])

    s = str(post['timestamp'])
    s = s.replace(s[s.index('.'):s.index('+')],'')

    s = datetime.datetime.strptime(s,"%Y-%m-%d %H:%M:%S%z")
    now = datetime.datetime.now(datetime.timezone.utc)

    delta = now-s

    naturalTime = humanize.naturaltime(delta)

    # print(naturalTime)

    post['timestamp'] = naturalTime

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

        if not title:
            return make_response({'status': 406})

        time = firestore.SERVER_TIMESTAMP
        doc = None

        try:
            doc = db.collection('articles').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).stream()
        except:
            pass

        uid = None

        make_data = {
            'title': title,
            'text': [text],
            'author': author,
            'timestamp': time
        }

        if request.form['uid']:
            uid = request.form['uid']
            try:
                docc = db.collection('articles').document(str(uid)).get().to_dict()
            except:
                return make_response({'status':404, 'msg': 'No Post Found'})

            docc['text'].append(text)

            print(docc)

            make_data.update({
                'text': docc['text'],
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

        db.collection('articles').document(str(uid)).set(make_data)

        return make_response({'status': 200, 'post_id': uid})

    if Authenticate():
        edit_post_id = request.args.get('post_id')

        if edit_post_id:
            article = db.collection('articles').document(str(edit_post_id)).get().to_dict()

            if article:
                if article['author'] != session['userHandle']['username']:
                    return 'Unauthorized',403

                if 'tags' in article:
                    article['tags'] = str(article['tags'])
                    article['tags'] = article['tags'].replace('[','').replace(']','').replace('"','')

                if article:
                    article.update({'edit_id': edit_post_id})
                    return render_template('postentry.html', user=session['userHandle'], post = article)
            else: return 'No article Found',404

        return render_template('postentry.html', user=session['userHandle'])

    flash('Please login first', 'danger')
    return redirect(url_for('app_auth.login'))


@blog.route('/retrieveposts')
def retposts():
    docs = db.collection('articles').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()

    data = []

    for doc in docs:
        rdoc = doc.to_dict()

        rdoc['text'] = rdoc['text'][-1]

        s = str(rdoc['timestamp'])
        s = s.replace(s[s.index('.'):s.index('+')],'')

        s = datetime.datetime.strptime(s,"%Y-%m-%d %H:%M:%S%z")
        now = datetime.datetime.now(datetime.timezone.utc)

        delta = now-s

        naturalTime = humanize.naturaltime(delta)

        # print(naturalTime)

        rdoc['timestamp'] = naturalTime

        # print(rdoc)
        data.append(rdoc)

    return jsonify(data)


@blog.route('/post/delete/<id>')
def delete_post(id):
    if Authenticate():
        docs = db.collection('articles').where(u'id', u'==', int(id)).stream()

        # print(docs)
        # print(session['userHandle']['username'])

        for doc in docs:
            data = doc.to_dict()

            if data['author'] == session['userHandle']['username']:
                doc.reference.delete()
                flash('Deleted', 'success')
                return redirect(request.referrer)

    return 'Unauthorized'


@blog.route('/retrieveindividualposts')
def retindposts():
    docs = db.collection('articles').where(
        'author', '==', request.args.get('author')).stream()

    data = []

    for doc in docs:
        rdoc = doc.to_dict()

        rdoc['text'] = rdoc['text'][-1]

        s = str(rdoc['timestamp'])
        s = s.replace(s[s.index('.'):s.index('+')],'')

        s = datetime.datetime.strptime(s,"%Y-%m-%d %H:%M:%S%z")
        now = datetime.datetime.now(datetime.timezone.utc)

        delta = now-s

        naturalTime = humanize.naturaltime(delta)

        # print(naturalTime)

        rdoc['timestamp'] = naturalTime

        data.append(rdoc)

    return jsonify(data)
