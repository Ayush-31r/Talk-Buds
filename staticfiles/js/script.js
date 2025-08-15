// script.js

// -----------------------
// Variables from Django template
// -----------------------
const roomId = document.getElementById('chatBox').dataset.roomId;
const CURRENT_USER_ID = document.getElementById('chatBox').dataset.userId;
const CURRENT_USERNAME = document.getElementById('chatBox').dataset.username;

// -----------------------
// WebSocket connection
// -----------------------
const chatSocket = new WebSocket(
    `ws://${window.location.host}/ws/chat/${roomId}/`
);

const chatLog = document.getElementById("chat-log");

// -----------------------
// Receive messages
// -----------------------
chatSocket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if(data.username && data.message) {
        const messageElement = document.createElement("p");
        messageElement.innerHTML = `<strong>${data.username}:</strong> ${data.message}`;
        chatLog.appendChild(messageElement);

        // Auto scroll to bottom
        chatLog.scrollTop = chatLog.scrollHeight;
    }
};

chatSocket.onclose = function(event) {
    console.error("WebSocket closed unexpectedly");
};

// -----------------------
// Send messages
// -----------------------
function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const message = messageInput.value.trim();

    if(message.length === 0) return;

    const messageData = {
        user_id: CURRENT_USER_ID,
        username: CURRENT_USERNAME,
        message: message
    };

    chatSocket.send(JSON.stringify(messageData));
    messageInput.value = "";
}

// -----------------------
// Enter key handler
// -----------------------
const messageInputField = document.getElementById("message-input");
messageInputField.addEventListener("keypress", function(event) {
    if(event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});
