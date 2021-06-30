import datetime
import sqlite3
from functools import wraps

from datetime import timedelta
from flask import Flask,g,render_template,redirect,request,session,url_for, app

import string, random, os
import time



#Changes Made:
#Changed the secret key for the sessions to a longer random string
#app added to the flask imports
#@app.before request added for timeout session - the time is set for 5 minutes and they are logged out
#error messages changed in the /login/
#Banned the characters (',-,=,",;) from the username input
#Added validation/sanitization to the serch of the page
#added a new page - search error, shows the banned character message and the button returns to homepage
#Added sanitisation to the registration inputs from the user, just incase any SQL can be injected there

app = Flask(__name__)
app.secret_key = "b1-8\xa1\x16woC\xbfdE\r\xa9\x1dQ\xb3%>\xc4\x7f\x04\x9b\xde\xbf\xa1"

DATABASE = 'database.sqlite'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    def make_dicts(cursor, row):
        return dict((cursor.description[idx][0], value)
                    for idx, value in enumerate(row))

    db.row_factory = make_dicts

    return db

@app.before_request
def make_session_permanent():
    session.permanent = False
    app.permanent_session_lifetime = timedelta(minutes=5)

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def std_context(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        context={}
        request.context = context
        if 'userid' in session:
            context['loggedin'] = True
            context['username'] = session['username']
        else:
            context['loggedin'] = False
        return f(*args,**kwargs)
    return wrapper

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
@std_context
def index():
    posts = query_db('SELECT posts.creator,posts.date,posts.title,posts.content,users.name,users.username FROM posts JOIN users ON posts.creator=users.userid ORDER BY date DESC LIMIT 10')

    def fix(item):
        item['date'] = datetime.datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d %H:%M')
        item['content'] = '%s...'%(item['content'][:200])
        return item

    context = request.context
    context['posts'] = map(fix, posts)
    return render_template('index.html', **context)

@app.route("/<uname>/")
@std_context
def users_posts(uname=None):
    cid = query_db('SELECT userid FROM users WHERE username="%s"'%(uname))
    if len(cid)<1:
        return 'No such user'

    cid = cid[0]['userid']
    query = 'SELECT date,title,content FROM posts WHERE creator=%s ORDER BY date DESC'%(cid)
    
    context = request.context

    def fix(item):
        item['date'] = datetime.datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d %H:%M')
        return item
    a = query_db(query)
    context['posts'] = map(fix, query_db(query))
    return render_template('user_posts.html', **context)

@app.route("/login/", methods=['GET', 'POST'])
@std_context
def login():
    global sessionID
    username = request.form.get('username','')
    password = request.form.get('password','')
    context = request.context

    if len(username)<1 and len(password)<1:
        return render_template('login.html', **context)

    
    for x in username:
    	if x == "'" or x == '"' or x == "=" or x == "-" or x == ';':
    		return redirect(url_for('login_fail', error = 'Banned Characters present\n Please avoid using \' or \" or = or -'))
    	else:
    		pass

    query = "SELECT userid FROM users WHERE username='%s'"%(username)
    account = query_db(query)
    user_exists = len(account)>0

    with open("salt.key", "rt") as saltedKey:
        saltedkey = str(saltedKey.readlines())[2:-2]
    with open("pepper.key", "rt") as pepperedKey:
        pepperedkey = str(pepperedKey.readlines())[2:-2]

    numbers = []
    for char in password: 
        number = ord(char) + int(saltedkey)
        numbers.append(number)

    numbers.append(pepperedkey)
    convertToSingular = "".join(str(num) for num in numbers)
    convertToHash = str(convertToSingular)

    query = "SELECT userid FROM users WHERE username='%s' AND password='%s'"%(username, password)
    print(query)
    account2 = query_db(query)
    print(account)
    pass_match = len(account2)>0

    if user_exists:
        if pass_match:

            ## SET SESSION ID HERE

            sessionLength = 32
            generateSessionKey = "".join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=sessionLength))
            usernameRaw = []
            for char in username:
                usernameNew = ord(char) + 96
                usernameRaw.append(usernameNew)
            fixUsername = "".join(str(userna) for userna in usernameRaw)
            obfuscatedUsername = str(fixUsername)
            sessionID = obfuscatedUsername + generateSessionKey

            

            session['userid'] = account[0]['userid']
            session['sessionid'] = sessionID
            session['username'] = username

            print(sessionID + username)
            return redirect(url_for('index'))
        else:
            # Return wrong password
            return redirect(url_for('login_fail', error='Username/password combination not found'))
    else:
        # Return no such user
        return redirect(url_for('login_fail', error='Username/password combination not found'))

@app.route("/loginfail/")
@std_context
def login_fail():
    context = request.context
    context['error_msg'] = request.args.get('error','Unknown error')
    return render_template('login_fail.html',**context)

@app.route("/logout/")
def logout():
    session.pop('userid', None)
    session.pop('username', None)
    return redirect('/')

@app.route("/post/", methods=['GET', 'POST'])
@std_context
def new_post():
    if 'userid' not in session:
        return redirect(url_for('login'))

    userid = session['userid']

    # sessionid = session['sessionID']
    print(userid)
    context = request.context
    

    if request.method=='GET':
        return render_template('new_post.html', sessionIDtok=sessionID)

    date = datetime.datetime.now().timestamp()
    title = request.form.get('title').replace("<", "&lt;")
    content = request.form.get('content').replace("<", "&lt;")

    sessionValid = request.form.get('validsession','')


    print("SessionID: " + sessionID)
    print("SessionVAlid" + sessionValid)

    if sessionValid == sessionID:

        query = "INSERT INTO posts (creator, date, title, content) VALUES ('%s',%d,'%s','%s')"%(userid, date, title, content)
        insert = query_db(query)

        get_db().commit()

        return redirect('/')
    else:
        return redirect(url_for('login_fail', error='Your session has expired.'))

@app.route("/reset/", methods=['GET', 'POST'])
@std_context
def reset():
    context = request.context

    email = request.form.get('email','')
    if email=='':
        return render_template('reset_request.html')

    context['email'] = email
    return render_template('sent_reset.html', **context)

@app.route("/search/")
@std_context
def search_page():
    context = request.context
    search = request.args.get('s', '').replace("%", "&#37;")

    for x in search:
    	if x == "'" or x == '"' or x == "=" or x == "-" or x == ';':
    		return redirect(url_for('search_fail', error = 'Banned Characters present\n Please avoid using \' or \" or = or - or ;'))
    	else:
    		pass

    #query = "SELECT posts.creator,posts.title,posts.content,users.username FROM posts JOIN users ON posts.creator=users.userid WHERE users.username LIKE '%%%s%%' ORDER BY date DESC LIMIT 10;"%(search)
    query = "SELECT username FROM users WHERE username LIKE '%%%s%%';"%(search)
    users = query_db(query)
    #for user in users:
        #post['content'] = '%s...'%(post['content'][:50])
    context['users'] = users
    context['query'] = search.replace("<", "&lt;")
    context['query'] = search.replace("%", "&#37;")
    if (len(search) < 1):
        context['users'].clear()
    return render_template('search_results.html', **context)

@app.route("/searchfail/")
@std_context
def search_fail():
    context = request.context
    context['error_msg'] = request.args.get('error','Unknown error')
    return render_template('search_error.html',**context)

@app.route("/resetdb/<token>")
def resetdb(token=None):
    if token=='secret42':
        import create_db
        create_db.delete_db()
        create_db.create()
        return 'Database reset'
    else:
        return 'Nope',401





@app.route("/registration/", methods=['GET', 'POST'])
@std_context
def registration():
    name = request.form.get('fname','')
    email = request.form.get('email','')
    username = request.form.get('username','')
    password = request.form.get('password','')
    confirmpassword = request.form.get('confirmpassword','')
    confirmcaptcha = request.form.get('captcha', '')
    context = request.context

    ### Generate Captcha
  
    capCha = ['qITFV', 'JvJl2', 'u4nPg', 'a4isT', 'ViQZv', 'JlexR', '5MTYv', 'b2rnl', 'j59XC', 'C895c', 'sE48N', 'M8JAh', 'hUiz5', 's3WUX', '7eAtQ', 'jp9Il', '7B0m6', 't8ej7', '21vRx', '8FcuJ', 'JEmnc', 'ATJQX', 'FWzQn', '5cl2M', '7Pv6Z', 'asC2r', 'Eo1zj', 'mKnmc', 'YkcFQ', 'pNzoo', '3hw9f', '1bjO3', 'nNdLB', 'hwYmq', 'JzpZE', 'guVmg', '5s4lJ', 'lui1m', '1aGxu', '1xY6f', '2GqzR', 'uofUF', 'JVVvJ', 'YIIk1', 'AzJHf', '5Gsyy', 'PL8ui', 'KkU99', 'cWEJo', 'vCzCF', 'fgTl9', 'EVudA', 'oxmyn', '5Cc9P', 'QXr4V', 'j1H1S', 'NHvLd', 'pWndp', 'X5qnQ', 'IQWta', '71VWP', 'rJFrv', 'TayWN', 'zTBF8', 'YfSRL', 'TSQuY', '9TMap', '37fDs', '61IEu', 'vVw43', 'nifrX', 'KUmKu', 'n2rqN', 'YomcS', 't29fc', 'jQFT2', 'hI6Uw', 'yioyn', 'JNMoP', 'KL9S0', 'zTYQI', 'MfGXi', 'xNwZ1', '1v6Fy', 'OYZrv', 'Kbtyf', '3euid', 'C59gx', 'ovDFG', 'xnNky', 'Shpo7', 'uyBFW', 'suw2v', 'r7tQq', 'Jz35i', 'xHyfZ', '60nGS', 'BFhHs', 'ioMFq', '1QFai', 'uExOn']
    
    pick = random.choice(capCha)

    
    
    

        
    

    if len(username)<1 and len(password)<1:
        return render_template('registration.html', captcha=pick)


    for x in username:
        if x == "'" or x =='"' or x == '=' or x =='-' or x ==';':
            return redirect(url_for('registration_fail', error=' Banned Characters present\nPlease avoid using \' or \" or = or - or ;'))
        else:
            pass

    for x in name:
        if x == "'" or x =='"' or x =='=' or x =='-' or x ==';':
            return redirect(url_for('registration_fail', error='Banned Characters present\nPlease avoid using \' or \" or = or - or ;'))
        else:
            pass  

   
    query = "SELECT username, email FROM users WHERE username = '%s' or email = '%s'"%(username, email)
    account = query_db(query)
    user_exists = len(account)>0

    if user_exists:
        return redirect(url_for('registration_fail', error='A user with that email/username already exists.'))
    else:
        
        if confirmcaptcha in capCha:
            if password == confirmpassword:
                cur = get_db()
                # query = "INSERT INTO users (username, name, password, email) VALUES ('%s', '%s', '%s', '%s')"%(username, name, password, email)
                
                minLength = "xxxxxxxx"
                symbol = [':','@','£','#','*','&','^','$','!','?','.','~']

                if not any(ch in symbol for ch in password):
                    return redirect(url_for('registration_fail', error = 'There was an error when creating your account. Please ensure your password is at least 8 characters long and includes a symbol.'))
                else: 
                    if len(password) <= len(minLength): 
                        return redirect(url_for('registration_fail', error = 'There was an error when making your account. Please ensure your password is at least 8 characters long and includes a symbol.'))
                    else:
                        with open("salt.key", "rt") as saltedKey:
                            saltedkey = str(saltedKey.readlines())[2:-2]
                        with open("pepper.key", "rt") as pepperedKey:
                            pepperedkey = str(pepperedKey.readlines())[2:-2]

                        
                        numbers = []
                        for char in password: 
                            number = ord(char) + int(saltedkey)
                            numbers.append(number)

                        numbers.append(pepperedkey)
                        convertToSingular = "".join(str(num) for num in numbers)
                        convertToHash = str(convertToSingular)

                        query = "INSERT INTO users (username, name, password, email) VALUES ('%s', '%s', '%s', '%s')"%(username, name, password, email)
                        cur.execute(query)
                        cur.commit()
                        cur.close()
                        return render_template('registration_fin.html')
        else:
            # print("Error > " + str(generateCaptcha) + " " + confirmcaptcha)
            # print(generateCaptcha)
            return redirect(url_for('registration_fail', error = 'Incorrect Captcha.'))
        

@app.route("/registrationfail/")
@std_context
def registration_fail():
    context = request.context
    context['error_msg'] = request.args.get('error','Unknown error')
    return render_template('registration_fail.html',**context)


if __name__ == '__main__':
    app.run()