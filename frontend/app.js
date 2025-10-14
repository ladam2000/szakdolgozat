import { userManager, signOutRedirect, getUser, isAuthenticated } from './auth.js';

const API_URL = 'https://fbiwuqkkwu6yqutfmr25anrnuy0hwfnl.lambda-url.eu-central-1.on.aws/';

let currentUser = null;
let sessionId = localStorage.getItem('sessionId');
if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem('sessionId', sessionId);
}

// Language translations
const translations = {
    en: {
        title: 'Virtual Travel Assistant',
        subtitle: 'Plan your perfect trip with AI-powered assistance',
        loginSubtitle: 'Sign in to start planning your trip',
        signIn: 'Sign In',
        signUp: 'Sign Up',
        signUpLink: 'Sign Up',
        signOut: 'Sign Out',
        send: 'Send',
        inputPlaceholder: 'Ask about flights, hotels, or activities...',
        welcomeMessage: 'Welcome! I can help you plan flights, hotels, and activities. What would you like to do?',
        errorMessage: 'Sorry, there was an error processing your request. Please try again.',
        signInRequired: 'Please sign in to continue',
        noAccount: "Don't have an account?",
        haveAccount: 'Already have an account?'
    },
    hu: {
        title: 'Virtuális Utazási Asszisztens',
        subtitle: 'Tervezd meg a tökéletes utazásod AI-alapú segítséggel',
        loginSubtitle: 'Jelentkezz be az utazástervezés megkezdéséhez',
        signIn: 'Bejelentkezés',
        signUp: 'Regisztráció',
        signUpLink: 'Regisztráció',
        signOut: 'Kijelentkezés',
        send: 'Küldés',
        inputPlaceholder: 'Kérdezz repülőjáratokról, szállásokról vagy programokról...',
        welcomeMessage: 'Üdvözöllek! Segíthetek repülőjáratok, szállások és programok tervezésében. Miben segíthetek?',
        errorMessage: 'Sajnálom, hiba történt a kérés feldolgozása során. Kérlek, próbáld újra.',
        signInRequired: 'Kérlek, jelentkezz be a folytatáshoz',
        noAccount: 'Nincs még fiókod?',
        haveAccount: 'Már van fiókod?'
    }
};

let currentLanguage = localStorage.getItem('language') || 'en';

// Initialize language on page load
console.log('Initial language:', currentLanguage);

const loginScreen = document.getElementById('loginScreen');
const appScreen = document.getElementById('appScreen');
const signInButton = document.getElementById('signInButton');
const signOutButton = document.getElementById('signOutButton');
const userEmail = document.getElementById('userEmail');
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

// Initialize language
function updateLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('language', lang);
    
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[lang][key]) {
            element.textContent = translations[lang][key];
        }
    });
    
    // Update placeholder
    const placeholderKey = messageInput.getAttribute('data-i18n-placeholder');
    if (placeholderKey && translations[lang][placeholderKey]) {
        messageInput.placeholder = translations[lang][placeholderKey];
    }
    
    // Update active state for language buttons
    document.querySelectorAll('.lang-btn, .lang-btn-login').forEach(btn => {
        if (btn.getAttribute('data-lang') === lang) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Language button event listeners
document.addEventListener('click', (e) => {
    const langBtn = e.target.closest('.lang-btn, .lang-btn-login');
    if (langBtn) {
        const lang = langBtn.getAttribute('data-lang');
        updateLanguage(lang);
    }
});

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
    updateLanguage(currentLanguage);
}

async function showApp() {
    loginScreen.style.display = 'none';
    appScreen.style.display = 'block';
    
    if (currentUser) {
        userEmail.textContent = currentUser.profile?.email || 'User';
    }
    
    // Update language BEFORE loading history
    updateLanguage(currentLanguage);
    
    // Load conversation history (language is now set)
    await loadConversationHistory();
}

const signUpLink = document.getElementById('signUpLink');

signInButton.addEventListener('click', async () => {
    await userManager.signinRedirect();
});

signUpLink.addEventListener('click', (e) => {
    e.preventDefault();
    // Redirect to Cognito sign-up page
    const cognitoDomain = 'https://eu-central-1ukrxqbex5.auth.eu-central-1.amazoncognito.com';
    const clientId = '6kmkgdkls92qfthrbglelcsdjm';
    const redirectUri = encodeURIComponent(window.location.origin + '/');
    const signUpUrl = `${cognitoDomain}/signup?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=email+openid+phone`;
    
    console.log('Redirecting to sign-up URL:', signUpUrl);
    window.location.href = signUpUrl;
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
        addSystemMessage(translations[currentLanguage].signInRequired);
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
        addSystemMessage(translations[currentLanguage].errorMessage);
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
    
    // Convert pattern: "Text - URL" to clickable link
    // Example: "Rentalcars.com - https://www.rentalcars.com" -> "<a>Rentalcars.com</a>"
    html = html.replace(/([^\n\-]+?)\s*-\s*(https?:\/\/[^\s<]+)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Convert standalone URLs to clickable links
    html = html.replace(/(?<!href="|">)(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Convert markdown links [text](url)
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
    // Generate a session ID that's at least 33 characters (AWS requirement)
    // Format: session_<timestamp>_<random>
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    return `session_${timestamp}_${random}`;
}

function generateId() {
    return 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
}

async function loadConversationHistory() {
    try {
        console.log('Loading conversation history for session:', sessionId);
        console.log('Current language when loading history:', currentLanguage);
        console.log('Welcome message will be:', translations[currentLanguage].welcomeMessage);
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.access_token}`,
            },
            body: JSON.stringify({
                action: 'getHistory',
                sessionId: sessionId,
                k: 3  // Get last 3 turns (6 messages)
            })
        });

        if (!response.ok) {
            console.log('No history available or error loading history');
            addSystemMessage(translations[currentLanguage].welcomeMessage);
            return;
        }

        const data = await response.json();
        const messages = data.messages || [];
        
        if (messages.length > 0) {
            console.log(`Loading ${messages.length} previous messages`);
            
            // Add the historical messages
            messages.forEach(msg => {
                addMessage(msg.content, msg.role);
            });
            
            console.log('Conversation history loaded successfully');
        } else {
            console.log('No previous conversation history found');
            addSystemMessage(translations[currentLanguage].welcomeMessage);
        }

    } catch (error) {
        console.log('Could not load conversation history:', error);
        // Show welcome message on error
        addSystemMessage(translations[currentLanguage].welcomeMessage);
    }
}
