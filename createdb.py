import datetime
import os
import random
import re
import sqlite3

DATABASE = 'database.sqlite'

# Simple user blog site

# From http://listofrandomnames.com/index.cfm?textarea
USERS=map(lambda x:x.strip(), re.split('[\r\n]+','''Aleida King  
Billye Quayle  
Mildred Beaty  
Adeline Beyers  
Tricia Wendel  
Kizzy Bedoya  
Marx Warn  
Hulda Culberson  
Devona Morvant  
Winston Tomasello  
Dede Frame  
Lissa Follansbee  
Timmy Dapolito  
Gracie Lonon  
Nana Officer  
Yuri Kruchten  
Chante Brasch  
Edmond Toombs  
Scott Schwan  
Lean Beauregard  
Norberto Petersen  
Carole Costigan  
Chantel Drumheller  
Riva Redfield  
Jennie Sandifer  
Vivian Cimini  
Goldie Hayworth  
Tomeka Kimler  
Micaela Juan  
Jerrold Tjaden  
Collene Olson  
Edna Serna  
Cleveland Miley  
Ena Haecker  
Huey Voelker  
Annamae Basco  
Florentina Quinlan  
Eryn Chae  
Mozella Mcknight  
Ruby Cobble  
Jeannine Simerly  
Colby Tabares  
Jason Castorena  
Asia Mosteller  
Betsy Mendelsohn  
Nicolle Leverette  
Bobette Tuel  
Lizabeth Borchert  
Danica Halverson  
Consuelo Crown'''))

def create():
    db = sqlite3.connect(DATABASE)

    c=db.cursor()

    c.execute('''CREATE TABLE users (userid integer PRIMARY KEY, username VARCHAR(32), name TEXT, password VARCHAR(256), email TEXT)''')
    c.execute('''CREATE TABLE posts (creator integer REFERENCES users(userid), date INTEGER, title TEXT, content TEXT)''')
    c.execute('''CREATE INDEX user_username on users (username)''')
    c.execute('''CREATE INDEX user_posts on posts (creator,date)''')
    db.commit()

    id=0
    for user in USERS:
        create_content(db, id, user)
        id+=1
    db.commit()

def create_content(db, id, name):
    password='password'
    c=db.cursor()
    username = '%s%s'%(name.lower()[0], name.lower()[name.index(' ')+1:])
    email = '%s.%s@email.com'%((name.lower()[0], name.lower()[name.index(' ')+1:]))
    c.execute('INSERT INTO users (userid, username, name, password, email) VALUES (?,?,?,?,?)',(id,username,name,password,email))
    date = datetime.datetime.now() - datetime.timedelta(28)
    
    for i in range( random.randrange(4,8) ):
        content = 'Some random text for item %d'%(i)
        title = 'Item %d'%(i)
        date = date + datetime.timedelta( random.randrange(1,3), minutes=random.randrange(1,120), hours=random.randrange(0,6) )

        c.execute('INSERT INTO posts (creator,date,title,content) VALUES (?,?,?,?)',(
            id, date.timestamp(), title, content
        ))

def delete_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

if __name__=='__main__':
    delete_db()
    create()