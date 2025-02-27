document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('symptom-form');
    const sliders = document.querySelectorAll('.symptom-slider');
    const analysisResult = document.getElementById('symptom-analysis-result');
    const chart = document.getElementById('symptom-chart');

    // Initialize sliders
    sliders.forEach(slider => {
        const value = slider.value;
        slider.style.background = `linear-gradient(to right, var(--primary-color) ${value * 10}%, #ddd ${value * 10}%)`;
        
        // Update slider appearance on input
        slider.addEventListener('input', (e) => {
            const value = e.target.value;
            slider.style.background = `linear-gradient(to right, var(--primary-color) ${value * 10}%, #ddd ${value * 10}%)`;
            slider.nextElementSibling.textContent = value;
        });
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const symptoms = Array.from(sliders).map(slider => ({
            name: slider.dataset.symptom,
            severity: parseInt(slider.value)
        }));

        const notes = document.getElementById('notes').value;

        try {
            const response = await fetch('/api/symptom_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symptoms, notes })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Display analysis
            analysisResult.innerHTML = `
                <div class="analysis-content">
                    <h3>Analysis Results</h3>
                    <div class="analysis-text">${data.analysis}</div>
                </div>
            `;

            // Update chart
            updateChart(symptoms);
            
            // Save to local storage for history
            saveSymptomHistory(symptoms, notes);

        } catch (error) {
            analysisResult.innerHTML = `
                <div class="error-message">
                    Sorry, there was an error analyzing your symptoms. Please try again.
                </div>
            `;
            console.error('Error:', error);
        }
    });

    // Initialize and update chart
    function updateChart(symptoms) {
        const ctx = chart.getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: symptoms.map(s => s.name),
                datasets: [{
                    label: 'Symptom Severity',
                    data: symptoms.map(s => s.severity),
                    backgroundColor: 'rgba(255, 105, 180, 0.6)',
                    borderColor: 'rgb(255, 105, 180)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10
                    }
                }
            }
        });
    }

    // Save symptom history to local storage
    function saveSymptomHistory(symptoms, notes) {
        const history = JSON.parse(localStorage.getItem('symptomHistory') || '[]');
        history.push({
            date: new Date().toISOString(),
            symptoms,
            notes
        });
        localStorage.setItem('symptomHistory', JSON.stringify(history));
    }
});
