document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const quickTopicButtons = document.querySelectorAll('.quick-topic-btn');
    const voiceButton = document.getElementById('voice-input');
    let isProcessing = false;

    // Function to send message to server
    async function sendMessage(message) {
        if (!message || isProcessing) return;
        
        isProcessing = true;
        appendMessage('user', message);
        appendTypingIndicator();
        
        try {
            const response = await fetch('/analyze_concerns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    concerns: message
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator();
            
            if (data.success) {
                // Add AI response
                appendMessage('assistant', data.analysis);
                
                // Add follow-up questions if available
                if (data.follow_up_questions && data.follow_up_questions.length > 0) {
                    appendFollowUpQuestions(data.follow_up_questions);
                }
            } else {
                throw new Error(data.error || 'Failed to get response');
            }
        } catch (error) {
            console.error('Error:', error);
            appendMessage('system', 'Sorry, I encountered an error. Please try again.');
        } finally {
            isProcessing = false;
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Function to append message to chat
    function appendMessage(type, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start ' + (type === 'user' ? 'justify-end' : '');

        const contentDiv = document.createElement('div');
        contentDiv.className = `${type === 'user' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-800'} rounded-lg p-4 max-w-[80%] ${type === 'user' ? 'ml-4' : 'mr-4'}`;
        
        if (type !== 'user') {
            const avatarDiv = document.createElement('div');
            avatarDiv.className = 'flex-shrink-0';
            avatarDiv.innerHTML = `
                <div class="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
                    </svg>
                </div>
            `;
            messageDiv.appendChild(avatarDiv);
        }

        contentDiv.textContent = text;
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to append typing indicator
    function appendTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'flex items-start';
        indicator.innerHTML = `
            <div class="flex-shrink-0">
                <div class="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
                    </svg>
                </div>
            </div>
            <div class="ml-4 bg-gray-100 rounded-lg p-4 max-w-[80%]">
                <div class="flex space-x-2">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to remove typing indicator
    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Function to append follow-up questions
    function appendFollowUpQuestions(questions) {
        const questionsDiv = document.createElement('div');
        questionsDiv.className = 'flex items-start';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'ml-14 space-y-2';
        
        questions.forEach(question => {
            const button = document.createElement('button');
            button.className = 'block text-left text-primary hover:text-primary-dark';
            button.textContent = question;
            button.onclick = () => {
                chatInput.value = question;
                sendMessage(question);
            };
            contentDiv.appendChild(button);
        });
        
        questionsDiv.appendChild(contentDiv);
        chatMessages.appendChild(questionsDiv);
    }

    // Handle form submission
    chatForm.onsubmit = (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message);
            chatInput.value = '';
        }
    };

    // Handle quick topic buttons
    quickTopicButtons.forEach(button => {
        button.onclick = () => {
            const topic = button.textContent.trim();
            chatInput.value = topic;
            sendMessage(topic);
        };
    });

    // Show initial welcome message
    appendMessage('assistant', 'Welcome to MenoCare! I can help you with menstrual health, pregnancy, and menopause concerns.');
});
