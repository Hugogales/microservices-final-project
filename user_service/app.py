from flask import Flask, request, jsonify, session
from flask_cors import CORS 
import os
import mysql.connector
import json
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')
CORS(app, supports_credentials=True)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST' , 'mysql'),
        user=os.environ.get('DB_USER' , 'root'),
        password=os.environ.get('DB_PASSWORD' , 'password'),
        database=os.environ.get('DB_NAME' , 'messaging_app')
    )

def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Users table created")


@app.route('/api/users/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Username already exists'}), 409
    
    cursor.execute(
        'INSERT INTO users (username, password) VALUES (%s, %s)',
        (username, password)
    )
    
    user_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'id': user_id, 'username': username, 'message': 'User registered successfully'}), 201

@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.json
    username = data.get( 'username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not user or not user['password'] == password:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # puts the user info on the cookies
    session['user_id'] = user['id']
    session['username'] = user['username']
    
    return jsonify({'id': user['id'],'username': user['username'],'message': 'Login successful'}), 200

@app.route('/api/users/logout', methods=['POST'])
def logout():
    # clears the cookies
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/users/current', methods=['GET'])
def get_current_user():
    #  get info from cookies
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id parameter is required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(user), 200

@app.route('/api/users', methods=['GET'])
def get_users():
    # get all users except the current user
    current_user_id = request.args.get('current_user_id')
    if not current_user_id:
        return jsonify({'error': 'current_user_id query parameter is required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, username FROM users WHERE id != %s', (current_user_id,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users), 200

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # get user info
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(user), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'user-service'}), 200

if __name__ == '__main__':
    create_users_table()
    app.run(host='0.0.0.0' , port=5001, debug=True) 