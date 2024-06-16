        // JavaScript for the widget
        // Function to open the chatbot
        var lastUserMessage = "";
        var greetingShown = false;

        // Function to show the email popup form
        function showEmailPopup() {
            // Get the current URL path
            var path = window.location.pathname;

            // Split the path into segments
            var segments = path.split('/');

            // The user ID should be the first segment after the leading empty segment
            var userId = segments[1];

            // The chatbot ID should be the second segment
            var chatbotId = segments[2];

            var popup = document.createElement('div');
            popup.id = 'email-popup';
            popup.innerHTML = `
                <form id="email-form">
                    <label for="name">Name:</label>
                    <input type="text" id="name" name="name" required>
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                    <input type="submit" value="Submit">
                </form>
                <p id="email-error" style="color: red; display: none;">Invalid email format. Please try again.</p>
            `;
            document.body.appendChild(popup);

            // Create an overlay over the widget
            var widgetOverlay = document.createElement('div');
            widgetOverlay.id = 'widget-overlay';
            widgetOverlay.style.position = 'absolute';
            widgetOverlay.style.width = '100%';
            widgetOverlay.style.height = '100%';
            widgetOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
            document.querySelector('.widget').appendChild(widgetOverlay);

            // Fetch the session data
            fetch('/' + userId + '/' + chatbotId + '/get-session-data', {
                method: 'GET',
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // If an email is already associated with the session ID
                if (data.email) {
                    // Hide the form
                    document.getElementById('email-popup').style.display = 'none';

                    // Remove the overlay
                    var widgetOverlay = document.getElementById('widget-overlay');
                    if (widgetOverlay) {
                        widgetOverlay.parentNode.removeChild(widgetOverlay);
                    }
                }
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
            });

// The rest of your code...
            // Handle form submission
            document.getElementById('email-form').addEventListener('submit', function(event) {
                event.preventDefault();
                var name = document.getElementById('name').value;
                var email = document.getElementById('email').value;

                // Validate the email
                var emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
                if (!emailRegex.test(email)) {
                    // Show the error message
                    document.getElementById('email-error').style.display = 'block';
                    return;
                }

                fetch('/' + userId + '/' + chatbotId + '/save-email', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: 'name=' + encodeURIComponent(name) + '&email=' + encodeURIComponent(email)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(data.message);
                    // Close the popup and remove the overlay
                    popup.remove();
                    widgetOverlay.remove();
                })
                .catch(error => {
                    console.error('There has been a problem with your fetch operation:', error);
                    // Show the error message
                    document.getElementById('email-error').style.display = 'block';
                });
            });
        }

        if (settings.include_email_form) {
            showEmailPopup();
        }

        function showGreetingMessage() {
            // If the greeting has already been shown, don't show it again
            if (greetingShown) {
                return;
            }

            // Get the current URL path
            var path = window.location.pathname;

            // Split the path into segments
            var segments = path.split('/');

            // The user ID should be the first segment after the leading empty segment
            var userId = segments[1];

            // The chatbot ID should be the second segment
            var chatbotId = segments[2];

            // Check if there are any existing messages in the chatbox
            const chatboxBody = document.querySelector(".chatbox-body");
            const existingMessages = 0;

            // If there are no existing messages, show the greeting with a delay
            if (!existingMessages) {
                fetch('/' + userId + '/' + chatbotId + '/greeting_message')
                    .then(response => response.json())
                    .then(data => {
                        const greetingMessage = data.greeting_message;
                        setTimeout(() => {
                            appendMessage("Chatbot", "left", greetingMessage);
                        }, 800); // Adjust the delay time as needed

                        // Set the flag to true so the greeting won't be shown again
                        greetingShown = true;
                    });
            }
        }
        showGreetingMessage();

        // Function to show the three dots typing indicator
        function showTypingIndicator() {
            const chatboxBody = document.querySelector(".chatbox-body");
            const userInput = document.getElementById("user-input");
    
            // Disable the input field
            userInput.disabled = true;


            const typingIndicatorHTML = `
                <div class="msg left-msg">
                    <div class="msg-image">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            chatboxBody.insertAdjacentHTML("beforeend", typingIndicatorHTML);
            chatboxBody.scrollTop = chatboxBody.scrollHeight;

        }

        // Function to hide the three dots typing indicator
        function hideTypingIndicator() {
            const typingIndicator = document.querySelector(".msg-image");
            const userInput = document.getElementById("user-input");
    
            // Disable the input field
            userInput.disabled = false;

            if (typingIndicator) {
                typingIndicator.remove();
            }
             // Enable the input field
            // const inputField = document.querySelector("user-input");
            // inputField.disabled = false;
        }

        // Add an event listener to the input element to listen for the "keydown" event
        // Add an event listener to the input element to listen for the "keydown" event
        var userInput = document.getElementById("user-input");
        userInput.addEventListener("keydown", function(event) {
            if (event.key === "Enter") {
                // Call the function to send the user message
                sendUserMessage();
            }
        });

        // Add an event listener to the send button to listen for clicks
        var sendButton = document.getElementById("send-button");
        sendButton.addEventListener("click", sendUserMessage);

        // Function to send a message from the user
        function sendUserMessage() {
            var userInput = document.getElementById("user-input");
            var message = userInput.value.trim();
            if (message !== "") {
                lastUserMessage = message;
                appendMessage("You", "right", message);
                showTypingIndicator(); // Show typing indicator before sending the message
                userInput.value = "";
                botResponse(message);
            }
        }
        // // Add an event listener to the send button to listen for clicks
        // var sendButton = document.getElementById("send-button");
        // sendButton.addEventListener("click", sendBotMessage);

        // Function to send a message from the user
        function sendBotMessage() {
            var userInput = document.getElementById("user-input");
            var message = userInput.value.trim();
            if (message !== "") {
                lastUserMessage = message;
                appendMessage_determined("You", "right", message);
                userInput.value = "";
                botResponse(message);
            }
        }

        // Function to handle question click
        function handleQuestionClick() {
            var message = this.textContent;
            var response = this.getAttribute('data-response');
            appendMessage_determined("You", "right", message); // Display user's message
            appendMessage_determined("Bot", "left", response); // Display bot's response
        }

        // Add event listeners to the question elements
        var suggestedQuestions = document.querySelectorAll('.suggested-question');
        suggestedQuestions.forEach(function(question) {
            question.addEventListener('click', handleQuestionClick);
        });

        function appendMessage_determined(name, side, text, sources) {
            text = text.replace(/\n/g, '<br>');
            text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
            text = text.replace(/(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)/g, '<a href="mailto:$1">$1</a>');
            const chatboxBody = document.querySelector(".chatbox-body");
            const sourcesHTML = appendSources(sources);
            const msgHTML = `
                <div class="msg ${side}-msg">
                    <div class="msg-info">
                        ${side === "left" ? `
                        <div class="msg-info-name">
                            <img src="/static/images/chatbot.svg" alt="Chatbot Icon" />
                        </div>
                        ` : ""}
                    </div>
                    ${side === "right" ? `
                    <div class="msg-bubble">
                        <div class="msg-text-user">${text}</div>
                    </div>
                    ` : ""}
                    ${side === "left" ? `
                    <div class="msg-bubble">
                        <div class="msg-text">${text}</div>
                        ${sourcesHTML}
                    </div>
                    ` : ""}
                </div>
                <div class="msg ${side}-msg">
                    ${side === "left" ? `
                    <div class="post" data-post-id="7712">
                        <div class="post-ratings-container">
                            <div class="post-rating">
                                <button class="post-rating-button material-icons like-button">thumb_up</button>
                            </div>
                            <div class="post-rating">
                                <button class="post-rating-button material-icons dislike-button">thumb_down</button>
                            </div>
                        </div>
                    </div>
                    ` : ""}
                </div>
            `;
            chatboxBody.insertAdjacentHTML("beforeend", msgHTML);
            chatboxBody.scrollTop = chatboxBody.scrollHeight;
        
            

            if (side === "left" && lastUserMessage.trim() !== "") {
                storeQuestionAnswer(lastUserMessage, text);
            }
            if (side === "left") {
            const messageElements = document.querySelectorAll('.msg-text');
            const messageElement = messageElements[messageElements.length - 1];
                const displayMessage = (text, index = 0, message = '') => {
                    if (index < text.length) {
                        message += text[index];
                        index++;
                        setTimeout(() => {
                            messageElement.innerHTML = message;
                            displayMessage(text, index, message);
                        }, 14);
                    }
                };

                displayMessage(text);
                const likeButtons = chatboxBody.querySelectorAll(".like-button");
                const dislikeButtons = chatboxBody.querySelectorAll(".dislike-button");
                likeButtons.forEach(function(likeButton) {
                    likeButton.addEventListener("click", function() {
                        if (!likeButton.classList.contains("clicked")) {
                            likeButton.classList.add("clicked");
                            likeButton.style.color = "green";
                            dislikeButtons.forEach(function(dislikeButton) {
                                dislikeButton.classList.remove("clicked");
                                dislikeButton.style.color = "#555555";
                                dislikeButton.disabled = true; // Disable the dislike button
                            });
                            sendFeedback("Like", text, lastUserMessage);
                            likeButton.disabled = true; // Disable the like button
                        }
                    });
                });
                dislikeButtons.forEach(function(dislikeButton) {
                    dislikeButton.addEventListener("click", function() {
                        if (!dislikeButton.classList.contains("clicked")) {
                            dislikeButton.classList.add("clicked");
                            dislikeButton.style.color = "#e65b5b";
                            likeButtons.forEach(function(likeButton) {
                                likeButton.classList.remove("clicked");
                                likeButton.style.color = "#555555";
                                likeButton.disabled = true; // Disable the like button
                            });
                            sendFeedback("Dislike", text, lastUserMessage);
                            dislikeButton.disabled = true; // Disable the dislike button
                        }
                    });
                });
            }
        }

        function appendSources(sources) {
            if (!sources || sources.length === 0) return '';

            let sourcesHTML = '';
            const validSources = sources.filter(source => source.source_url.startsWith('http://') || source.source_url.startsWith('https://')); // Filter to only include URLs

            // Remove duplicates
            const uniqueSources = Array.from(new Set(validSources.map(source => source.source_url)))
                .map(source_url => {
                    return validSources.find(source => source.source_url === source_url)
                });

            if (uniqueSources.length > 0) {
                sourcesHTML += '<div class="msg-sources"><br>Sources:<br>';
                uniqueSources
                    .slice(0, 3) // Get the first URL source
                    .forEach((source) => {
                        sourcesHTML += `
                            <div class="source" style="border: 1px solid #ccc; border-radius: 10px; overflow: auto; max-width: 280px; word-wrap: break-word; margin-bottom: 10px; background-color: white;">
                                <a href="${source.source_url}" target="_blank" style="display: block; padding: 10px; text-decoration: none; color: black;">
                                    <img src="http://www.google.com/s2/favicons?domain=${source.source_url}" alt="Favicon" style="width: 24px; height: 24px; margin-right: 10px;">
                                    ${source.source_url}
                                </a>
                            </div>
                        `;
                    });
                sourcesHTML += '</div>';
            }

            return sourcesHTML;
        }
        function appendMessage(name, side, text, sources) {
            text = text.replace(/\n/g, '<br>');
            text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
            text = text.replace(/(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)/g, '<a href="mailto:$1">$1</a>');
            const chatboxBody = document.querySelector(".chatbox-body");
            const sourcesHTML = appendSources(sources);
            const msgHTML = `
                <div class="msg ${side}-msg">
                    <div class="msg-info">
                        ${side === "left" ? `
                        <div class="msg-info-name">
                            <img src="/static/images/chatbot.svg" alt="Chatbot Icon" />
                        </div>
                        ` : ""}
                    </div>
                    ${side === "right" ? `
                    <div class="msg-bubble">
                        <div class="msg-text-user">${text}</div>
                    </div>
                    ` : ""}
                    ${side === "left" ? `
                    <div class="msg-bubble">
                        <div class="msg-text">${text}</div>
                        ${sourcesHTML}
                    </div>
                    ` : ""}
                </div>
                <div class="msg ${side}-msg">
                    ${side === "left" ? `
                    <div class="post" data-post-id="7712">
                        <div class="post-ratings-container">
                            <div class="post-rating">
                                <button class="post-rating-button material-icons like-button">thumb_up</button>
                            </div>
                            <div class="post-rating">
                                <button class="post-rating-button material-icons dislike-button">thumb_down</button>
                            </div>
                        </div>
                    </div>
                    ` : ""}
                </div>
            `;
            chatboxBody.insertAdjacentHTML("beforeend", msgHTML);
            chatboxBody.scrollTop = chatboxBody.scrollHeight;
        
            

            if (side === "left" && lastUserMessage.trim() !== "") {
                storeQuestionAnswer(lastUserMessage, text);
            }
            if (side === "left") {
            const messageElements = document.querySelectorAll('.msg-text');
            const messageElement = messageElements[messageElements.length - 1];
                const displayMessage = (text, index = 0, message = '') => {
                    if (index < text.length) {
                        message += text[index];
                        index++;
                        setTimeout(() => {
                            messageElement.innerHTML = message;
                            displayMessage(text, index, message);
                        }, 20);
                    }
                };

                displayMessage(text);
                const likeButtons = chatboxBody.querySelectorAll(".like-button");
                const dislikeButtons = chatboxBody.querySelectorAll(".dislike-button");
                likeButtons.forEach(function(likeButton) {
                    likeButton.addEventListener("click", function() {
                        if (!likeButton.classList.contains("clicked")) {
                            likeButton.classList.add("clicked");
                            likeButton.style.color = "green";
                            dislikeButtons.forEach(function(dislikeButton) {
                                dislikeButton.classList.remove("clicked");
                                dislikeButton.style.color = "#555555";
                                dislikeButton.disabled = true; // Disable the dislike button
                            });
                            sendFeedback("Like", text, lastUserMessage);
                            likeButton.disabled = true; // Disable the like button
                        }
                    });
                });
                dislikeButtons.forEach(function(dislikeButton) {
                    dislikeButton.addEventListener("click", function() {
                        if (!dislikeButton.classList.contains("clicked")) {
                            dislikeButton.classList.add("clicked");
                            dislikeButton.style.color = "#e65b5b";
                            likeButtons.forEach(function(likeButton) {
                                likeButton.classList.remove("clicked");
                                likeButton.style.color = "#555555";
                                likeButton.disabled = true; // Disable the like button
                            });
                            sendFeedback("Dislike", text, lastUserMessage);
                            dislikeButton.disabled = true; // Disable the dislike button
                        }
                    });
                });
            }
        }
        function sendFeedback(type, botResponse, userQuestion) {
            // Get the current URL path
            var path = window.location.pathname;

            // Split the path into segments
            var segments = path.split('/');

            // The user ID should be the first segment after the leading empty segment
            var userId = segments[1];
            var chatbotId = segments[2];

            fetch('/' + userId + '/' + chatbotId + '/store_feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    feedback_type: type,
                    bot_response: botResponse,
                    user_question: userQuestion,
                    id: lastRecordId
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        function storeQuestionAnswer(question, answer) {
            // Get the current URL path
            var path = window.location.pathname;

            // Split the path into segments
            var segments = path.split('/');

            // The user ID should be the first segment after the leading empty segment
            var userId = segments[1];
            var chatbotId = segments[2];

            fetch('/' + userId + '/' + chatbotId + '/store_qa', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: question,
                    answer: answer
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                lastRecordId = data.id;
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        document.getElementById('chatboxCloseButton').addEventListener('click', function() {
            var iframe = parent.document.getElementById('e');
            var widget = parent.document.getElementById('b');
            iframe.style.opacity = 0;
            iframe.style.transform = 'scale(0)'; // shrink to no size
            setTimeout(function() {
                iframe.style.display = 'none';
                // Reappear logic for the widget
                widget.style.opacity = 1;
                widget.style.transform = 'scale(1)';
                widget.style.display = 'block'; // or 'flex', 'inline-block', etc., depending on your layout
            }, 200); // after transition ends
        });

        function botResponse(rawText) {
            // Get the current URL path
            var path = window.location.pathname;

            // Split the path into segments
            var segments = path.split('/');

            // The user ID should be the first segment after the leading empty segment
            var userId = segments[1];

            // The chatbot ID should be the second segment
            var chatbotId = segments[2];

            $.post("/" + userId + "/" + chatbotId + "/chat", { message: rawText })
            .done(function(data) {
                // Hide the typing indicator when the bot responds
                hideTypingIndicator();

                // Assuming the API response includes a 'sources' array
                let sources = data.sources || []; // Fallback to an empty array if no sources are provided

                // Now pass the content and sources to appendMessage
                appendMessage("Chatbot", "left", data.content, sources);
            })
            .fail(function() {
                // Hide the typing indicator in case of an error
                hideTypingIndicator();

                appendMessage("Chatbot", "left", "An error occurred while processing your request");
            });
        }