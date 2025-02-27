// Article Management
let articles = JSON.parse(sessionStorage.getItem('articles')) || [];

function createArticle(title, content, category) {
    const newArticle = {
        id: Date.now(),
        title,
        content,
        category,
        created_at: new Date().toLocaleDateString()
    };
    articles.push(newArticle);
    sessionStorage.setItem('articles', JSON.stringify(articles));
    displayArticles();
}

function editArticle(id, title, content, category) {
    articles = articles.map(article => 
        article.id === id 
            ? { ...article, title, content, category }
            : article
    );
    sessionStorage.setItem('articles', JSON.stringify(articles));
    displayArticles();
}

function deleteArticle(id) {
    if (confirm('Are you sure you want to delete this article?')) {
        articles = articles.filter(article => article.id !== id);
        sessionStorage.setItem('articles', JSON.stringify(articles));
        displayArticles();
    }
}

function displayArticles() {
    const container = document.getElementById('articles-container');
    if (!container) return;

    if (articles.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-600">No articles yet. Create one to get started!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = articles.map(article => `
        <div class="bg-white rounded-xl shadow-lg p-6">
            <h3 class="text-xl font-semibold mb-4">${article.title}</h3>
            <p class="text-gray-600 mb-4">${article.content}</p>
            <div class="flex justify-between items-center text-sm text-gray-500">
                <span>Category: ${article.category}</span>
                <span>${article.created_at}</span>
            </div>
            <div class="flex justify-end space-x-2 mt-4">
                <button onclick="openEditModal(${article.id}, '${article.title}', '${article.content}', '${article.category}')"
                        class="text-blue-500 hover:text-blue-600">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                </button>
                <button onclick="deleteArticle(${article.id})"
                        class="text-red-500 hover:text-red-600">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </div>
        </div>
    `).join('');
}

// Modal Management
function openCreateModal() {
    document.getElementById('articleModal').classList.remove('hidden');
    document.getElementById('modalTitle').textContent = 'Create New Article';
    document.getElementById('articleForm').reset();
    document.getElementById('articleId').value = '';
}

function openEditModal(id, title, content, category) {
    document.getElementById('articleModal').classList.remove('hidden');
    document.getElementById('modalTitle').textContent = 'Edit Article';
    document.getElementById('articleTitle').value = title;
    document.getElementById('articleContent').value = content;
    document.getElementById('articleCategory').value = category;
    document.getElementById('articleId').value = id;
}

function closeModal() {
    document.getElementById('articleModal').classList.add('hidden');
}

// Form Handling
document.getElementById('articleForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const id = document.getElementById('articleId').value;
    const title = document.getElementById('articleTitle').value;
    const content = document.getElementById('articleContent').value;
    const category = document.getElementById('articleCategory').value;

    if (id) {
        editArticle(parseInt(id), title, content, category);
    } else {
        createArticle(title, content, category);
    }

    closeModal();
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    displayArticles();
});

document.addEventListener('DOMContentLoaded', () => {
    const readButtons = document.querySelectorAll('.btn-read');
    const modal = document.getElementById('article-modal');
    const modalContent = document.getElementById('article-content');
    const closeBtn = document.querySelector('.close');

    // Article content
    const articles = {
        'menopause-basics': {
            title: 'Understanding Menopause',
            content: `
                <h2>What is Menopause?</h2>
                <p>Menopause is a natural biological process marking the end of menstrual cycles. It's diagnosed after 12 months without a menstrual period. While it can happen in your 40s or 50s, the average age is 51 in the United States.</p>
                
                <h3>Common Signs and Symptoms</h3>
                <ul>
                    <li>Hot flashes and night sweats</li>
                    <li>Irregular periods</li>
                    <li>Mood changes</li>
                    <li>Sleep problems</li>
                    <li>Weight gain and slowed metabolism</li>
                    <li>Thinning hair and dry skin</li>
                </ul>

                <h3>What Causes Menopause?</h3>
                <p>Menopause occurs when the ovaries naturally decrease their production of the hormones estrogen and progesterone. This process can also be triggered by:</p>
                <ul>
                    <li>Surgery (such as removal of ovaries)</li>
                    <li>Chemotherapy and radiation therapy</li>
                    <li>Primary ovarian insufficiency</li>
                </ul>
            `
        },
        'menopause-stages': {
            title: 'Stages of Menopause',
            content: `
                <h2>The Three Stages of Menopause</h2>
                
                <h3>1. Perimenopause</h3>
                <p>The transition period before menopause, typically lasting 7-14 years. During this time:</p>
                <ul>
                    <li>Periods become irregular</li>
                    <li>Hormonal fluctuations begin</li>
                    <li>First experience of symptoms</li>
                </ul>

                <h3>2. Menopause</h3>
                <p>Officially diagnosed after 12 consecutive months without a period. Key characteristics:</p>
                <ul>
                    <li>Complete cessation of menstruation</li>
                    <li>End of fertility</li>
                    <li>Significant hormonal changes</li>
                </ul>

                <h3>3. Postmenopause</h3>
                <p>The years following menopause, bringing:</p>
                <ul>
                    <li>Symptom relief for some women</li>
                    <li>New health considerations</li>
                    <li>Need for continued health monitoring</li>
                </ul>
            `
        },
        'hot-flashes': {
            title: 'Managing Hot Flashes',
            content: `
                <h2>Effective Strategies for Managing Hot Flashes</h2>

                <h3>Immediate Relief Techniques</h3>
                <ul>
                    <li>Dress in layers</li>
                    <li>Keep a fan nearby</li>
                    <li>Maintain cool room temperature</li>
                    <li>Keep ice water handy</li>
                </ul>

                <h3>Lifestyle Changes</h3>
                <ul>
                    <li>Identify and avoid triggers</li>
                    <li>Practice stress reduction</li>
                    <li>Exercise regularly</li>
                    <li>Maintain healthy weight</li>
                </ul>

                <h3>When to Seek Help</h3>
                <p>Consult your healthcare provider if hot flashes:</p>
                <ul>
                    <li>Significantly disrupt sleep</li>
                    <li>Interfere with daily life</li>
                    <li>Cause extreme discomfort</li>
                </ul>
            `
        },
        'sleep-tips': {
            title: 'Sleep Solutions',
            content: `
                <h2>Better Sleep During Menopause</h2>

                <h3>Create an Optimal Sleep Environment</h3>
                <ul>
                    <li>Keep bedroom cool (65-68°F)</li>
                    <li>Use breathable bedding</li>
                    <li>Block out light and noise</li>
                    <li>Consider a cooling mattress pad</li>
                </ul>

                <h3>Develop a Sleep Routine</h3>
                <ul>
                    <li>Consistent bedtime and wake time</li>
                    <li>Relaxing bedtime ritual</li>
                    <li>Limit screen time before bed</li>
                    <li>Avoid caffeine after 2 PM</li>
                </ul>

                <h3>Natural Sleep Aids</h3>
                <ul>
                    <li>Calming teas (chamomile, valerian)</li>
                    <li>Meditation or deep breathing</li>
                    <li>Gentle yoga or stretching</li>
                    <li>White noise or nature sounds</li>
                </ul>
            `
        }
    };

    // Add click handlers for read buttons
    readButtons.forEach(button => {
        button.addEventListener('click', () => {
            const articleId = button.dataset.article;
            const article = articles[articleId];
            
            if (article) {
                modalContent.innerHTML = `
                    <h2>${article.title}</h2>
                    ${article.content}
                `;
                modal.style.display = 'block';
            }
        });
    });

    // Close modal
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Resource content data
const resourceContent = {
    'understanding-menopause': {
        title: 'Understanding Menopause',
        content: `
            <h4 class="text-lg font-semibold mb-4">What You Need to Know</h4>
            <p class="mb-4">Menopause is a natural biological process marking the end of a woman's reproductive years. Understanding this transition is crucial for managing symptoms and maintaining quality of life.</p>
            
            <h4 class="text-lg font-semibold mb-4">Key Points</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Natural life transition occurring between ages 45-55</li>
                <li>Marks the end of reproductive years</li>
                <li>Involves significant hormonal changes</li>
                <li>Affects each woman differently</li>
                <li>Can last several years</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Impact on Daily Life</h4>
            <ul class="list-disc pl-6">
                <li>Physical changes and symptoms</li>
                <li>Emotional and psychological effects</li>
                <li>Changes in energy levels</li>
                <li>Sleep pattern alterations</li>
                <li>Effects on relationships and lifestyle</li>
            </ul>`
    },
    'what-is-menopause': {
        title: 'What is Menopause?',
        content: `
            <h4 class="text-lg font-semibold mb-4">Definition</h4>
            <p class="mb-4">Menopause is officially diagnosed when a woman has gone 12 consecutive months without a menstrual period, marking the end of her reproductive years.</p>
            
            <h4 class="text-lg font-semibold mb-4">Key Facts</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Average age is 51 years</li>
                <li>Natural part of aging</li>
                <li>Caused by declining estrogen levels</li>
                <li>Results in the end of fertility</li>
                <li>Accompanied by various physical changes</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Common Experiences</h4>
            <ul class="list-disc pl-6">
                <li>Hot flashes and night sweats</li>
                <li>Changes in menstrual patterns</li>
                <li>Mood fluctuations</li>
                <li>Sleep disturbances</li>
                <li>Physical body changes</li>
            </ul>`
    },
    'stages-of-menopause': {
        title: 'Stages of Menopause',
        content: `
            <h4 class="text-lg font-semibold mb-4">The Three Main Stages</h4>
            
            <h5 class="font-semibold mb-2">1. Perimenopause</h5>
            <ul class="list-disc pl-6 mb-4">
                <li>First stage of the process</li>
                <li>Can last 4-8 years</li>
                <li>Periods become irregular</li>
                <li>Begin experiencing symptoms</li>
                <li>Fertility declining</li>
            </ul>

            <h5 class="font-semibold mb-2">2. Menopause</h5>
            <ul class="list-disc pl-6 mb-4">
                <li>Officially begins after 12 months without a period</li>
                <li>Average age is 51</li>
                <li>End of reproductive years</li>
                <li>Symptoms may intensify</li>
                <li>Permanent change</li>
            </ul>

            <h5 class="font-semibold mb-2">3. Postmenopause</h5>
            <ul class="list-disc pl-6">
                <li>All years after menopause</li>
                <li>Symptoms may continue</li>
                <li>Increased health risks</li>
                <li>Need for preventive care</li>
                <li>New phase of life</li>
            </ul>`
    },
    'common-symptoms': {
        title: 'Common Symptoms',
        content: `
            <h4 class="text-lg font-semibold mb-4">Physical Symptoms</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Hot flashes and night sweats</li>
                <li>Sleep problems</li>
                <li>Weight changes</li>
                <li>Joint pain</li>
                <li>Vaginal dryness</li>
                <li>Skin changes</li>
                <li>Hair changes</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Emotional Symptoms</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Mood swings</li>
                <li>Anxiety</li>
                <li>Depression</li>
                <li>Irritability</li>
                <li>Memory issues</li>
                <li>Concentration difficulties</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Other Changes</h4>
            <ul class="list-disc pl-6">
                <li>Reduced energy</li>
                <li>Changes in libido</li>
                <li>Bladder issues</li>
                <li>Heart palpitations</li>
                <li>Digestive changes</li>
            </ul>`
    },
    'treatment-options': {
        title: 'Treatment Options',
        content: `
            <h4 class="text-lg font-semibold mb-4">Medical Treatments</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Hormone therapy</li>
                <li>Non-hormonal medications</li>
                <li>Vaginal treatments</li>
                <li>Antidepressants</li>
                <li>Sleep medications</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Alternative Treatments</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Herbal supplements</li>
                <li>Acupuncture</li>
                <li>Mindfulness practices</li>
                <li>Yoga therapy</li>
                <li>Dietary changes</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Lifestyle Modifications</h4>
            <ul class="list-disc pl-6">
                <li>Regular exercise</li>
                <li>Healthy diet</li>
                <li>Stress management</li>
                <li>Good sleep habits</li>
                <li>Regular check-ups</li>
            </ul>`
    },
    'hormone-therapy': {
        title: 'Hormone Therapy',
        content: `
            <h4 class="text-lg font-semibold mb-4">Types of Hormone Therapy</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Systemic estrogen therapy</li>
                <li>Local estrogen therapy</li>
                <li>Combination therapy</li>
                <li>Bioidentical hormones</li>
                <li>Low-dose options</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Benefits</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Reduces hot flashes</li>
                <li>Improves sleep quality</li>
                <li>Prevents bone loss</li>
                <li>Helps with mood stability</li>
                <li>Manages vaginal symptoms</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Important Considerations</h4>
            <ul class="list-disc pl-6">
                <li>Individual assessment needed</li>
                <li>Regular monitoring required</li>
                <li>Different forms available</li>
                <li>Risks and benefits vary</li>
                <li>Not suitable for everyone</li>
            </ul>`
    },
    'natural-remedies': {
        title: 'Natural Remedies',
        content: `
            <h4 class="text-lg font-semibold mb-4">Herbal Supplements</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Black cohosh for hot flashes</li>
                <li>Red clover for night sweats</li>
                <li>Evening primrose oil</li>
                <li>Ginseng for mood</li>
                <li>St. John's wort</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Dietary Supplements</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Vitamin D and calcium</li>
                <li>B-complex vitamins</li>
                <li>Magnesium</li>
                <li>Omega-3 fatty acids</li>
                <li>Iron supplements</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Natural Approaches</h4>
            <ul class="list-disc pl-6">
                <li>Regular exercise</li>
                <li>Meditation</li>
                <li>Acupuncture</li>
                <li>Dietary changes</li>
                <li>Stress reduction</li>
            </ul>`
    },
    'lifestyle-changes': {
        title: 'Lifestyle Changes',
        content: `
            <h4 class="text-lg font-semibold mb-4">Diet Modifications</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Increase whole foods</li>
                <li>Reduce processed foods</li>
                <li>Limit caffeine and alcohol</li>
                <li>Stay hydrated</li>
                <li>Add phytoestrogens</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Exercise Routine</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Regular physical activity</li>
                <li>Strength training</li>
                <li>Flexibility exercises</li>
                <li>Balance work</li>
                <li>Daily walking</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Sleep Habits</h4>
            <ul class="list-disc pl-6">
                <li>Regular sleep schedule</li>
                <li>Cool bedroom environment</li>
                <li>Limit screen time</li>
                <li>Relaxation techniques</li>
                <li>Comfortable bedding</li>
            </ul>`
    },
    'wellness-self-care': {
        title: 'Wellness & Self-Care',
        content: `
            <h4 class="text-lg font-semibold mb-4">Daily Practices</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Mindful meditation</li>
                <li>Gentle exercise</li>
                <li>Adequate rest</li>
                <li>Healthy eating</li>
                <li>Stress management</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Mental Wellness</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Positive thinking</li>
                <li>Social connections</li>
                <li>Hobby engagement</li>
                <li>Learning new skills</li>
                <li>Emotional expression</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Physical Care</h4>
            <ul class="list-disc pl-6">
                <li>Regular check-ups</li>
                <li>Skin care routine</li>
                <li>Dental hygiene</li>
                <li>Eye care</li>
                <li>Bone health</li>
            </ul>`
    },
    'exercise-tips': {
        title: 'Exercise Tips',
        content: `
            <h4 class="text-lg font-semibold mb-4">Recommended Activities</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Walking (30 minutes daily)</li>
                <li>Swimming or water aerobics</li>
                <li>Yoga or gentle stretching</li>
                <li>Light weight training</li>
                <li>Low-impact cardio</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Benefits</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Weight management</li>
                <li>Bone strength maintenance</li>
                <li>Mood improvement</li>
                <li>Better sleep quality</li>
                <li>Reduced symptoms</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Exercise Guidelines</h4>
            <ul class="list-disc pl-6">
                <li>Start slowly and build up</li>
                <li>Stay consistent</li>
                <li>Listen to your body</li>
                <li>Stay hydrated</li>
                <li>Include variety</li>
            </ul>`
    },
    'nutrition-guide': {
        title: 'Nutrition Guide',
        content: `
            <h4 class="text-lg font-semibold mb-4">Essential Nutrients</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Calcium (1,200 mg daily)</li>
                <li>Vitamin D (600-800 IU)</li>
                <li>Protein (varied sources)</li>
                <li>Iron-rich foods</li>
                <li>Fiber (25-30g daily)</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Recommended Foods</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Leafy green vegetables</li>
                <li>Whole grains</li>
                <li>Lean proteins</li>
                <li>Healthy fats</li>
                <li>Fresh fruits</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Foods to Limit</h4>
            <ul class="list-disc pl-6">
                <li>Processed foods</li>
                <li>Added sugars</li>
                <li>Excessive caffeine</li>
                <li>Alcohol</li>
                <li>High-sodium foods</li>
            </ul>`
    },
    'stress-management': {
        title: 'Stress Management',
        content: `
            <h4 class="text-lg font-semibold mb-4">Relaxation Techniques</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Deep breathing exercises</li>
                <li>Progressive muscle relaxation</li>
                <li>Guided visualization</li>
                <li>Mindfulness meditation</li>
                <li>Gentle yoga</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Physical Activities</h4>
            <ul class="list-disc pl-6 mb-4">
                <li>Walking in nature</li>
                <li>Swimming</li>
                <li>Gardening</li>
                <li>Dancing</li>
                <li>Gentle stretching</li>
            </ul>

            <h4 class="text-lg font-semibold mb-4">Support Systems</h4>
            <ul class="list-disc pl-6">
                <li>Family and friends</li>
                <li>Support groups</li>
                <li>Professional counseling</li>
                <li>Online communities</li>
                <li>Healthcare providers</li>
            </ul>`
    }
};

// Function to show resource content
function showResourceContent(resourceId) {
    const resource = resourceContent[resourceId];
    if (resource) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('resourceModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'resourceModal';
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center z-50';
            modal.innerHTML = `
                <div class="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                    <div class="flex justify-between items-center mb-6">
                        <h3 id="modalTitle" class="text-2xl font-bold text-purple-600"></h3>
                        <button onclick="closeResourceModal()" class="text-gray-500 hover:text-gray-700">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div id="modalContent" class="prose max-w-none text-gray-700"></div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        // Update modal content
        document.getElementById('modalTitle').textContent = resource.title;
        document.getElementById('modalContent').innerHTML = resource.content;
        modal.classList.remove('hidden');
    }
}

// Function to close resource modal
function closeResourceModal() {
    const modal = document.getElementById('resourceModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}
