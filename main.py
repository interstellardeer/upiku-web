import datetime
import json

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import requests
from config import SERVER_ADDRESS, PORT


app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Add this line
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # replace with your secret key
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config.from_object('config')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET'])
def admin():
    # Add any necessary logic here
    return render_template('admin.html')

@app.route('/user', methods=['GET'])
def user():
    # Add any necessary logic here
    return render_template('user.html')

@app.route('/curhats', methods=['GET'])
def get_curhats():
    response = requests.get(f'{SERVER_ADDRESS}/curhat')
    if response.status_code == 200:
        try:
            curhats = response.json()
            for curhat in curhats:
                if 'curhatid' not in curhat:
                    return 'Curhat does not have curhatid', 500
            return render_template('curhats.html', curhats=curhats)
        except json.JSONDecodeError:
            return 'Failed to parse response as JSON', 500
    else:
        return 'Failed to get curhats', response.status_code

@app.route('/curhats', methods=['POST'])
def add_curhat():
    form_data = request.form.to_dict()

    # Set the userid to the current logged in user's userid
    form_data['userid'] = session['userid']

    # Set the date and time to the current date and time
    now = datetime.datetime.now()
    form_data['date'] = now.strftime('%Y-%m-%d')
    form_data['time'] = now.strftime('%H:%M:%S')

    response = requests.post(f'{SERVER_ADDRESS}/curhat', json=form_data, headers={'Content-Type': 'application/json'})
    if response.status_code == 201:
        return redirect(url_for('get_curhats'))
    else:
        return 'Failed to add curhat', 400

@app.route('/curhats/<curhat_id>', methods=['POST'])
def update_curhat(curhat_id):
    curhat_data = request.form.to_dict()
    response = requests.put(f'{SERVER_ADDRESS}/curhat/{curhat_id}', json=curhat_data)
    if response.status_code == 200:
        return redirect(url_for('curhat_detail', curhat_id=curhat_id))
    else:
        return 'Failed to update curhat', 400

@app.route('/curhats/<curhat_id>', methods=['POST'])
def delete_curhat(curhat_id):
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/json'
    }
    response = requests.delete(f'{SERVER_ADDRESS}/curhat/{curhat_id}', headers=headers)
    if response.status_code == 200:
        return redirect(url_for('get_curhats'))
    else:
        return 'Failed to delete curhat', 400
@app.route('/curhats/<int:curhat_id>', methods=['GET'])
def curhat_detail(curhat_id):
    # Get the curhat
    response = requests.get(f'{SERVER_ADDRESS}/curhat/{curhat_id}')
    if response.status_code != 200:
        return 'Failed to get curhat', response.status_code
    curhat = response.json()

    # Get the user data for the userid in the curhat
    response = requests.get(f'{SERVER_ADDRESS}/user/{curhat["userid"]}')
    if response.status_code != 200:
        return 'Failed to get user data', response.status_code
    user_data = response.json()

    # Add the username to the curhat
    curhat['username'] = user_data['username']

    # Get the comments for the curhat
    response = requests.get(f'{SERVER_ADDRESS}/comment', params={'curhatid': curhat_id})
    if response.status_code == 200:
        comments = response.json()
    else:
        comments = []  # Set comments to an empty list if there are no comments

    # Get the number of comments
    num_comments = len(comments)

    return render_template('curhat_detail.html', curhat=curhat, comments=comments, num_comments=num_comments, session=session)

@app.route('/comment', methods=['GET'])
def get_comments():
    curhat_id = request.args.get('curhatid')
    search = request.args.get('search')
    response = requests.get(f'{SERVER_ADDRESS}/comment', params={'curhatid': curhat_id, 'search': search})
    if response.status_code == 200:
        return response.json()
    else:
        return 'Failed to get comments', response.status_code

from datetime import datetime

@app.route('/comment', methods=['POST'])
def post_comment():
    comment_data = request.form.to_dict()

    # Set the userid to the current logged in user's userid
    comment_data['userid'] = session['userid']

    # Set the date and time to the current date and time
    now = datetime.now()
    comment_data['date'] = now.strftime('%Y-%m-%d')
    comment_data['time'] = now.strftime('%H:%M:%S')

    response = requests.post(f'{SERVER_ADDRESS}/comment', json=comment_data, headers={'Content-Type': 'application/json'})
    if response.status_code == 201:
        return redirect(url_for('curhat_detail', curhat_id=comment_data['curhatid']))
    else:
        return 'Failed to post comment', 400

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form_data = request.form.to_dict()

        user_data = {
            'username': form_data.get('username'),
            'email': form_data.get('email'),
            'roles': form_data.get('roles'),
            'password': form_data.get('password'),
            'profile_picture': form_data.get('profile_picture'),
            'bio_text': form_data.get('bio_text'),
            'phone_number': form_data.get('phone_number'),
            'faculty': form_data.get('faculty')
        }

        response = requests.post(f'{SERVER_ADDRESS}/user', json=user_data, headers={'Content-Type': 'application/json'})
        if response.status_code == 201:
            return redirect(url_for('login'))
        else:
            return 'Registration failed', 400
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_data = request.form.to_dict()

        user_data = {
            'username': form_data.get('username'),
            'password': form_data.get('password')  # send password in plain text
        }

        response = requests.post(f'{SERVER_ADDRESS}/login', json=user_data,
                                 headers={'Content-Type': 'application/json'})
        print("Response status code:", response.status_code)
        print("Response data:", response.json())

        if response.status_code == 200:
            user_data = response.json()
            session['access_token'] = user_data['access_token']  # store the token in session
            session['userid'] = user_data['userid']
            # session['username'] = user_data.get('username')
            # session['roles'] = user_data.get('roles')

            if user_data.get('roles') == 'admin':  # use get method to avoid KeyError
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('user'))
        else:
            return 'Login failed', 400
    else:
        return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # clear the session
    return redirect(url_for('index'))  # redirect to the index page

@app.route('/session_data', methods=['GET'])
def session_data():
    data = {
        'userid': session.get('userid'),
        'access_token': session.get('access_token')
    }
    return jsonify(data)

@app.route('/home', methods=['GET'])
def home_route():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(port=PORT, debug=True)
