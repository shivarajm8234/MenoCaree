// Resource content data
const resourceContent = {
    'what-is-menopause': {
        title: 'What is Menopause?',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">Definition</h4>
                    <p class="text-gray-700">Menopause is officially diagnosed when a woman has gone 12 consecutive months without a menstrual period, marking the end of her reproductive years.</p>
                </div>
                
                <div>
                    <h4 class="text-lg font-semibold mb-3">Key Facts</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Average age is 51 years</li>
                        <li>Natural part of aging</li>
                        <li>Caused by declining estrogen levels</li>
                        <li>Results in the end of fertility</li>
                        <li>Accompanied by various physical changes</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Common Experiences</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Hot flashes and night sweats</li>
                        <li>Changes in menstrual patterns</li>
                        <li>Mood fluctuations</li>
                        <li>Sleep disturbances</li>
                        <li>Physical body changes</li>
                    </ul>
                </div>
            </div>`
    },
    'stages-of-menopause': {
        title: 'Stages of Menopause',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">The Three Main Stages</h4>
                    
                    <div class="space-y-4">
                        <div>
                            <h5 class="font-semibold mb-2">1. Perimenopause</h5>
                            <ul class="list-disc pl-6 space-y-2 text-gray-700">
                                <li>First stage of the process</li>
                                <li>Can last 4-8 years</li>
                                <li>Periods become irregular</li>
                                <li>Begin experiencing symptoms</li>
                                <li>Fertility declining</li>
                            </ul>
                        </div>

                        <div>
                            <h5 class="font-semibold mb-2">2. Menopause</h5>
                            <ul class="list-disc pl-6 space-y-2 text-gray-700">
                                <li>Officially begins after 12 months without a period</li>
                                <li>Average age is 51</li>
                                <li>End of reproductive years</li>
                                <li>Symptoms may intensify</li>
                                <li>Permanent change</li>
                            </ul>
                        </div>

                        <div>
                            <h5 class="font-semibold mb-2">3. Postmenopause</h5>
                            <ul class="list-disc pl-6 space-y-2 text-gray-700">
                                <li>All years after menopause</li>
                                <li>Symptoms may continue</li>
                                <li>Increased health risks</li>
                                <li>Need for preventive care</li>
                                <li>New phase of life</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>`
    },
    'common-symptoms': {
        title: 'Common Symptoms',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">Physical Symptoms</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Hot flashes and night sweats</li>
                        <li>Sleep problems</li>
                        <li>Weight changes</li>
                        <li>Joint pain</li>
                        <li>Vaginal dryness</li>
                        <li>Skin changes</li>
                        <li>Hair changes</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Emotional Symptoms</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Mood swings</li>
                        <li>Anxiety</li>
                        <li>Depression</li>
                        <li>Irritability</li>
                        <li>Memory issues</li>
                        <li>Concentration difficulties</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Other Changes</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Reduced energy</li>
                        <li>Changes in libido</li>
                        <li>Bladder issues</li>
                        <li>Heart palpitations</li>
                        <li>Digestive changes</li>
                    </ul>
                </div>
            </div>`
    },
    'hormone-therapy': {
        title: 'Hormone Therapy',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">Types of Hormone Therapy</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Systemic estrogen therapy</li>
                        <li>Local estrogen therapy</li>
                        <li>Combination therapy</li>
                        <li>Bioidentical hormones</li>
                        <li>Low-dose options</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Benefits</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Reduces hot flashes</li>
                        <li>Improves sleep quality</li>
                        <li>Prevents bone loss</li>
                        <li>Helps with mood stability</li>
                        <li>Manages vaginal symptoms</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Important Considerations</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Individual assessment needed</li>
                        <li>Regular monitoring required</li>
                        <li>Different forms available</li>
                        <li>Risks and benefits vary</li>
                        <li>Not suitable for everyone</li>
                    </ul>
                </div>
            </div>`
    },
    'natural-remedies': {
        title: 'Natural Remedies',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">Herbal Supplements</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Black cohosh for hot flashes</li>
                        <li>Red clover for night sweats</li>
                        <li>Evening primrose oil</li>
                        <li>Ginseng for mood</li>
                        <li>St. John's wort</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Dietary Supplements</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Vitamin D and calcium</li>
                        <li>B-complex vitamins</li>
                        <li>Magnesium</li>
                        <li>Omega-3 fatty acids</li>
                        <li>Iron supplements</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Natural Approaches</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Regular exercise</li>
                        <li>Meditation</li>
                        <li>Acupuncture</li>
                        <li>Dietary changes</li>
                        <li>Stress reduction</li>
                    </ul>
                </div>
            </div>`
    },
    'lifestyle-changes': {
        title: 'Lifestyle Changes',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">Diet Modifications</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Increase whole foods</li>
                        <li>Reduce processed foods</li>
                        <li>Limit caffeine and alcohol</li>
                        <li>Stay hydrated</li>
                        <li>Add phytoestrogens</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Exercise Routine</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Regular physical activity</li>
                        <li>Strength training</li>
                        <li>Flexibility exercises</li>
                        <li>Balance work</li>
                        <li>Daily walking</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Sleep Habits</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Regular sleep schedule</li>
                        <li>Cool bedroom environment</li>
                        <li>Limit screen time</li>
                        <li>Relaxation techniques</li>
                        <li>Comfortable bedding</li>
                    </ul>
                </div>
            </div>`
    },
    'exercise-tips': {
        title: 'Exercise Tips',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">Recommended Activities</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Walking (30 minutes daily)</li>
                        <li>Swimming or water aerobics</li>
                        <li>Yoga or gentle stretching</li>
                        <li>Light weight training</li>
                        <li>Low-impact cardio</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Benefits</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Weight management</li>
                        <li>Bone strength maintenance</li>
                        <li>Mood improvement</li>
                        <li>Better sleep quality</li>
                        <li>Reduced symptoms</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Exercise Guidelines</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Start slowly and build up</li>
                        <li>Stay consistent</li>
                        <li>Listen to your body</li>
                        <li>Stay hydrated</li>
                        <li>Include variety</li>
                    </ul>
                </div>
            </div>`
    },
    'nutrition-guide': {
        title: 'Nutrition Guide',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">Essential Nutrients</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Calcium (1,200 mg daily)</li>
                        <li>Vitamin D (600-800 IU)</li>
                        <li>Protein (varied sources)</li>
                        <li>Iron-rich foods</li>
                        <li>Fiber (25-30g daily)</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Recommended Foods</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Leafy green vegetables</li>
                        <li>Whole grains</li>
                        <li>Lean proteins</li>
                        <li>Healthy fats</li>
                        <li>Fresh fruits</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Foods to Limit</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Processed foods</li>
                        <li>Added sugars</li>
                        <li>Excessive caffeine</li>
                        <li>Alcohol</li>
                        <li>High-sodium foods</li>
                    </ul>
                </div>
            </div>`
    },
    'stress-management': {
        title: 'Stress Management',
        content: `
            <div class="space-y-6">
                <div>
                    <h4 class="text-lg font-semibold mb-3">Relaxation Techniques</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Deep breathing exercises</li>
                        <li>Progressive muscle relaxation</li>
                        <li>Guided visualization</li>
                        <li>Mindfulness meditation</li>
                        <li>Gentle yoga</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Physical Activities</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Walking in nature</li>
                        <li>Swimming</li>
                        <li>Gardening</li>
                        <li>Dancing</li>
                        <li>Gentle stretching</li>
                    </ul>
                </div>

                <div>
                    <h4 class="text-lg font-semibold mb-3">Support Systems</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700">
                        <li>Family and friends</li>
                        <li>Support groups</li>
                        <li>Professional counseling</li>
                        <li>Online communities</li>
                        <li>Healthcare providers</li>
                    </ul>
                </div>
            </div>`
    }
};

// Function to show resource content
function showResourceContent(resourceId) {
    const resource = resourceContent[resourceId];
    if (resource) {
        const modal = document.getElementById('resourceModal');
        if (modal) {
            document.getElementById('modalTitle').textContent = resource.title;
            document.getElementById('modalContent').innerHTML = resource.content;
            modal.classList.remove('hidden');
        }
    }
}

// Function to close resource modal
function closeResourceModal() {
    const modal = document.getElementById('resourceModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}
