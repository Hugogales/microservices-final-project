import os
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Environment variables for service discovery
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://user-service:5001')
MESSAGE_SERVICE_URL = os.environ.get('MESSAGE_SERVICE_URL', 'http://message-service:5002')

# MySQL Connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'mysql'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'password'),
        database=os.environ.get('DB_NAME', 'messaging_app')
    )

# Create the groups table if it doesn't exist
def create_groups_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS `groups` (
        id VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        creator_id VARCHAR(255) NOT NULL,
        members TEXT NOT NULL
    )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("Groups table created")

@app.route('/groups', methods=['POST'])
def create_group():
    data = request.get_json()
    name = data.get('name')
    creator_id = str(data.get('creator_id'))
    members = [str(member_id) for member_id in data.get('members', [])]

    if not name or not creator_id:
        return jsonify({"error": "Group name and creator_id are required"}), 400
    if creator_id not in members:
        members.append(creator_id)
    group_id = str(uuid.uuid4())
    group = {
        "id": group_id,
        "name": name,
        "creator_id": creator_id,
        "members": members
    }
    # Store group in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO `groups` (id, name, creator_id, members) VALUES (%s, %s, %s, %s)',
        (group_id, name, creator_id, json.dumps(members))
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({
        "message": "Group created successfully",
        "group_id": group_id,
        "group": group
    }), 201

@app.route('/groups/<group_id>', methods=['GET'])
def get_group(group_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM `groups` WHERE id = %s', (group_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    group = {
        "id": row['id'],
        "name": row['name'],
        "creator_id": row['creator_id'],
        "members": json.loads(row['members'])
    }
    
    # get details of all members
    members_info = []
    for member_id in group['members']:
        try:
            response = requests.get(f"{USER_SERVICE_URL}/api/users/{member_id}")
            if response.status_code == 200:
                members_info.append(response.json())
            else:
                members_info.append({"id": member_id, "username": "Unknown User"})

        except requests.exceptions.RequestException:
            members_info.append({"id": member_id, "username": "Unknown User"})
    
    result = group.copy()
    result['members_info'] = members_info
    return jsonify(result), 200

@app.route('/groups/user/<user_id>', methods=['GET'])
def get_user_groups(user_id):
    """Get all groups where a user is a member."""
    user_id = str(user_id)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM `groups`')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    user_groups = []
    for row in rows:
        members = json.loads(row['members'])
        if user_id in members:
            group = {
                "id": row['id'],
                "name": row['name'],
                "creator_id": row['creator_id'],
                "members": members
            }
            user_groups.append(group)
    return jsonify(user_groups), 200

@app.route('/groups/<group_id>/members', methods=['POST'])
def add_member(group_id):
    data = request.get_json()
    user_id = str(data.get('user_id'))
    added_by = str(data.get('added_by'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM `groups` WHERE id = %s', (group_id,))
    row = cursor.fetchone()
    group = {
        "id": row['id'],
        "name": row['name'],
        "creator_id": row['creator_id'],
        "members": json.loads(row['members'])
    }

    if added_by not in group['members']:
        cursor.close()
        conn.close()
        return jsonify({"error": "Only group members can add users"}), 403

    if user_id in group['members']:
        cursor.close()
        conn.close()
        return jsonify({"message": "User is already a member of this group"}), 200

    group['members'].append(user_id)
    cursor.execute('UPDATE `groups` SET members = %s WHERE id = %s', (json.dumps(group['members']), group_id))

    conn.commit()
    cursor.close()
    conn.close()
   
    return jsonify({
        "message": "User added to group successfully",
        "group": group
    }), 200

@app.route('/groups/<group_id>/members/<user_id>', methods=['DELETE'])
def remove_member(group_id, user_id):
    user_id = str(user_id)
    removed_by = str(request.args.get('removed_by'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM `groups` WHERE id = %s', (group_id,))
    row = cursor.fetchone()
    group = {
        "id": row['id'],
        "name": row['name'],
        "creator_id": row['creator_id'],
        "members": json.loads(row['members'])
    }
    
    if removed_by not in group['members']:
        cursor.close()
        conn.close()
        return jsonify({"error": "Only group members can remove users"}), 403
    
    if user_id not in group['members']:
        cursor.close()
        conn.close()
        return jsonify({"error": "User is not a member of this group"}), 404
    
    group['members'].remove(user_id)
    
    if not group['members']: # case of no members left
        cursor.execute('DELETE FROM `groups` WHERE id = %s', (group_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Group deleted as last member left"}), 200
    else:
        cursor.execute('UPDATE `groups` SET members = %s WHERE id = %s', (json.dumps(group['members']), group_id))
        conn.commit()
        cursor.close()
        conn.close()
   
    return jsonify({
        "message": "User removed from group successfully",
        "group": group
    }), 200

@app.route('/groups/<group_id>/name', methods=['PUT'])
def update_group_name(group_id):

    data = request.get_json()
    new_name = data.get('name')
    updated_by = str(data.get('updated_by'))

    if not new_name or not updated_by:
        return jsonify({"error": "New name and updated_by are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM `groups` WHERE id = %s', (group_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Group not found"}), 404

    group = {
        "id": row['id'],
        "name": row['name'],
        "creator_id": row['creator_id'],
        "members": json.loads(row['members'])
    }

    if updated_by not in group['members']:
        cursor.close()
        conn.close()
        return jsonify({"error": "Only group members can update the group name"}), 403

    old_name = group['name']
    group['name'] = new_name

    cursor.execute('UPDATE `groups` SET name = %s WHERE id = %s', (new_name, group_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "message": "Group name updated successfully",
        "group": group
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'group-chat-service'}), 200

if __name__ == '__main__':
    create_groups_table()
    app.run(host='0.0.0.0', port=5004, debug=True) 