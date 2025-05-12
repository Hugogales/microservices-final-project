document.addEventListener('DOMContentLoaded', function() {
    // App state
    const state = {
        activeTab: 'conversations',
        activeConversation: null,
        activeConversationType: null, // 'direct' or 'group'
        users: [],
        conversations: [],
        groups: [],
        messages: [],
        currentUser: {
            id: document.body.getAttribute('data-user-id'),
            username: document.body.getAttribute('data-username')
        }
    };
    
    // DOM Elements
    const conversationTab = document.querySelector('[data-tab="conversations"]');
    const groupsTab = document.querySelector('[data-tab="groups"]');
    const conversationsTabContent = document.getElementById('conversations-tab');
    const groupsTabContent = document.getElementById('groups-tab');
    const conversationList = document.getElementById('conversation-list');
    const groupList = document.getElementById('group-list');
    const messagesContainer = document.getElementById('messages-container');
    const chatTitle = document.getElementById('chat-title');
    const chatActions = document.getElementById('chat-actions');
    const messageInput = document.getElementById('message-input');
    const messageInputContainer = document.getElementById('message-input-container');
    const sendMessageBtn = document.getElementById('send-message-btn');
    
    // Modals
    const createGroupBtn = document.getElementById('create-group-btn');
    const createGroupModal = document.getElementById('create-group-modal');
    const closeGroupModalBtn = document.getElementById('close-group-modal');
    const createGroupSubmitBtn = document.getElementById('create-group-submit');
    const groupNameInput = document.getElementById('group-name');
    const userList = document.getElementById('user-list');
    
    const groupInfoModal = document.getElementById('group-info-modal');
    const closeGroupInfoModalBtn = document.getElementById('close-group-info-modal');
    const groupInfoTitle = document.getElementById('group-info-title');
    const editGroupNameInput = document.getElementById('edit-group-name');
    const updateGroupNameBtn = document.getElementById('update-group-name-btn');
    const groupMembersList = document.getElementById('group-members-list');
    const addMembersList = document.getElementById('add-members-list');
    
    // Tab switching
    conversationTab.addEventListener('click', function() {
        setActiveTab('conversations');
    });
    
    groupsTab.addEventListener('click', function() {
        setActiveTab('groups');
    });
    
    function setActiveTab(tabName) {
        state.activeTab = tabName;
        
        // Update UI
        if (tabName === 'conversations') {
            conversationTab.classList.add('active');
            groupsTab.classList.remove('active');
            conversationsTabContent.style.display = 'block';
            groupsTabContent.style.display = 'none';
        } else {
            conversationTab.classList.remove('active');
            groupsTab.classList.add('active');
            conversationsTabContent.style.display = 'none';
            groupsTabContent.style.display = 'block';
        }
        
        // Reset chat area when switching tabs
        resetChatArea();
    }
    
    // Data loading functions
    function loadUsers() {
        fetch('/api/users')
            .then(response => response.json())
            .then(data => {
                state.users = data;
                renderConversations();
            })
            .catch(error => {
                console.error('Error loading users:', error);
                conversationList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="fas fa-exclamation-circle"></i></div>
                        <div class="empty-state-text">Failed to load users</div>
                        <div class="empty-state-subtext">Please try again later</div>
                    </div>
                `;
            });
    }
    
    function loadGroups() {
        fetch('/api/groups')
            .then(response => response.json())
            .then(data => {
                state.groups = data;
                renderGroups();
            })
            .catch(error => {
                console.error('Error loading groups:', error);
                groupList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="fas fa-exclamation-circle"></i></div>
                        <div class="empty-state-text">Failed to load groups</div>
                        <div class="empty-state-subtext">Please try again later</div>
                    </div>
                `;
            });
    }
    
    function loadDirectMessages(userId) {
        // Ensure userId is a number as expected by the API
        const numericUserId = parseInt(userId);
        
        fetch(`/api/messages/conversation/${numericUserId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Direct messages loaded:', data.length);
                state.messages = data;
                renderMessages();
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                messagesContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="fas fa-exclamation-circle"></i></div>
                        <div class="empty-state-text">Failed to load messages</div>
                        <div class="empty-state-subtext">Please try again later</div>
                    </div>
                `;
            });
    }
    
    function loadGroupMessages(groupId) {
        fetch(`/api/groups/${groupId}/messages`)
            .then(response => response.json())
            .then(data => {
                state.messages = data;
                renderMessages();
            })
            .catch(error => {
                console.error('Error loading group messages:', error);
                messagesContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="fas fa-exclamation-circle"></i></div>
                        <div class="empty-state-text">Failed to load messages</div>
                        <div class="empty-state-subtext">Please try again later</div>
                    </div>
                `;
            });
    }
    
    // Rendering functions
    function renderConversations() {
        if (!state.users || state.users.length === 0) {
            conversationList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon"><i class="fas fa-users"></i></div>
                    <div class="empty-state-text">No users available</div>
                    <div class="empty-state-subtext">Please try again later</div>
                </div>
            `;
            return;
        }
        
        let html = '';
        state.users.forEach(user => {
            if (user.id === state.currentUser.id) return;
            
            const isActive = state.activeConversation === user.id && state.activeConversationType === 'direct';
            const initials = user.username ? user.username.substring(0, 2).toUpperCase() : 'UN';
            
            html += `
                <div class="conversation-item ${isActive ? 'active' : ''}" data-id="${user.id}" data-type="direct">
                    <div class="conversation-avatar">${initials}</div>
                    <div class="conversation-details">
                        <div class="conversation-name">${user.username || 'Unknown User'}</div>
                    </div>
                </div>
            `;
        });
        
        conversationList.innerHTML = html;
        
        // Add event listeners
        document.querySelectorAll('#conversation-list .conversation-item').forEach(item => {
            item.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                const type = this.getAttribute('data-type');
                if (type === 'direct') {
                    openDirectConversation(id);
                }
            });
        });
    }
    
    function renderGroups() {
        if (!state.groups || state.groups.length === 0) {
            groupList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon"><i class="fas fa-users"></i></div>
                    <div class="empty-state-text">No groups yet</div>
                    <div class="empty-state-subtext">Create a new group to start a group chat</div>
                </div>
            `;
            return;
        }
        
        let html = '';
        state.groups.forEach(group => {
            const isActive = state.activeConversation === group.id && state.activeConversationType === 'group';
            const initials = group.name.substring(0, 2).toUpperCase();
            
            html += `
                <div class="conversation-item ${isActive ? 'active' : ''}" data-id="${group.id}" data-type="group">
                    <div class="conversation-avatar">${initials}</div>
                    <div class="conversation-details">
                        <div class="conversation-name">${group.name}</div>
                        <div class="conversation-message">${group.members.length} members</div>
                    </div>
                </div>
            `;
        });
        
        groupList.innerHTML = html;
        
        // Add event listeners
        document.querySelectorAll('#group-list .conversation-item').forEach(item => {
            item.addEventListener('click', function() {
                const groupId = this.getAttribute('data-id');
                openGroupConversation(groupId);
            });
        });
    }
    
    function renderMessages() {
        if (!state.messages || state.messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon"><i class="fas fa-comment-dots"></i></div>
                    <div class="empty-state-text">No messages yet</div>
                    <div class="empty-state-subtext">Be the first to say hello!</div>
                </div>
            `;
            return;
        }
        
        let html = '';
        let currentDate = null;
        let currentSender = null;
        
        // Debug current user ID
        console.log('Current user ID in renderMessages:', state.currentUser.id);
        
        state.messages.forEach(message => {
            // Convert sender_id to string for consistent comparison
            const senderId = String(message.sender_id);
            const currentUserId = String(state.currentUser.id);
            
            const messageDate = new Date(message.timestamp).toDateString();
            const isCurrentUser = senderId === currentUserId;
            
            console.log(`Message from ${senderId}, current user: ${currentUserId}, is current: ${isCurrentUser}`);
            
            // Add date separator if needed
            if (messageDate !== currentDate) {
                html += `<div class="system-message">${formatDate(message.timestamp)}</div>`;
                currentDate = messageDate;
                currentSender = null; // Reset sender after date change
            }
            
            // Special handling for system messages (sender_id is 'system')
            if (senderId === 'system') {
                html += `<div class="system-message">${message.content}</div>`;
                currentSender = null; // Reset sender after system message
                return;
            }
            
            // Start new message group if sender changed - Always show sender name
            if (senderId !== currentSender) {
                currentSender = senderId;
                
                // Show sender name for all messages, with appropriate alignment
                const senderName = isCurrentUser ? 'You' : (message.sender_username || 'Unknown User');
                const senderClass = isCurrentUser ? 'outgoing-sender' : 'incoming-sender';
                html += `<div class="message-sender ${senderClass}">${senderName}</div>`;
            }
            
            html += `
                <div class="message ${isCurrentUser ? 'message-outgoing' : 'message-incoming'}">
                    <div class="message-bubble">
                        ${message.content}
                        <div class="message-time">${formatTime(message.timestamp)}</div>
                    </div>
                </div>
            `;
        });
        
        messagesContainer.innerHTML = html;
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function renderUserList() {
        if (!state.users || state.users.length === 0) {
            userList.innerHTML = `
                <div class="empty-state">
                    <p>No users available</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        state.users.forEach(user => {
            if (user.id !== state.currentUser.id) {
                html += `
                    <div class="user-item">
                        <input type="checkbox" id="user-${user.id}" class="user-checkbox" value="${user.id}">
                        <label for="user-${user.id}">${user.username}</label>
                    </div>
                `;
            }
        });
        
        userList.innerHTML = html;
    }
    
    function renderGroupMembersList(group) {
        if (!group || !group.members_info) {
            groupMembersList.innerHTML = '<p>Failed to load members</p>';
            return;
        }
        
        let html = '';
        group.members_info.forEach(member => {
            const isCurrentUser = member.id === state.currentUser.id;
            const isCreator = group.creator_id === member.id;
            
            html += `
                <div class="user-item">
                    <span>${member.username} ${isCreator ? ' (Creator)' : ''}</span>
                    ${!isCurrentUser && !isCreator ? 
                        `<button class="remove-member-btn" data-id="${member.id}">
                            <i class="fas fa-times"></i>
                        </button>` : 
                        ''}
                </div>
            `;
        });
        
        groupMembersList.innerHTML = html;
        
        // Add event listeners for remove buttons
        document.querySelectorAll('.remove-member-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const memberId = this.getAttribute('data-id');
                removeGroupMember(group.id, memberId);
            });
        });
    }
    
    function renderAddMembersList(group) {
        if (!state.users || state.users.length === 0) {
            addMembersList.innerHTML = '<p>No users available</p>';
            return;
        }
        
        const memberIds = group.members_info.map(m => m.id);
        const availableUsers = state.users.filter(user => 
            !memberIds.includes(user.id) && user.id !== state.currentUser.id);
        
        if (availableUsers.length === 0) {
            addMembersList.innerHTML = '<p>All users are already in this group</p>';
            return;
        }
        
        let html = '';
        availableUsers.forEach(user => {
            html += `
                <div class="user-item">
                    <span>${user.username}</span>
                    <button class="add-member-btn" data-id="${user.id}">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            `;
        });
        
        addMembersList.innerHTML = html;
        
        // Add event listeners for add buttons
        document.querySelectorAll('.add-member-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const userId = this.getAttribute('data-id');
                addGroupMember(group.id, userId);
            });
        });
    }
    
    // Action functions
    function openDirectConversation(userId) {
        userId = String(userId);
        state.activeConversation = userId;
        state.activeConversationType = 'direct';
        
        // Update UI
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.conversation-item[data-id="${userId}"][data-type="direct"]`)?.classList.add('active');
        
        // Find the user
        const user = state.users.find(u => String(u.id) === userId);
        if (user) {
            chatTitle.textContent = `Chat with ${user.username}`;
        } else {
            chatTitle.textContent = `Direct Message`;
        }
        
        // Show the message input
        messageInputContainer.style.display = 'flex';
        
        // Hide group chat actions
        chatActions.style.display = 'none';
        
        // Load messages
        loadDirectMessages(userId);
    }
    
    function openGroupConversation(groupId) {
        state.activeConversation = groupId;
        state.activeConversationType = 'group';
        
        // Update UI
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.conversation-item[data-id="${groupId}"][data-type="group"]`)?.classList.add('active');
        
        // Find the group
        const group = state.groups.find(g => g.id === groupId);
        if (group) {
            chatTitle.textContent = `Group: ${group.name}`;
            
            // Show group chat actions
            chatActions.innerHTML = `
                <button id="group-info-btn">
                    <i class="fas fa-info-circle"></i> Group Info
                </button>
            `;
            chatActions.style.display = 'block';
            
            // Add event listener for group info button
            document.getElementById('group-info-btn')?.addEventListener('click', function() {
                openGroupInfoModal(groupId);
            });
        }
        
        // Show the message input
        messageInputContainer.style.display = 'flex';
        
        // Load messages
        loadGroupMessages(groupId);
    }
    
    function sendMessage() {
        const content = messageInput.value.trim();
        if (!content) return;
        
        let url, data;
        
        if (state.activeConversationType === 'direct') {
            url = '/api/messages/send';
            data = {
                sender_id: state.currentUser.id, // Send as string to match backend expectations
                recipient_id: state.activeConversation,
                content: content
            };
        } else if (state.activeConversationType === 'group') {
            url = `/api/groups/${state.activeConversation}/messages/send`;
            data = {
                sender_id: state.currentUser.id, // Send as string to match backend expectations
                content: content
            };
        } else {
            console.error('No active conversation');
            return;
        }
        
        // Add loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'message message-outgoing';
        loadingIndicator.innerHTML = `
            <div class="message-bubble">
                <div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Sending...</div>
            </div>
        `;
        messagesContainer.appendChild(loadingIndicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            // Remove loading indicator
            messagesContainer.removeChild(loadingIndicator);
            
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Failed to send message');
                });
            }
            return response.json();
        })
        .then(result => {
            // Clear input
            messageInput.value = '';
            
            // Reload conversation
            if (state.activeConversationType === 'direct') {
                loadDirectMessages(state.activeConversation);
            } else {
                loadGroupMessages(state.activeConversation);
            }
            
            // Immediately add the sent message to the UI for better feedback
            const sentMessage = {
                id: result.id || Date.now(), // Use server-provided ID if available
                sender_id: state.currentUser.id,
                content: content,
                timestamp: new Date().toISOString(),
                sender_username: state.currentUser.username
            };
            
            // Add to messages array
            state.messages.push(sentMessage);
            
            // Update UI with the new message
            renderMessages();
        })
        .catch(error => {
            console.error('Error sending message:', error);
            alert(error.message || 'Failed to send message. Please try again.');
        });
    }
    
    function createGroup() {
        const name = groupNameInput.value.trim();
        if (!name) {
            alert('Please enter a group name');
            return;
        }
        
        // Get selected users
        const selectedUsers = [];
        document.querySelectorAll('#user-list .user-checkbox:checked').forEach(checkbox => {
            selectedUsers.push(checkbox.value);
        });
        
        if (selectedUsers.length === 0) {
            alert('Please select at least one member');
            return;
        }
        
        fetch('/api/groups/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                members: selectedUsers
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to create group');
            }
            return response.json();
        })
        .then(result => {
            // Close modal and reset form
            createGroupModal.style.display = 'none';
            groupNameInput.value = '';
            document.querySelectorAll('#user-list .user-checkbox:checked').forEach(checkbox => {
                checkbox.checked = false;
            });
            
            // Reload groups and switch to groups tab
            loadGroups();
            setActiveTab('groups');
            
            // Open the new group conversation
            if (result.group_id) {
                setTimeout(() => {
                    openGroupConversation(result.group_id);
                }, 500);
            }
        })
        .catch(error => {
            console.error('Error creating group:', error);
            alert('Failed to create group');
        });
    }
    
    function openGroupInfoModal(groupId) {
        fetch(`/api/groups/${groupId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load group info');
                }
                return response.json();
            })
            .then(group => {
                groupInfoTitle.textContent = `Group: ${group.name}`;
                editGroupNameInput.value = group.name;
                
                // Render group members
                renderGroupMembersList(group);
                
                // Render users not in group
                renderAddMembersList(group);
                
                // Setup update name button
                updateGroupNameBtn.onclick = function() {
                    updateGroupName(groupId, editGroupNameInput.value.trim());
                };
                
                // Show modal
                groupInfoModal.style.display = 'flex';
            })
            .catch(error => {
                console.error('Error loading group info:', error);
                alert('Failed to load group information');
            });
    }
    
    function updateGroupName(groupId, newName) {
        if (!newName) {
            alert('Please enter a valid group name');
            return;
        }
        
        fetch(`/api/groups/${groupId}/update-name`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: newName
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to update group name');
            }
            return response.json();
        })
        .then(result => {
            // Update UI
            groupInfoTitle.textContent = `Group: ${newName}`;
            chatTitle.textContent = `Group: ${newName}`;
            
            // Reload groups
            loadGroups();
            
            // Reload messages
            loadGroupMessages(groupId);
            
            alert('Group name updated successfully');
        })
        .catch(error => {
            console.error('Error updating group name:', error);
            alert('Failed to update group name');
        });
    }
    
    function addGroupMember(groupId, userId) {
        fetch(`/api/groups/${groupId}/add-member`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to add member');
            }
            return response.json();
        })
        .then(result => {
            // Reload the group info
            openGroupInfoModal(groupId);
            
            // Reload messages
            loadGroupMessages(groupId);
        })
        .catch(error => {
            console.error('Error adding member:', error);
            alert('Failed to add member to group');
        });
    }
    
    function removeGroupMember(groupId, userId) {
        if (!confirm('Are you sure you want to remove this member from the group?')) {
            return;
        }
        
        fetch(`/api/groups/${groupId}/remove-member/${userId}?removed_by=${state.currentUser.id}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Failed to remove member');
                });
            }
            return response.json();
        })
        .then(result => {
            // Reload the group info
            openGroupInfoModal(groupId);
            
            // Reload messages
            loadGroupMessages(groupId);
        })
        .catch(error => {
            console.error('Error removing member:', error);
            alert(error.message || 'Failed to remove member from group');
        });
    }
    
    function resetChatArea() {
        state.activeConversation = null;
        state.activeConversationType = null;
        chatTitle.textContent = 'Select a conversation';
        chatActions.style.display = 'none';
        messagesContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon"><i class="fas fa-comment-dots"></i></div>
                <div class="empty-state-text">Select a conversation to start messaging</div>
            </div>
        `;
        messageInputContainer.style.display = 'none';
    }
    
    // Helper functions
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    function formatDate(timestamp) {
        const date = new Date(timestamp);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        
        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString();
        }
    }
    
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return formatTime(timestamp);
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            return days[date.getDay()];
        } else {
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }
    }
    
    // Event listeners
    sendMessageBtn.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Group modal events
    createGroupBtn.addEventListener('click', function() {
        renderUserList();
        createGroupModal.style.display = 'flex';
    });
    
    closeGroupModalBtn.addEventListener('click', function() {
        createGroupModal.style.display = 'none';
    });
    
    createGroupSubmitBtn.addEventListener('click', createGroup);
    
    // Group info modal events
    closeGroupInfoModalBtn.addEventListener('click', function() {
        groupInfoModal.style.display = 'none';
    });
    
    // Close modals when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === createGroupModal) {
            createGroupModal.style.display = 'none';
        } else if (e.target === groupInfoModal) {
            groupInfoModal.style.display = 'none';
        }
    });
    
    // Initial data loading
    loadUsers();
    loadGroups();
    
    // Set user data as attributes
    document.body.setAttribute('data-user-id', state.currentUser.id);
    document.body.setAttribute('data-username', state.currentUser.username);
    
    // Remove the polling for conversations since we don't need it
    setInterval(() => {
        if (state.activeConversationType === 'direct') {
            loadDirectMessages(state.activeConversation);
        } else if (state.activeConversationType === 'group') {
            loadGroupMessages(state.activeConversation);
        }
        
        // Only refresh groups
        loadGroups();
    }, 10000); // Every 10 seconds
}); 