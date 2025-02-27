document.addEventListener('DOMContentLoaded', () => {
    const topics = document.querySelectorAll('.topic');
    const joinButtons = document.querySelectorAll('.btn-join');

    // Add hover effect to topics
    topics.forEach(topic => {
        topic.addEventListener('mouseenter', () => {
            topic.style.transform = 'translateY(-2px)';
            topic.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
        });

        topic.addEventListener('mouseleave', () => {
            topic.style.transform = 'translateY(0)';
            topic.style.boxShadow = 'none';
        });

        // Make entire topic clickable
        topic.addEventListener('click', () => {
            // In a full implementation, this would navigate to the topic page
            alert('This feature will be implemented soon!');
        });
    });

    // Handle event join buttons
    joinButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const eventTitle = e.target.parentElement.querySelector('h4').textContent;
            
            // In a full implementation, this would handle event registration
            alert(`You will be notified about: ${eventTitle}`);
            button.textContent = 'Registered';
            button.disabled = true;
        });
    });

    // Simulate real-time updates (in a full implementation, this would use WebSocket)
    setInterval(() => {
        updateTopicStats();
    }, 30000);

    function updateTopicStats() {
        const topics = document.querySelectorAll('.topic-stats');
        topics.forEach(stats => {
            // Simulate small random changes in numbers
            const posts = stats.querySelector('span:first-child');
            const members = stats.querySelector('span:last-child');
            
            const currentPosts = parseInt(posts.textContent.split(': ')[1]);
            const currentMembers = parseInt(members.textContent.split(': ')[1]);
            
            posts.textContent = `Posts: ${currentPosts + Math.floor(Math.random() * 3)}`;
            members.textContent = `Members: ${currentMembers + Math.floor(Math.random() * 2)}`;
        });
    }
});
