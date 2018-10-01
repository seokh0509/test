# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, g, session, redirect, url_for, send_from_directory
from werkzeug import secure_filename
from datetime import datetime
import sqlite3, hashlib

app = Flask(__name__)
DATABASE = './db/data.db'
app.secret_key='abc'

UPLOAD_FOLDER='/files'
ALLOWED_EXTENSIONS=set(['txt','pdf','jpg','png', 'zip'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


##############################[1. DB]####################################
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        f = open('schema.sql', 'r')
        db.execute(f.read())
        db.commit()


#############################[2. Main Page]###############################
@app.route('/', methods=['GET', 'POST'])
def main_page():
    if 'uid' in session:
        if session['uid']=="admin":
            return render_template('admin.html', state = session['uid'])
        else:
            return render_template('main.html', state = session['uid'])
    else:
        return render_template('main.html', state = "Not Logged")

@app.route('/logout')
def log_out():
    session.pop('uid',None)
    session.pop('upw',None)
    session.pop('umail',None)
    return '<script>alert("Log-out"); document.location.href="/"</script>'

##############################[3. Userlist]################################
def detect_user(uid, umail, phone):
    sql = 'select 1 from userlist where u_id="%s" or u_mail="%s" or u_phone="%s"' %(uid, umail, phone)
    db = get_db()
    rv=db.execute(sql)
    res= rv.fetchall()
    try:
        if res[0][1] == 1:
            return "error"
        else:
            return "error"
    except IndexError:
        if res == []:
            return "none"
        else:
            return "one"

def add_user(uid, upw, umail, phone):
    hpw = hashlib.sha224(upw).hexdigest()
    sql = 'INSERT INTO userlist (u_id, u_pw, u_mail, u_phone) VALUES("%s", "%s", "%s", "%s")' %(uid, hpw, umail, phone)
    db = get_db()
    db.execute(sql)
    db.commit()

def login_user(uid, upw):
    hpw = hashlib.sha224(upw).hexdigest()
    sql = 'SELECT * FROM userlist where u_id="%s" and u_pw="%s"' %(uid,hpw)
    db = get_db()
    rv = db.execute(sql)
    res = rv.fetchall()
    return res    

def get_list():
    sql = 'select * from userlist'
    db = get_db()
    rv=db.execute(sql)
    res= rv.fetchall()
    db.close()
    return res

def get_user4mod(uid):
    sql = 'select * from userlist where u_id="%s";' %(uid)
    db = get_db()
    rv = db.execute(sql)
    res = rv.fetchone()
    return res

def mod_user(uid, upw, umail, phone):
    hpw = hashlib.sha224(upw).hexdigest()
    sql = 'update userlist set u_pw="%s", u_mail="%s", u_phone="%s" where u_id="%s"' %(hpw, umail, phone, uid)
    db = get_db()
    db.execute(sql)
    db.commit()

def del_user(uid):
    sql = 'delete from userlist where u_id="%s"' %(uid)
    db = get_db()
    db.execute(sql)
    db.commit()

#-----------------------------------------------------------------------------

@app.route('/user_list', methods=['GET','POST'])
def userlist():
    return render_template('user_list.html', users = get_list())

@app.route('/user_add', methods=['GET', 'POST'])
def add_userlist():
    if request.method == 'GET':
        return render_template('user_add.html')
    elif request.method == 'POST':
        uid = request.form.get('uid')
        upw = request.form.get('upw')
        umail = request.form.get('umail')
        uphone = request.form.get('phone')
        if uid != "" and upw != "" and umail != "" and uphone != "" and detect_user(uid, umail, uphone)=="none":
            add_user(uid, upw, umail,uphone)
            return '<script>alert("Register Success"); document.location.href="/"</script>'
        else:
            return '<script>alert("invalid input"); document.location.href="/user_add"</script>' 

@app.route('/login', methods=['GET', 'POST'])
def log_in():
    if request.method == "GET":
        return render_template('login.html')
    else:
        uid = request.form.get('uid')
        upw = request.form.get('upw')
        test = login_user(uid,upw)
        if len(test) !=  0:
            session['uid']=uid
            session['upw']=upw
            session['umail']=test[0][2]
            return '<script>alert("Login Success."); document.location.href="/"</script>'
        else:
            return '<script>alert("Login Failed."); document.location.href="/login"</script>'


@app.route('/user_mod', methods=['GET', 'POST'])
def user_mod():
    if 'uid' in session:
        uid = session['uid']
        if request.method == 'GET':
            res = get_user4mod(uid)
            return render_template('user_mod.html', data = res)
        else:
            upw = request.form.get('upw')
            mail = request.form.get('mail')
            phone = request.form.get('phone')
            if uid != "" and upw != "" and mail != "" and phone != "" and detect_user(uid, mail, phone)=="one":
                res = mod_user(uid,upw,mail,phone)
                return render_template('user_mod.html', data = res)
            else:
                return '<script>alert("invalid input"); document.location.href="/user_mod"</script>' 
    else:
        return '<script>alert("Login Please."); document.location.href="/"</script>'
    
@app.route('/user_del', methods=['GET', 'POST'])
def user_del():
    if 'uid' in session:
        uid = session['uid']
        if request.method == 'GET':
            res = get_user4mod(uid)
            return render_template('user_del.html', data = res)
        else:
            upw = request.form.get('upw')
            test = login_user(uid,upw)
            if len(test) !=  0:
                log_out()
                del_user(uid)
                return '<script>alert("Delete User Complate."); document.location.href="/"</script>'
            else:
                return '<script>alert("Check Userinfo."); document.location.href="/user_del"</script>'
    else:
        return '<script>alert("Login Please."); document.location.href="/"</script>'
  


##############################[4. Board]################################
def get_board():
    sql = 'select * from board order by time DESC;'
    db = get_db()
    rv=db.execute(sql)
    res= rv.fetchall()
    return res

def board_add(title, cont, uid, ftime="", fn=""):
    sql = 'INSERT INTO board (title, cont, uid, file, fn) VALUES("%s", "%s", "%s", "%s", "%s");' %(title,cont,uid,ftime,fn)
    db = get_db()
    db.execute(sql)
    db.commit()

def mod_board(title, cont, idx):
    sql = 'update board set title="%s", cont="%s" where idx="%s";' %(title, cont, idx)
    db = get_db()
    db.execute(sql)
    db.commit()

def del_board(idx):
    sql = 'delete from board where idx="%s";' %(idx)
    db = get_db()
    db.execute(sql)
    db.commit()

def get_cont(idx):
    sql = 'select * from board where idx=%s;' %(idx)
    db = get_db()
    rv=db.execute(sql)
    res= rv.fetchone()
    return res

def comment_add(comm,uid,bid,pid=""):
    sql = 'INSERT INTO comments (pid,bid,cont,uid) VALUES("%s", "%s", "%s","%s");' %(pid,bid,comm,uid)
    db = get_db()
    db.execute(sql)
    db.commit()

def get_com(idx):
    sql = 'select * from comments where bid="%s";' %(idx)
    db = get_db()
    rv=db.execute(sql)
    res= rv.fetchall()
    return res

def get_comm(idx):
    sql = 'select * from comments where idx="%s";' %(idx)
    db = get_db()
    rv=db.execute(sql)
    res= rv.fetchall()
    return res

#------------------------------------------------------------------------
@app.route('/board', methods=['GET','POST'])
def board_list():
    return render_template('board.html', data = get_board())

@app.route('/board_add', methods=['GET','POST'])
def board():
    if 'uid' in session:
        if request.method=='GET':
            return render_template('board_add.html')
        else:
            title = request.form.get('title')
            cont = request.form.get('cont')
            uid = session['uid']
            if len(title) != 0 and len(cont) != 0:
                if 'file' in request.files:
                    f=request.files['file']
                    fn=f.filename
                    time = str(datetime.now())
                    htime = hashlib.sha224(time).hexdigest() 
                    filepath = (htime + fn).replace(" ","")
                    f.save('./files/' + secure_filename(filepath))
                    board_add(title, cont, uid, filepath, fn)
                    return redirect(url_for('board_list'))
                else:
                    board_add(title, cont, uid)
                    return redirect(url_for('board_list'))
            else:
                return '<script>alert("input text, please."); document.location.href="/board_add" </script>'
    else:
        return '<script>alert("Login Please."); document.location.href="/"</script>'


@app.route('/board_view/<idx>', methods=['GET', 'POST'])
def board_view(idx):
    f = get_cont(idx)[7]    # Load filename_value in DB
    fpath = get_cont(idx)[6]
    if f  == "":         # if filetime == ""
        return render_template('board_view.html', data = get_cont(idx), com = get_com(idx))
    else :                  # if filetime != ""
        return render_template('board_view.html', data = get_cont(idx), com = get_com(idx), filename=f, fdown=fpath)


@app.route('/download/<filepath>')
def download(filepath):
    fpath = "./files/" + filepath
    return send_from_directory(directory='files', filename=filepath)

@app.route('/comment/<idx>', methods=['post'])
def add_co(idx):
    if 'uid' in session:
        com = request.form.get('com')
        uid = session['uid']
        if len(com) != 0:
            comment_add(com,uid,idx)
            return render_template('board_view.html', data = get_cont(idx), com = get_com(idx))
        else:
            return '<script>alert("input text, please.")</script>'
    else:
        return '<script>alert("Login Please."); document.location.href="/"</script>'

@app.route('/modcom/<idx>', methods=['GET','POST'])
def modcom(idx):
    com = get_comm(idx)
    if session['uid'] == com[0][4]:
        if request.method == "GET":
            return render_template('mod_com.html', data = com)
        else:
            cont = request.form.get('modcom')
            sql = 'update comments set cont="%s" where idx="%s";' %(cont, idx)
            db = get_db()
            db.execute(sql)
            db.commit()
            return '<script>alert("Update Complate"); document.location.href="/board" </script>'
    else:
        return '<script>alert("Invalid User"); document.location.href="/board" </script>'

@app.route('/delcom/<idx>', methods=['GET','POST'])
def delcom(idx):
    com = get_comm(idx)
    uid = session['uid']
    if uid == com[0][4]:
        if request.method=='GET':
            return render_template('del_com.html', data = com)
        else:
            user = get_user4mod(uid)
            upw = request.form.get('upw')
            hpw = hashlib.sha224(upw).hexdigest()
            if hpw == user[1]:
                sql = 'delete from comments where idx="%s";' %(idx)
                db = get_db()
                db.execute(sql)
                db.commit()
                return '<script>alert("Delete Comment Complate"); document.location.href="/board" </script>' 
            else:
                return '<script>alert("Invalid User."); document.location.href="/board" </script>'
    else:
        return '<script>alert("Invalid User"); document.location.href="/board" </script>'

@app.route('/board_mod/<idx>', methods=['GET','POST'])
def board_mod(idx):
    res = get_cont(idx)
    if res[3] == session['uid']:
        if request.method=='GET':
            return render_template('board_mod.html', data = res)
        else:
            title = request.form.get('title')
            cont = request.form.get('cont')
            if len(title) != 0 and len(cont) != 0:
                mod_board(title, cont, idx)
                return '<script>alert("Update Complate"); document.location.href="/board" </script>'
            else:
                return '<script>alert("input text, please."); document.location.href="/board"</script>'
    else:
        return '<script>alert("Invalid User"); document.location.href="/board" </script>'
 
@app.route('/board_del/<idx>', methods=['GET','POST'])
def board_del(idx):
    res = get_cont(idx)
    uid = session['uid']
    if res[3] == uid:
        if request.method=='GET':
            return render_template('board_del.html', data = res)
        else:
            if len(detect_com(idx)) == 0:
                user = get_user4mod(uid)
                upw = request.form.get('upw')
                hpw = hashlib.sha224(upw).hexdigest()
                if hpw == user[1]:
                    del_board(idx)
                    return '<script>alert("Delete Board Complate"); document.location.href="/board" </script>' 
                else:
                    return '<script>alert("Invalid User."); document.location.href="/board" </script>'
            else:
                print detect_com(idx)
                print len(detect_com(idx))
                return '<script>alert("First, Delete Comment."); document.location.href="/board" </script>'
    else:
        return '<script>alert("Invalid User"); document.location.href="/board" </script>'

def detect_com(bid):
    sql = 'select 1 from comments where bid="%s";' %(bid)
    db = get_db()
    rv=db.execute(sql)
    res= rv.fetchall()
    return res




#------------------------------------------------------------------
if __name__ == '__main__':
#    init_db()
    app.run(debug=True, host='0.0.0.0', port=1111)
