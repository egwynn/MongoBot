# -*- coding: utf-8 -*-

# Welcome to the server. If you've install uwsgi and nginx
# and that nginx server is running and then ran uwsgi server/deploy.ini,
# yay! You can use this. This runs a couple of simple pages, a
# chatlog interface, and an error log behind an http auth or the
# temporary password thing. Will eventually document how to get it
# up and running more extensively.


import os
import random
import time
import simplejson as json

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, _app_ctx_stack
from server.decorators import requires_auth
from server.helpers import fetch_chats, render_xml, fetch_quotes
from autonomic import Dendrite
from config import load_config
from util import shorten
from cybernetics import metacortex

# Commented out until broca is fixed
# from brainmeats.broca import Broca

app = Flask(__name__)

conf = load_config('config/settings.yaml')
secret = load_config('config/secrets.yaml')

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/api/chat", methods=['GET', 'POST'])
@requires_auth
def api_chat():
    offset = False
    if request.args.get('offset'):
        offset = request.args.get('offset')

    try:
        chats = fetch_chats(request, offset)
    except Exception as e:
        return str(e)

    return json.dumps(chats)


@app.route("/quotes")
@requires_auth
def quotes():
    quotes = fetch_quotes()
    onetime = request.args.get('onetime')
    return render_template('quotes.html', quotes=quotes, onetime=onetime)

@app.route("/chatlogs")
@requires_auth
def chatlogs():
    hint = 'Press "/" to search logs.'
    onetime = request.args.get('onetime')
    return render_template('chatlogs.html', hint=hint, onetime=onetime)


@app.route("/errorlog")
@requires_auth
def errorlog():
    log = open('hippocampus/log/error.log', 'r').read()
    return render_template('errors.html', log=log)


@app.route("/codez")
def codez():
    return render_template('codez.html')

@app.route("/shock")
def shock():
    os.system('python /usr/home/peter/bots/mongo.bak/medulla.py')
    return render_template('index.html')

@app.route("/poetry")
def poetry():
    poems = os.listdir(conf.media.poems)
    display = []
    for poem in poems:
        if poem == '.gitignore':
            continue
        f = open('%s/%s' % (conf.media.poems, poem), 'r')
        title = f.readline()
        f.close()
        display.append({'title': title, 'link': poem[:-4]})

    return render_template('poetry.html', poems=display)

@app.route("/upload", methods=['NORRIS'])
def upload():
    try:
        file = request.files['file']
        msg = 'New file upload'
        if 'msg' in request.form:
            msg = request.form['msg']

        timestamp = int(time.time())
        name = "%s-%s" % (timestamp, file.filename)
        path = 'server/static/uploads/%s' % name
        file.save(path)

    except Exception as e:
        return str(e) + "\n"

    url = shorten('%s/static/uploads/%s' % (conf.misc.website, name))

    line = "%s %s" % (msg, url) #secret.primary_channel)
    messages = open('/tmp/uploads.msgs', 'a')
    messages.write(line + "\n")
    messages.close()

    return "File saved: %s\n" % url


# Commented out until broca is fixed
#@app.route("/random_poem")
#def randompoem():
#    b = Broca(Dendrite)
#
#    starter = random.choice(['e', 'a', 'i', 'o', 'u'])
#
#    seed = b.babble([starter])
#    title = seed
#
#    poem = []
#    seed = seed.split()
#    for word in seed:
#        line = b.babble([word])
#        line = ''.join([i if ord(i) < 128 else '' for i in line])
#        poem.append(line)
#
#    return render_template('poem.html', title=title, poem=poem)


# There's a weird bug in some of the poems that crashes. Not sure what.
@app.route("/poem/<title>")
def showpoem(title):
    if not title:
        return render_template('poem.html', title='Have not written that', poem=[])

    try:
        f = open('%s/%s.txt' % (conf.media.poems, title), 'r')
        title = f.readline()
        text = [line for line in f]
        f.close()
    except:
        return render_template('poem.html', title='Have not written that', poem=[])

    poem = []
    for line in text:
        line = ''.join([i if ord(i) < 128 else '' for i in line])
        poem.append(line)

    return render_template('poem.html', title=title, poem=poem)


@app.route("/voice.xml", methods=['GET', 'POST'])
def twilio_voice():
    return render_xml('voice.xml')


@app.route("/sms.xml", methods=['GET', 'POST'])
def twilio_sms():
    return render_xml('sms.xml')


@app.route("/callback")
@app.route("/callback.html")
def callback():
    text = "Gettin jiggy wid it"
    return render_template('callback.html', text=text)


if __name__ == "__main__":
    app.debug = True
    app.run()
