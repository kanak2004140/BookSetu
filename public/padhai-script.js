/* PadhAI chat page. */

document.addEventListener('DOMContentLoaded', () => {
    if (!isLoggedIn()) return redirectToLogin();

    const input = document.getElementById('userInput');
    const messages = document.getElementById('messagesArea');

    function addMessage(text, sender) {
        const message = document.createElement('div');
        message.className = `message ${sender}-message`;
        message.innerHTML = '<div class="message-bubble"></div><span class="message-time"></span>';
        message.querySelector('.message-bubble').textContent = text;
        message.querySelector('.message-time').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
        return message;
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;
        addMessage(text, 'user');
        input.value = '';
        const pending = addMessage('Thinking...', 'bot');
        try {
            const reply = await api.chat(text);
            pending.querySelector('.message-bubble').textContent = reply.success ? reply.response : (reply.error || reply.response);
        } catch (error) {
            pending.querySelector('.message-bubble').textContent = error.message;
        }
    }

    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    input.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    document.querySelectorAll('.suggestion-btn').forEach(button => button.addEventListener('click', () => {
        input.value = button.dataset.question;
        sendMessage();
    }));
});
