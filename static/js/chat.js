document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const chatForm = document.getElementById('chat-form');
    const sendBtn = document.getElementById('send-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const sessionList = document.getElementById('session-list');
    const themeToggle = document.getElementById('theme-toggle');
    const voiceBtn = document.getElementById('voice-btn');
    const deleteChatBtn = document.getElementById('delete-chat-btn');
    const exportPdfBtn = document.getElementById('export-pdf-btn');
    const pdfUpload = document.getElementById('pdf-upload');
    const welcomeMessage = document.getElementById('welcome-message');

    // Sidebar Elements for Mobile
    const sidebar = document.getElementById('sidebar');
    const openSidebarBtn = document.getElementById('open-sidebar-btn');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');

    let currentSessionId = localStorage.getItem('sessionId');
    let isStreaming = false;

    // Initialize
    initTheme();
    if (currentSessionId) {
        loadChatHistory(currentSessionId);
    } else {
        createNewSession();
    }

    // --- EVENT LISTENERS ---

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (isStreaming || !messageInput.value.trim()) return;

        const message = messageInput.value.trim();
        messageInput.value = '';
        messageInput.style.height = 'auto';

        if (welcomeMessage) welcomeMessage.style.display = 'none';

        // Add User Message to UI
        appendMessage(message, 'user');

        // Start Streaming Response
        await streamResponse(message);
    });

    messageInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        sendBtn.disabled = this.value.trim() === '';
    });

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    newChatBtn.addEventListener('click', createNewSession);

    deleteChatBtn.addEventListener('click', async () => {
        if (!currentSessionId) return;
        if (!confirm('Are you sure you want to delete this conversation?')) return;

        try {
            const res = await fetch(`/api/delete_chat/${currentSessionId}`, { method: 'DELETE' });
            if (res.ok) {
                chatContainer.innerHTML = '';
                localStorage.removeItem('sessionId');
                currentSessionId = null;
                if (welcomeMessage) welcomeMessage.style.display = 'block';
                chatContainer.appendChild(welcomeMessage);
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
        }
    });

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // Mobile Sidebar Toggle
    openSidebarBtn.addEventListener('click', () => sidebar.classList.add('open'));
    closeSidebarBtn.addEventListener('click', () => sidebar.classList.remove('open'));

    // Export PDF
    exportPdfBtn.addEventListener('click', () => {
        const element = document.getElementById('chat-container');
        const opt = {
            margin: 1,
            filename: `Medical_Chat_${currentSessionId}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
        };
        html2pdf().set(opt).from(element).save();
    });

    // PDF Upload
    pdfUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            alert('Uploading and processing PDF... This may take a moment.');
            const res = await fetch('/api/upload_pdf', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                alert('PDF processed successfully! You can now ask questions about it.');
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Failed to upload PDF.');
        } finally {
            e.target.value = ''; // Reset input
        }
    });


    // --- SPEECH RECOGNITION ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';

        recognition.onstart = function () {
            voiceBtn.classList.add('recording');
        };

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            messageInput.value += transcript;
            messageInput.dispatchEvent(new Event('input'));
        };

        recognition.onerror = function (event) {
            console.error('Speech recognition error', event.error);
            voiceBtn.classList.remove('recording');
        };

        recognition.onend = function () {
            voiceBtn.classList.remove('recording');
        };

        voiceBtn.addEventListener('click', () => {
            if (voiceBtn.classList.contains('recording')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    } else {
        voiceBtn.style.display = 'none'; // Hide if not supported
    }

    // --- CORE FUNCTIONS ---
    function initTheme() {
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-theme');
        }
    }

    async function createNewSession() {
        try {
            const res = await fetch('/api/new_chat', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                currentSessionId = data.session_id;
                localStorage.setItem('sessionId', currentSessionId);
                chatContainer.innerHTML = '';
                if (welcomeMessage) welcomeMessage.style.display = 'block';
                chatContainer.appendChild(welcomeMessage);
            }
        } catch (error) {
            console.error("Error creating new session:", error);
        }
    }

    async function loadChatHistory(sessionId) {
        try {
            const res = await fetch(`/api/chat_history/${sessionId}`);
            const data = await res.json();

            if (data.success && data.data.length > 0) {
                if (welcomeMessage) welcomeMessage.style.display = 'none';
                chatContainer.innerHTML = ''; // Clear container

                data.data.forEach(msg => {
                    appendMessage(msg.content, msg.role, msg.sources);
                });
                scrollToBottom();
            }
        } catch (error) {
            console.error("Error loading history:", error);
        }
    }

    function appendMessage(content, role, sources = []) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Parse markdown immediately for history
        contentDiv.innerHTML = marked.parse(content);

        // Add sources if assistant and sources exist
        if (role === 'assistant' && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-container';
            sourcesDiv.innerHTML = '<strong>Sources:</strong><br>';
            sources.forEach(src => {
                const badge = document.createElement('span');
                badge.className = 'source-badge';
                // Extract filename from path if needed
                const srcName = src.source ? src.source.split('/').pop() : 'Document';
                badge.innerText = `${srcName} (Pg ${src.page || 'N/A'})`;
                sourcesDiv.appendChild(badge);
            });
            contentDiv.appendChild(sourcesDiv);
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(contentDiv);
        chatContainer.appendChild(msgDiv);
        scrollToBottom();

        return contentDiv; // Return content div for streaming updates
    }

    async function streamResponse(query) {
        isStreaming = true;
        sendBtn.disabled = true;
        messageInput.disabled = true;

        if (!currentSessionId) await createNewSession();

        // Create Assistant Bubble
        const msgDiv = document.createElement('div');
        msgDiv.className = `message assistant`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Add Typing Indicator initially
        contentDiv.innerHTML = `
            <div class="typing-indicator" id="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            <div class="stream-content"></div>
        `;

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(contentDiv);
        chatContainer.appendChild(msgDiv);
        scrollToBottom();

        const streamContentDiv = contentDiv.querySelector('.stream-content');
        let fullResponseBuffer = "";

        try {
            const response = await fetch('/api/stream_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: currentSessionId, message: query })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);

                        if (dataStr === '[DONE]') {
                            isStreaming = false;
                            break;
                        }

                        try {
                            const data = JSON.parse(dataStr);

                            // Remove typing indicator on first chunk
                            const typingIndicator = document.getElementById('typing-indicator');
                            if (typingIndicator) typingIndicator.remove();

                            if (data.type === 'chunk') {
                                fullResponseBuffer += data.content;
                                // Update markdown live
                                streamContentDiv.innerHTML = marked.parse(fullResponseBuffer);
                                scrollToBottom();
                            }
                            else if (data.type === 'sources' && data.sources.length > 0) {
                                const sourcesDiv = document.createElement('div');
                                sourcesDiv.className = 'sources-container';
                                sourcesDiv.innerHTML = '<strong>Sources:</strong><br>';
                                data.sources.forEach(src => {
                                    const badge = document.createElement('span');
                                    badge.className = 'source-badge';
                                    const srcName = src.source ? src.source.split('/').pop() : 'Document';
                                    badge.innerText = `${srcName} (Pg ${src.page || 'N/A'})`;
                                    sourcesDiv.appendChild(badge);
                                });
                                contentDiv.appendChild(sourcesDiv);
                                scrollToBottom();
                            }
                            else if (data.type === 'error') {
                                streamContentDiv.innerHTML += `<br><span style="color: red;">${data.content}</span>`;
                            }
                        } catch (e) {
                            console.error('Error parsing SSE json:', e, dataStr);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Fetch error:', error);
            streamContentDiv.innerHTML = `<span style="color: red;">Failed to connect to server.</span>`;
        } finally {
            isStreaming = false;
            sendBtn.disabled = false;
            messageInput.disabled = false;
            messageInput.focus();
        }
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
