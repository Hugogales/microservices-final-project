import os
import requests
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from functools import wraps

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Service URLs from environment variables with defaults for local development
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://localhost:5001')
MESSAGE_SERVICE_URL = os.environ.get('MESSAGE_SERVICE_URL', 'http://localhost:5002')
GROUP_CHAT_SERVICE_URL = os.environ.get('GROUP_CHAT_SERVICE_URL', 'http://localhost:5004')

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/test')
def test_page():
    """A test page to check service connectivity"""
    user_service_status = "Unknown"
    message_service_status = "Unknown"
    group_chat_service_status = "Unknown"
    
    try:
        user_response = requests.get(f'{USER_SERVICE_URL}/health', timeout=3)
        user_service_status = f"Connected (Status: {user_response.status_code})" if user_response.status_code == 200 else f"Error (Status: {user_response.status_code})"
    except Exception as e:
        user_service_status = f"Error: {str(e)}"
    
    try:
        message_response = requests.get(f'{MESSAGE_SERVICE_URL}/health', timeout=3)
        message_service_status = f"Connected (Status: {message_response.status_code})" if message_response.status_code == 200 else f"Error (Status: {message_response.status_code})"
    except Exception as e:
        message_service_status = f"Error: {str(e)}"
    
    try:
        group_chat_response = requests.get(f'{GROUP_CHAT_SERVICE_URL}/health', timeout=3)
        group_chat_service_status = f"Connected (Status: {group_chat_response.status_code})" if group_chat_response.status_code == 200 else f"Error (Status: {group_chat_response.status_code})"
    except Exception as e:
        group_chat_service_status = f"Error: {str(e)}"
    
    html = f"""
    <html>
        <head>
            <title>Frontend Service Test</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #4CAF50; text-align: center; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .status-box {{ border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 5px; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .status-title {{ font-weight: bold; }}
                .service-url {{ color: #666; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Frontend Service Test Page</h1>
                
                <div class="status-box">
                    <p class="status-title">User Service:</p>
                    <p class="service-url">URL: {USER_SERVICE_URL}</p>
                    <p class="{'success' if 'Connected' in user_service_status else 'error'}">{user_service_status}</p>
                </div>
                
                <div class="status-box">
                    <p class="status-title">Message Service:</p>
                    <p class="service-url">URL: {MESSAGE_SERVICE_URL}</p>
                    <p class="{'success' if 'Connected' in message_service_status else 'error'}">{message_service_status}</p>
                </div>
                
                <div class="status-box">
                    <p class="status-title">Group Chat Service:</p>
                    <p class="service-url">URL: {GROUP_CHAT_SERVICE_URL}</p>
                    <p class="{'success' if 'Connected' in group_chat_service_status else 'error'}">{group_chat_service_status}</p>
                </div>
                
                <p><a href="/login">Go to Login Page</a></p>
            </div>
        </body>
    </html>
    """
    return html

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter username and password', 'error')
            return render_template('login.html')
        
        try:
            response = requests.post(
                f'{USER_SERVICE_URL}/api/users/login',
                json={'username': username, 'password': password}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                session['user_id'] = user_data['id']
                session['username'] = user_data['username']
                
                # Store authentication token if provided by the user service
                if 'token' in user_data:
                    session['token'] = user_data['token']
                    
                return redirect(url_for('chat'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
        except requests.exceptions.RequestException as e:
            flash(f'Error connecting to the user service: {str(e)}', 'error')
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('Please enter username and password', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        try:
            response = requests.post(
                f'{USER_SERVICE_URL}/api/users/register',
                json={'username': username, 'password': password}
            )
            
            if response.status_code == 201:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                error_data = response.json()
                flash(f'Registration failed: {error_data.get("error", "Unknown error")}', 'error')
        except requests.exceptions.RequestException as e:
            flash(f'Error connecting to the user service: {str(e)}', 'error')
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        try:
            requests.post(f'{USER_SERVICE_URL}/api/users/logout')
        except:
            pass  # Continue even if the request fails
        
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    try:
        # Try to test connectivity to services
        user_service_healthy = False
        message_service_healthy = False
        group_chat_service_healthy = False
        
        try:
            user_response = requests.get(f'{USER_SERVICE_URL}/health', timeout=2)
            user_service_healthy = user_response.status_code == 200
        except Exception as e:
            user_service_healthy = False
            print(f"Error connecting to user service: {e}")
        
        try:
            message_response = requests.get(f'{MESSAGE_SERVICE_URL}/health', timeout=2)
            message_service_healthy = message_response.status_code == 200
        except Exception as e:
            message_service_healthy = False
            print(f"Error connecting to message service: {e}")
            
        try:
            group_chat_response = requests.get(f'{GROUP_CHAT_SERVICE_URL}/health', timeout=2)
            group_chat_service_healthy = group_chat_response.status_code == 200
        except Exception as e:
            group_chat_service_healthy = False
            print(f"Error connecting to group chat service: {e}")
        
        if not user_service_healthy or not message_service_healthy or not group_chat_service_healthy:
            error_html = f"""
            <html>
                <head>
                    <title>Service Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        h1 {{ color: red; }}
                        .error-box {{ border: 1px solid #ffcccc; padding: 20px; background-color: #fff0f0; margin-bottom: 20px; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <h1>Service Connection Error</h1>
                    
                    <div class="error-box">
                        <p>One or more required services are not available:</p>
                        <ul>
                            <li>User Service: {"Available" if user_service_healthy else "Not Available"}</li>
                            <li>Message Service: {"Available" if message_service_healthy else "Not Available"}</li>
                            <li>Group Chat Service: {"Available" if group_chat_service_healthy else "Not Available"}</li>
                        </ul>
                        <p>Please try again later or contact system administrator.</p>
                        <p><a href="/test">View Detailed Service Status</a></p>
                        <p><a href="/logout">Logout</a></p>
                    </div>
                </body>
            </html>
            """
            return error_html
        
        # Use index.html instead of chat.html
        print(f"Rendering index.html template for user: {session.get('username')}, id: {session.get('user_id')}")
        return render_template('index.html', username=session.get('username', 'User'), user_id=session.get('user_id'))
    except Exception as e:
        print(f"Exception in chat route: {str(e)}")
        return f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>An error occurred</h1>
                <p>{str(e)}</p>
                <p><a href="/logout">Logout</a></p>
            </body>
        </html>
        """

@app.route('/new-chat', methods=['GET', 'POST'])
@login_required
def new_chat():
    if request.method == 'POST':
        # This handles creating new direct chats or group chats
        chat_type = request.form.get('chat_type', 'direct')
        
        if chat_type == 'direct':
            recipient_id = request.form.get('recipient_id')
            if not recipient_id:
                flash('Please select a recipient', 'error')
                return redirect(url_for('new_chat'))
            
            # For direct chat, just redirect to the chat page with the recipient ID
            return redirect(url_for('chat') + f'?selected_user={recipient_id}')
        else:  # Group chat
            group_name = request.form.get('group_name')
            member_ids = request.form.getlist('group_members')
            
            if not group_name:
                flash('Please enter a group name', 'error')
                return redirect(url_for('new_chat'))
            
            if not member_ids:
                flash('Please select at least one group member', 'error')
                return redirect(url_for('new_chat'))
            
            # Make sure current user's ID is included
            current_user_id = str(session['user_id'])
            if current_user_id not in member_ids:
                member_ids.append(current_user_id)
            
            try:
                # Create the group via the group chat service
                response = requests.post(
                    f'{GROUP_CHAT_SERVICE_URL}/groups',
                    json={
                        'name': group_name,
                        'creator_id': current_user_id,
                        'members': member_ids
                    }
                )
                
                if response.status_code == 201:
                    group_data = response.json()
                    group_id = group_data.get('group_id')
                    flash(f'Group "{group_name}" created successfully', 'success')
                    
                    # For better debugging, log the group details
                    print(f"Created group: {group_data}")
                    
                    # Redirect to chat with the new group selected
                    return redirect(url_for('chat') + f'?selected_group={group_id}')
                else:
                    error_data = response.json()
                    flash(f'Failed to create group: {error_data.get("error", "Unknown error")}', 'error')
            except requests.exceptions.RequestException as e:
                flash(f'Error connecting to the group chat service: {str(e)}', 'error')
    
    # GET request or form submission failed - show the new chat form
    try:
        # Get list of users for the form
        current_user_id = str(session['user_id'])
        response = requests.get(f'{USER_SERVICE_URL}/api/users?current_user_id={current_user_id}')
        users = response.json() if response.status_code == 200 else []
        
        # Filter out the current user
        users = [user for user in users if str(user['id']) != str(session['user_id'])]
        
        return render_template('new_chat.html', users=users)
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching users: {str(e)}', 'error')
        return redirect(url_for('chat'))

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    try:
        current_user_id = str(session['user_id'])
        response = requests.get(f'{USER_SERVICE_URL}/api/users?current_user_id={current_user_id}')
        if response.status_code == 200:
            users = response.json()
            # Filter out current user
            users = [user for user in users if str(user['id']) != str(session['user_id'])]
            return jsonify(users)
        else:
            return jsonify({'error': 'Failed to fetch users'}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/conversations', methods=['GET'])
@login_required
def get_conversations():
    try:
        current_user_id = str(session['user_id'])
        
        # Get direct message conversations
        dm_response = requests.get(f'{MESSAGE_SERVICE_URL}/api/messages/conversations?user_id={current_user_id}')
        dm_conversations = dm_response.json() if dm_response.status_code == 200 else []
        
        # Get group conversations
        group_response = requests.get(f'{GROUP_CHAT_SERVICE_URL}/groups/user/{current_user_id}')
        
        # Add debug logging for group API response
        print(f"Groups API response status: {group_response.status_code}")
        if group_response.status_code != 200:
            print(f"Groups API error: {group_response.text}")
        
        groups = group_response.json() if group_response.status_code == 200 else []
        print(f"User {current_user_id} groups: {len(groups)}")
        
        # Format group data to match the conversation format
        group_conversations = []
        for group in groups:
            # Get the last message for each group (if available)
            try:
                last_msg_response = requests.get(f'{MESSAGE_SERVICE_URL}/api/messages/group/{group["id"]}?user_id={current_user_id}')
                group_messages = last_msg_response.json() if last_msg_response.status_code == 200 else []
                
                last_message = {
                    'content': 'No messages yet',
                    'timestamp': group['updated_at'],
                    'is_sent_by_me': False
                }
                
                if group_messages:
                    latest_msg = group_messages[-1]  # Get the most recent message
                    last_message = {
                        'content': latest_msg['content'],
                        'timestamp': latest_msg['timestamp'],
                        'is_sent_by_me': str(latest_msg['sender_id']) == current_user_id
                    }
            except Exception as e:
                print(f"Error getting messages for group {group['id']}: {e}")
                last_message = {
                    'content': 'No messages yet',
                    'timestamp': group['updated_at'],
                    'is_sent_by_me': False
                }
            
            # Add debug information
            print(f"Adding group to conversations: {group['id']} - {group['name']}")
            
            group_conversations.append({
                'group_id': group['id'],
                'name': group['name'],
                'last_message': last_message,
                'unread_count': 0,  # Not implemented
                'type': 'group',
                'member_count': len(group['members'])
            })
        
        # Combine and sort all conversations by timestamp (most recent first)
        all_conversations = dm_conversations + group_conversations
        
        # Debug output to see what conversations we have
        print(f"Total conversations: {len(all_conversations)} (DM: {len(dm_conversations)}, Groups: {len(group_conversations)})")
        
        # Sort by timestamp if possible
        try:
            all_conversations.sort(key=lambda x: x['last_message']['timestamp'], reverse=True)
        except Exception as e:
            print(f"Error sorting conversations: {e}")
        
        return jsonify(all_conversations)
    except Exception as e:
        print(f"Error in get_conversations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/conversation/<int:other_user_id>', methods=['GET'])
@login_required
def get_conversation(other_user_id):
    try:
        response = requests.get(
            f'{MESSAGE_SERVICE_URL}/api/messages/conversation/{other_user_id}?user_id={session["user_id"]}'
        )
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch messages'}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.json
        if not data.get('recipient_id') or not data.get('content'):
            return jsonify({'error': 'Recipient ID and content are required'}), 400
        
        response = requests.post(
            f'{MESSAGE_SERVICE_URL}/api/messages/send',
            json={
                'sender_id': session['user_id'],
                'recipient_id': data['recipient_id'],
                'content': data['content']
            }
        )
        
        if response.status_code == 201:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to send message'}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/current', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        'id': session['user_id'],
        'username': session.get('username', 'User')
    })

@app.route('/api/groups/create', methods=['POST'])
@login_required
def create_group():
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'error': 'Group name is required'}), 400
        
        # Ensure the current user is included in the members list
        members = data.get('members', [])
        if session['user_id'] not in members:
            members.append(session['user_id'])
        
        response = requests.post(
            f'{GROUP_CHAT_SERVICE_URL}/groups',
            json={
                'name': data['name'],
                'creator_id': session['user_id'],
                'members': members
            }
        )
        
        if response.status_code == 201:
            group_data = response.json()
            return jsonify({
                'group_id': group_data['group_id'],
                'message': 'Group created successfully'
            }), 201
        else:
            error_data = response.json()
            return jsonify({'error': error_data.get('error', 'Failed to create group')}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups')
@login_required
def get_groups():
    try:
        response = requests.get(f'{GROUP_CHAT_SERVICE_URL}/groups/user/{session["user_id"]}')
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch groups'}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<group_id>')
@login_required
def get_group(group_id):
    try:
        response = requests.get(f'{GROUP_CHAT_SERVICE_URL}/groups/{group_id}')
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch group'}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<group_id>/messages')
@login_required
def get_group_messages(group_id):
    try:
        current_user_id = str(session['user_id'])
        print(f"Fetching group messages for group {group_id}, user {current_user_id}")
        
        # First verify user is a member of the group to prevent unnecessary calls to message service
        group_response = requests.get(f'{GROUP_CHAT_SERVICE_URL}/groups/{group_id}')
        if group_response.status_code != 200:
            print(f"Group not found: {group_response.status_code}")
            return jsonify([]), 404  # Return empty array with 404 status
        
        group_data = group_response.json()
        group_members = [str(member) for member in group_data.get('members', [])]
        
        print(f"Group members: {group_members}")
        
        if current_user_id not in group_members:
            print(f"User {current_user_id} is not in group members")
            return jsonify([]), 403  # Return empty array with 403 status
        
        # Now fetch the messages
        response = requests.get(
            f'{MESSAGE_SERVICE_URL}/api/messages/group/{group_id}?user_id={current_user_id}'
        )
        
        print(f"Message service response: {response.status_code}")
        
        if response.status_code == 200:
            messages = response.json()
            # Ensure we always return an array, even if the API returns an object
            if not isinstance(messages, list):
                print(f"Converting non-list response to empty list: {messages}")
                messages = []
                
            print(f"Returning {len(messages)} messages")
            return jsonify(messages)
        else:
            print(f"Failed to fetch messages: {response.status_code}")
            # Always return an empty array for error conditions to prevent frontend errors
            return jsonify([]), response.status_code
    except Exception as e:
        print(f"Error in get_group_messages: {e}")
        # Return empty array to prevent frontend errors
        return jsonify([]), 500

@app.route('/api/groups/<group_id>/messages/send', methods=['POST'])
@login_required
def send_group_message(group_id):
    try:
        data = request.json
        if not data.get('content'):
            return jsonify({'error': 'Message content is required'}), 400
        
        # First verify user is a member of the group
        group_response = requests.get(f'{GROUP_CHAT_SERVICE_URL}/groups/{group_id}')
        if group_response.status_code != 200:
            return jsonify({'error': 'Failed to verify group membership'}), group_response.status_code
        
        group_data = group_response.json()
        current_user_id = str(session['user_id'])
        
        # Convert all member IDs to strings for consistent comparison
        group_members = [str(member_id) for member_id in group_data['members']]
        
        if current_user_id not in group_members:
            return jsonify({'error': 'You are not a member of this group'}), 403
        
        # Send the message
        response = requests.post(
            f'{MESSAGE_SERVICE_URL}/api/messages/group/send',
            json={
                'group_id': group_id,
                'sender_id': current_user_id,
                'content': data['content']
            }
        )
        
        # Log the response for debugging
        print(f"Group message response: {response.status_code}")
        if response.status_code != 201:
            try:
                error_data = response.json()
                print(f"Error data: {error_data}")
            except:
                print(f"Could not parse response: {response.text}")
        
        if response.status_code == 201:
            return jsonify(response.json())
        else:
            error_msg = "Failed to send message"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg = error_data['error']
            except:
                pass
            return jsonify({'error': error_msg}), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Request exception in send_group_message: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Unexpected exception in send_group_message: {e}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/groups/<group_id>/add-member', methods=['POST'])
@login_required
def add_group_member(group_id):
    try:
        data = request.json
        if not data.get('user_id'):
            return jsonify({'error': 'User ID is required'}), 400
        
        response = requests.post(
            f'{GROUP_CHAT_SERVICE_URL}/groups/{group_id}/members',
            json={
                'user_id': data['user_id'],
                'added_by': session['user_id']
            }
        )
        
        if response.status_code == 200:
            return jsonify({
                'message': 'User added to group successfully',
                'group': response.json().get('group')
            })
        else:
            error_data = response.json()
            return jsonify({'error': error_data.get('error', 'Failed to add user to group')}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<group_id>/remove-member/<user_id>', methods=['DELETE'])
@login_required
def remove_group_member(group_id, user_id):
    try:
        response = requests.delete(
            f'{GROUP_CHAT_SERVICE_URL}/groups/{group_id}/members/{user_id}?removed_by={session["user_id"]}'
        )
        
        if response.status_code == 200:
            return jsonify({
                'message': 'User removed from group successfully',
                'group': response.json().get('group')
            })
        else:
            error_data = response.json()
            return jsonify({'error': error_data.get('error', 'Failed to remove user from group')}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<group_id>/update-name', methods=['PUT'])
@login_required
def update_group_name(group_id):
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'error': 'Group name is required'}), 400
        
        response = requests.put(
            f'{GROUP_CHAT_SERVICE_URL}/groups/{group_id}/name',
            json={
                'name': data['name'],
                'updated_by': session['user_id']
            }
        )
        
        if response.status_code == 200:
            return jsonify({
                'message': 'Group name updated successfully',
                'group': response.json().get('group')
            })
        else:
            error_data = response.json()
            return jsonify({'error': error_data.get('error', 'Failed to update group name')}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 