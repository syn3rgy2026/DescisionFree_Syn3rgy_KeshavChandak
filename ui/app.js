document.addEventListener('DOMContentLoaded', () => {
    const taskInput = document.getElementById('task-input');
    const sendBtn = document.getElementById('send-btn');
    const attachBtn = document.getElementById('attach-btn');
    const fileUpload = document.getElementById('file-upload');
    const filesList = document.getElementById('attached-files-list');
    const chatMessages = document.getElementById('chat-messages');

    const progressContainer = document.getElementById('progress-container');
    const progressLog = document.getElementById('progress-log');
    
    let isProcessing = false;
    let selectedFiles = [];
    let pollingInterval = null;

    // Auto-resize textarea
    taskInput.addEventListener('input', function() {
        this.style.height = '20px';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Enter to send, Shift+Enter for newline
    taskInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    // File attachments
    attachBtn.addEventListener('click', () => {
        fileUpload.click();
    });

    fileUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            Array.from(e.target.files).forEach(file => {
                selectedFiles.push(file);
                renderFileChip(file);
            });
        }
        fileUpload.value = ''; // reset
    });

    function renderFileChip(file) {
        const chip = document.createElement('div');
        chip.className = 'file-chip';
        chip.innerHTML = `
            <i class="fa-solid fa-file"></i> 
            <span>${file.name}</span>
            <i class="fa-solid fa-times" data-name="${file.name}"></i>
        `;
        
        chip.querySelector('.fa-times').addEventListener('click', function() {
            const name = this.getAttribute('data-name');
            selectedFiles = selectedFiles.filter(f => f.name !== name);
            chip.remove();
        });

        filesList.appendChild(chip);
    }

    function addMessage(text, role) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        // Use markdown parser if assistant
        let contentHtml = text;
        if (role === 'assistant') {
            try {
                contentHtml = marked.parse(text);
            } catch(e) {
                // fallback if marked is not loaded
                contentHtml = text.replace(/\\n/g, '<br>');
            }
        } else {
            // User messages just escape somewhat to avoid XSS
            contentHtml = text.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\\n/g, "<br>");
        }

        const sender = role === 'user' ? 'You' : 'Synergy';

        msgDiv.innerHTML = `
            <div class="message-sender">${sender}</div>
            <div class="bubble">${contentHtml}</div>
        `;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function startPollingStatus() {
        progressContainer.style.display = 'block';
        progressLog.innerHTML = '';
        
        pollingInterval = setInterval(async () => {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                if (data.logs && data.logs.length > 0) {
                    // Update log viewer
                    progressLog.innerHTML = data.logs.map(log => `<div>> ${log}</div>`).join('');
                    progressLog.scrollTop = progressLog.scrollHeight;
                }
            } catch(e) {
                console.error("Polling error", e);
            }
        }, 1000);
    }

    function stopPollingStatus() {
        clearInterval(pollingInterval);
        pollingInterval = null;
        progressContainer.style.display = 'none';
    }

    async function sendMessage() {
        if (isProcessing) return;
        
        const taskText = taskInput.value.trim();
        if (!taskText && selectedFiles.length === 0) return;

        isProcessing = true;
        sendBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';

        let displayMsg = taskText;
        if (selectedFiles.length > 0) {
            displayMsg += `\n[Attached ${selectedFiles.length} file(s)]`;
        }

        if(displayMsg) {
            addMessage(displayMsg, 'user');
        }

        // Clear input
        taskInput.value = '';
        taskInput.style.height = '20px';
        filesList.innerHTML = '';

        const formData = new FormData();
        formData.append('task', taskText);
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        // Start reading thinking steps
        startPollingStatus();

        try {
            const response = await fetch('/run-task', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if(data.response) {
                addMessage(data.response, 'assistant');
            } else {
                addMessage("Task finished, but no output text was returned.", 'assistant');
            }

        } catch (error) {
            addMessage(`**Error:** ${error.message}`, 'assistant');
        } finally {
            isProcessing = false;
            sendBtn.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
            selectedFiles = [];
            stopPollingStatus();
        }
    }
});
