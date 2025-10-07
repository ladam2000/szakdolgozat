import { userManager, signOutRedirect, getUser, isAuthenticated } from './auth.js';

// Configuration - Replace with your API Gateway URL after deployment
const API_URL = 'https://fbiwuqkkwu6yqutfmr25anrnuy0hwfnl.lambda-url.eu-central-1.on.aws/';

// Global state
let currentUser = null;
let sessionId = localStorage.getItem('sessionId');
if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.getItem('sessionId', sessionId);
}

// DOM elements
const loginScreen = document.getElementById('loginScreen');
const appScreen = document.getElementById('appScreen');
const signInButton = document.getElementById('signInButton');
const signOutButton = document.getElementById('signOutButton');
const userEmail = document.getElementById('userEmail');
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const resetButton = document.getElementById('resetButton');

// Initialize app
async function initializeApp() {
    // Check if returning from Cognito redirect
    if (window.location.search.includes('code=')) {
        try {
            currentUser = await userManager.signinCallback();
            window.history.replaceState({}, document.title, window.location.pathname);
            showApp();
            return;
        } catch (error) {
            console.error('Sign in callback error:', error);
            showLogin();
            return;
        }
    }
    
    // Check authentication status
    const authenticated = await isAuthenticated();
    
    if (authenticated) {
        currentUser = await getUser();
        showApp();
    } else {
        showLogin();
    }
}

// Show login screen
function showLogin() {
    loginScreen.style.display = 'flex';
    appScreen.style.display = 'none';
}

// Show main app
function showApp() {
    loginScreen.style.display = 'none';
    appScreen.style.display = 'block';
    
    if (currentUser) {
        userEmail.textContent = currentUser.profile?.email || 'User';
    }
    
    addSystemMessage('Welcome! I can help you plan flights, hotels, and activities. What would you like to do?');
}

// Event listeners
signInButton.addEventListener('click', async () => {
    await userManager.signinRedirect();
});

signOutButton.addEventListener('click', async () => {
    await signOutRedirect();
});

sendButton.addEventListener('click', sendMessage);
resetButton.addEventListener('click', resetSession);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initialize on load
initializeApp();

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Check authentication
    if (!currentUser) {
        addSystemMessage('Please sign in to continue');
        return;
    }
    
    // Disable input
    messageInput.disabled = true;
    sendButton.disabled = true;
    
    // Add user message
    addMessage(message, 'user');
    messageInput.value = '';
    
    try {
        // Show loading indicator
        const loadingId = addLoadingMessage();
        
        // Send to API with auth token
        // Lambda Function URL doesn't support paths, send directly
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.access_token}`,
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
            }),
        });
        
        // Remove loading indicator
        removeMessage(loadingId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant response
        addMessage(data.response, 'assistant');
        
    } catch (error) {
        console.error('Error:', error);
        addSystemMessage('Sorry, there was an error processing your request. Please try again.');
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

async function resetSession() {
    if (!confirm('Are you sure you want to reset the conversation?')) {
        return;
    }
    
    try {
        // For reset, just generate new session ID locally
        // Lambda Function URL doesn't support routing
        // await fetch(API_URL, {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        //     body: JSON.stringify({
        //         session_id: sessionId,
        //         reset: true,
        //     }),
        // });
        
        // Clear messages
        messagesContainer.innerHTML = '';
        
        // Generate new session ID
        sessionId = generateSessionId();
        localStorage.setItem('sessionId', sessionId);
        
        addSystemMessage('Conversation reset. How can I help you plan your trip?');
        
    } catch (error) {
        console.error('Error:', error);
        addSystemMessage('Error resetting conversation. Please refresh the page.');
    }
}

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    // Convert markdown to HTML
    let formattedText = text
        // Headings (must be done before newlines)
        .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
        .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
        // Lists (must be done before newlines)
        .replace(/^- (.*?)$/gm, '<li>$1</li>')
        // Bold and italic
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Code
        .replace(/`(.*?)`/g, '<code>$1</code>')
        // Convert remaining newlines to <br>
        .replace(/\n/g, '<br>');
    
    // Wrap consecutive <li> elements in <ul>
    formattedText = formattedText.replace(/(<li>.*?<\/li>)(<br>)?(?=<li>|$)/g, '$1');
    formattedText = formattedText.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
    
    messageDiv.innerHTML = formattedText;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv.id = generateId();
}

function addSystemMessage(text) {
    return addMessage(text, 'system');
}

function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = '<span class="loading"></span> <span class="loading"></span> <span class="loading"></span>';
    const id = generateId();
    messageDiv.id = id;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function generateId() {
    return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}
