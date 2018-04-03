from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import MySQLConnector

import md5
import re
NAME_REGEX = re.compile(r"[a-zA-Z]")
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__)
mysql = MySQLConnector(app, 'walldb')
app.secret_key="LetItBeSecret!"

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/register', methods=['POST'])
def createUser():
    if len(request.form['first_name']) < 2:
        flash("First Name cannot be less than 2 characters!")
        return redirect('/')
    elif not NAME_REGEX.match(request.form['first_name']):
        flash("First Name cannot contain numbers!")
        return redirect('/') 
    elif len(request.form['last_name']) < 2:
        flash("Last name cannot be less than 2 characters!")
        return redirect('/')
    elif not NAME_REGEX.match(request.form['last_name']):
        flash("Last Name cannot contain numbers!")
        return redirect('/')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!")
        return redirect('/')
    elif len(request.form['password']) < 8:
        flash("Password should be 8 characters!")
        return redirect('/')
    elif request.form['pw_confirmation']!=request.form['password']:
        flash("Password should match!")
        return redirect('/')
    else:
        hashed_password = md5.new(request.form['password']).hexdigest()
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())"

        data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'password': hashed_password
        }
        mysql.query_db(query, data)
        flash("Thank you for registering! Please log in below!")
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!")
        return redirect('/')
    elif len(request.form['password']) < 8:
        flash("Password should be 8 characters!")
        return redirect('/')
    else:
        user_email = request.form['email']
        hashed_password = md5.new(request.form['password']).hexdigest()
        query = "SELECT * FROM users WHERE email = :user_email"
        data = {
            'user_email': request.form['email']
        }
        users = mysql.query_db(query,data)
        if hashed_password == users[0]['password']:  
            session['user_id'] = users[0]['idusers']
            session['name'] = users[0]['first_name']
            print  session['user_id']
            return redirect('/wall')

        else: 
            flash("Password doesnot match!")
            return redirect('/')

@app.route('/messages', methods=['POST'])
def message():
        user_id= session['user_id']
        query = "INSERT INTO messages (message, created_at, updated_at, users_idusers) VALUES (:message, NOW(), NOW(), :user_id);"
        
        data = {
                'message': request.form['message'], 
                'user_id': session['user_id']
            }
        messages = mysql.query_db(query, data)

        return redirect('/wall')

@app.route('/comments', methods=['POST'])
def comment():
        user_id = session['user_id']
        message_id = int(request.form['hidden'])
        query = "INSERT INTO comments (commenttext, created_at, updated_at, users_idusers, messages_idmessages) VALUES (:comment, NOW(), NOW(), :user_id, :message_id);"
        data = {
            'comment': request.form['comment'], 
            'user_id': session['user_id'],
            'message_id': message_id
        }
        mysql.query_db(query, data)
        
        return redirect('/wall')

@app.route('/wall')
def messages():
        username= session['name']

        messages_query = "SELECT messages.idmessages, messages.message, users.idusers, CONCAT(users.first_name,' ', users.last_name) as name, messages.created_at FROM messages JOIN users ON messages.users_idusers=users.idusers;"
        messages=mysql.query_db(messages_query)

        comments_query = "SELECT comments.created_at, comments.commenttext, comments.messages_idmessages, users.idusers, CONCAT(users.first_name,' ', users.last_name) as name FROM comments JOIN messages ON comments.messages_idmessages = messages.idmessages JOIN users ON comments.users_idusers=users.idusers;"
        comments = mysql.query_db(comments_query)
        
        return render_template('wall.html', username=username, messages=messages, comments=comments)

app.run(debug=True)