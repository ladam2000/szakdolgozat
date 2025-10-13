import { userManager, signOutRedirect, getUser, isAuthenticated } from './auth.js';

const API_URL = 'https://fbiwuqkkwu6yqutfmr25anrnuy0hwfnl.lambda-url.eu-central-1.on.aws/';

let currentUser = null;
let sessionId = localStorage.getItem('sessionId');
if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem('sessionId', sessionId);
}

const loginScreen = document.getElementById('loginScreen');
const appScreen = document.getElementById('appScreen');
const signInButton = document.getElementById('signInButton');
const signOutButton = document.getElementById('signOutButton');
const userEmail = document.getElementById('userEmail');
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

async function initializeApp() {
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
    
    const authenticated = await isAuthenticated();
    
    if (authenticated) {
        currentUser = await getUser();
        showApp();
    } else {
        showLogin();
    }
}

function showLogin() {
    loginScreen.style.display = 'flex';
    appScreen.style.display = 'none';
}

async function showApp() {
    loginScreen.style.display = 'none';
    appScreen.style.display = 'block';
    
    if (currentUser) {
        userEmail.textContent = currentUser.profile?.email || 'User';
    }
    
    addSystemMessage('Welcome! I can help you plan flights, hotels, and activities. What would you like to do?');
}

signInButton.addEventListener('click', async () => {
    await userManager.signinRedirect();
});

signOutButton.addEventListener('click', async () => {
    await signOutRedirect();
});

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

initializeApp();

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    if (!currentUser) {
        addSystemMessage('Please sign in to continue');
        return;
    }
    
    messageInput.disabled = true;
    sendButton.disabled = true;
    
    addMessage(message, 'user');
    messageInput.value = '';
    
    try {
        const loadingId = addLoadingMessage();
        
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
        
        removeMessage(loadingId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        addMessage(data.response, 'assistant');
        
    } catch (error) {
        console.error('Error:', error);
        addSystemMessage('Sorry, there was an error processing your request. Please try again.');
    } finally {
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    let html = text;
    
    // Convert markdown links FIRST - this is critical
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Convert headings
    html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
    
    // Convert lists
    html = html.replace(/^- (.*?)$/gm, '<li>$1</li>');
    
    // Convert bold and italic
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert code
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Convert newlines to br
    html = html.replace(/\n/g, '<br>');
    
    // Wrap list items in ul
    html = html.replace(/(<li>.*?<\/li><br>)+/g, match => {
        const cleaned = match.replace(/<br>/g, '');
        return `<ul>${cleaned}</ul>`;
    });
    
    messageDiv.innerHTML = html;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    messageDiv.id = generateId();
    return messageDiv.id;
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
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
}

function generateId() {
    return 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
}
