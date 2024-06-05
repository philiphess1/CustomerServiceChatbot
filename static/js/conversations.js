document.addEventListener('DOMContentLoaded', function() {
    var sessionLinks = document.querySelectorAll('.session-link');
    var sessionConversations = document.querySelectorAll('.session-conversation');

    // Show the first conversation when the page loads
    if (sessionConversations.length > 0) {
        sessionConversations[0].style.display = 'block';
    }

    sessionLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            var sessionId = this.dataset.sessionId;

            sessionConversations.forEach(function(conversation) {
                if (conversation.id === sessionId) {
                    conversation.style.display = 'block';
                } else {
                    conversation.style.display = 'none';
                }
            });
        });
    });
});