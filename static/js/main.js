document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-message');
    const analyzeButton = document.getElementById('analyze-symptoms');
    const symptomAnalysisResult = document.getElementById('symptom-analysis-result');

    // Chat functionality
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        appendMessage('You', message);
        userInput.value = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            // Add AI response to chat
            appendMessage('MenoCare AI', data.response);
        } catch (error) {
            appendMessage('System', 'Sorry, there was an error processing your message.');
            console.error('Error:', error);
        }
    }

    function appendMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender.toLowerCase()}`;
        messageDiv.innerHTML = `
            <strong>${sender}:</strong>
            <p>${text}</p>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Symptom tracking functionality
    async function analyzeSymptoms() {
        const symptoms = Array.from(document.querySelectorAll('.symptom-slider')).map(slider => ({
            name: slider.dataset.symptom,
            severity: slider.value
        }));

        try {
            const response = await fetch('/api/symptom_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symptoms })
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            symptomAnalysisResult.innerHTML = `
                <h3>Analysis Results:</h3>
                <p>${data.analysis}</p>
            `;
        } catch (error) {
            symptomAnalysisResult.innerHTML = 'Sorry, there was an error analyzing your symptoms.';
            console.error('Error:', error);
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    analyzeButton.addEventListener('click', analyzeSymptoms);

    // Initialize symptom sliders
    document.querySelectorAll('.symptom-slider').forEach(slider => {
        const value = slider.value;
        slider.style.background = `linear-gradient(to right, var(--primary-color) ${value * 10}%, #ddd ${value * 10}%)`;
        
        slider.addEventListener('input', (e) => {
            const value = e.target.value;
            slider.style.background = `linear-gradient(to right, var(--primary-color) ${value * 10}%, #ddd ${value * 10}%)`;
        });
    });
});
