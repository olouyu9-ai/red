// Minimal JS placeholder for chat UX enhancements (AJAX could be added here)
document.addEventListener('DOMContentLoaded', function() {
    console.log('chat.js loaded');

    // Connect to websocket for group pages if present
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;

    const pathParts = window.location.pathname.split('/');
    // Expect URL like /chat/groups/<uuid>/
    const groupId = pathParts.includes('groups') ? pathParts[pathParts.indexOf('groups') + 1] : null;
    if (!groupId) return;

    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socketUrl = `${wsScheme}://${window.location.host}/ws/chat/${groupId}/`;
    const socket = new WebSocket(socketUrl);

    socket.onopen = () => console.log('WebSocket connected');
    socket.onclose = () => console.log('WebSocket closed');
    socket.onerror = (e) => console.error('WebSocket error', e);

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const node = document.createElement('div');
        node.className = 'message';
        node.innerHTML = `<strong>${data.sender}</strong> <span class="time">${data.created_at}</span><div class="content">${data.message}</div>`;
        messagesContainer.appendChild(node);
    };

    // Hook send form to websocket — select the message field explicitly
    const form = document.querySelector('form[action$="/send/"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const messageField = form.querySelector('textarea[name="content"], input[name="content"]');
            if (!messageField) {
                console.warn('No message field found in form');
                return;
            }
            const text = (messageField.value || '').trim();
            if (!text) return;
            const payload = { message: text };
            try {
                socket.send(JSON.stringify(payload));
            } catch (err) {
                console.error('WebSocket send error', err);
                // fallback to normal POST
                form.submit();
                return;
            }
            messageField.value = '';
        });
    }
});
