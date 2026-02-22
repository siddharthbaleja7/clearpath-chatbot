const chatWindow = document.getElementById("chat-window");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const debugContent = document.getElementById("debug-content");

let conversationId = null;

// Add a message to the chat UI
function appendMessage(sender, text, isWarning = false) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    
    let contentHtml = `<div class="bubble">${text.replace(/\n/g, "<br>")}</div>`;
    
    // If warning flagged
    if (isWarning && sender === "bot") {
        contentHtml += `<div class="warning-flag">⚠️ Low confidence — please verify with support.</div>`;
    }
    
    messageDiv.innerHTML = contentHtml;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Update the debug panel
function updateDebugPanel(metadata) {
    const flagsList = metadata.evaluator_flags.length > 0
        ? metadata.evaluator_flags.join(", ")
        : "None";

    debugContent.innerHTML = `
        <div class="debug-item">
            <div class="debug-label">Model Used</div>
            <div class="debug-value">${metadata.model_used}</div>
        </div>
        <div class="debug-item">
            <div class="debug-label">Classification</div>
            <div class="debug-value">${metadata.classification}</div>
        </div>
        <div class="debug-item">
            <div class="debug-label">Latency</div>
            <div class="debug-value">${metadata.latency_ms} ms</div>
        </div>
        <div class="debug-item">
            <div class="debug-label">Tokens (In / Out)</div>
            <div class="debug-value">${metadata.tokens.input} / ${metadata.tokens.output}</div>
        </div>
        <div class="debug-item">
            <div class="debug-label">Chunks Retrieved</div>
            <div class="debug-value">${metadata.chunks_retrieved}</div>
        </div>
        <div class="debug-item" style="border-left: 3px solid ${metadata.evaluator_flags.length > 0 ? '#ff7675' : '#00b894'};">
            <div class="debug-label">Evaluator Flags</div>
            <div class="debug-value" style="color: ${metadata.evaluator_flags.length > 0 ? '#ff7675' : '#00b894'};">${flagsList}</div>
        </div>
    `;
}

async function handleSend() {
    const question = userInput.value.trim();
    if (!question) return;

    // Display user message
    appendMessage("user", question);
    userInput.value = "";
    sendBtn.disabled = true;

    // Show loading state
    const loadingId = "msg-" + Date.now();
    const loadingDiv = document.createElement("div");
    loadingDiv.classList.add("message", "bot");
    loadingDiv.id = loadingId;
    loadingDiv.innerHTML = `<div class="bubble">Thinking...</div>`;
    chatWindow.appendChild(loadingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch("http://localhost:8000/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                conversation_id: conversationId
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        
        // Remove loading state
        const loadingBox = document.getElementById(loadingId);
        if (loadingBox) loadingBox.remove();

        // Save conversation ID
        if (data.conversation_id) {
            conversationId = data.conversation_id;
        }

        // Determine if warning is needed based on flags
        const hasWarning = data.metadata.evaluator_flags.length > 0;

        // Display bot answer
        appendMessage("bot", data.answer, hasWarning);

        // Display debug metadata
        updateDebugPanel(data.metadata);

    } catch (error) {
        console.error(error);
        const loadingBox = document.getElementById(loadingId);
        if (loadingBox) loadingBox.remove();
        appendMessage("bot", "Sorry, an error occurred while connecting to the server.");
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
}

sendBtn.addEventListener("click", handleSend);
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        handleSend();
    }
});
