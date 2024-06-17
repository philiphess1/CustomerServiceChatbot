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

document.addEventListener('DOMContentLoaded', function() {
    var sessionLinks = document.querySelectorAll('.session-link');

    sessionLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // Remove the 'selected' class from all links
            sessionLinks.forEach(function(otherLink) {
                otherLink.style.backgroundColor = ''; // Reset the background color
            });

            // Add the 'selected' class to the clicked link
            this.style.backgroundColor = 'rgb(13, 132, 255)'; 

            var selectedId = this.dataset.sessionId;
            var convo = document.getElementById(selectedId);

            if (convo) {
                var individualConvos = document.querySelectorAll('.individual-convo');
                individualConvos.forEach(function(convo) {
                    convo.style.display = 'none';
                });

                convo.style.display = 'block';

                // Hide the "no-conversation-message" element
                var noConversationMessage = document.getElementById('no-conversation-message');
                if (noConversationMessage) {
                    noConversationMessage.style.display = 'none';
                }
            }
        });
    });
});