const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("msg-input");
const sendBtn = document.getElementById("send-btn");

function appendMessage(role, text) {
  const row = document.createElement("div");
  row.className = "msg-row " + (role === "user" ? "user" : "bot");

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble " + (role === "user" ? "msg-user" : "msg-bot");
  bubble.textContent = text;

  row.appendChild(bubble);
  messagesEl.appendChild(row);

  // Auto-scroll to bottom
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage(text) {
  // Show the user's message
  appendMessage("user", text);
  sendBtn.disabled = true;

  try {
    // Send POST request to /api/chat
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();

    if (!res.ok) {
      appendMessage("bot", "Error: " + (data.error || "Unknown error"));
    } else {
      appendMessage("bot", data.answer);
    }
  } catch (err) {
    console.error(err);
    appendMessage("bot", "Network error. Please try again.");
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

// Handle form submit (when user presses Enter or clicks Send)
formEl.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = "";
  sendMessage(text);
});

// Focus input when page loads
window.addEventListener("load", () => inputEl.focus());
