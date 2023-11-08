        // JavaScript for the widget
        // Function to open the chatbot
        var lastUserMessage = "";

        function openChatbot() {
            var widgetButton = document.getElementById("widget-button");
            widgetButton.style.animation = "slide-down 0.5s ease-out";
            setTimeout(function() {
                widgetButton.style.display = "none";
                document.getElementById("chatbot").style.display = "block";
                document.addEventListener("click", closeChatbotOnClickOutside);
            }, 300);
        }

        // Function to close the chatbot
        function closeChatbot() {
            var widgetButton = document.getElementById("widget-button");
            var chatbot = document.getElementById("chatbot");
            chatbot.style.animation = "slide-down 0.5s ease-out";
            setTimeout(function() {
                chatbot.style.display = "none";
                chatbot.style.animation = ""; // Remove animation property
                document.removeEventListener("click", closeChatbotOnClickOutside);
                setTimeout(function() {
                    widgetButton.style.display = "block";
                    widgetButton.style.animation = "slide-up 0.5s ease-out";
                }, 100);
            }, 300);
        }

        // Function to close the chatbot when clicked outside
        function closeChatbotOnClickOutside(event) {
            var chatbot = document.getElementById("chatbot");
            if (!chatbot.contains(event.target)) {
                closeChatbot();
            }
        }

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

        // Attach event listeners to the widget button and chatbox close button
        document.getElementById("widget-button").addEventListener("click", openChatbot);
        document.getElementById("chatbox-close").addEventListener("click", closeChatbot);

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

        function appendMessage(name, side, text) {
            const chatboxBody = document.querySelector(".chatbox-body");
            const msgHTML = `
                <div class="msg ${side}-msg">
                    <div class="msg-info">
                        <div class="msg-info-name">${name}</div>
                    </div>
                </div>
                ${side === "right" ? `
                <div class="msg ${side}-msg">
                    <div class="msg-bubble">
                        <div class="msg-text-user">${text}</div>
                    </div>
                </div>
                ` : ""}
                ${side === "left" ? `
                <div class="msg ${side}-msg">
                    <div class="msg-bubble">
                        <div class="msg-text"></div>
                    </div>
                </div>
                ` : ""}
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

            

            if (side === "left") {
                const messageElements = document.querySelectorAll('.msg-text');
            const messageElement = messageElements[messageElements.length - 1];
                const displayMessage = (text, index = 0, message = '') => {
                    if (index < text.length) {
                        message += text[index];
                        index++;
                        setTimeout(() => {
                            messageElement.textContent = message;
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
                            sendFeedback("like", text, lastUserMessage);
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
                            sendFeedback("dislike", text, lastUserMessage);
                            dislikeButton.disabled = true; // Disable the dislike button
                        }
                    });
                });
            }
        }
        function sendFeedback(type, botResponse, userQuestion) {
            fetch('/store_feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    feedback_type: type,
                    bot_response: botResponse,
                    user_question: userQuestion
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


        function botResponse(rawText) {
            $.post("/chat", { message: rawText })
            .done(function(data) {
                // Hide the typing indicator when the bot responds
                hideTypingIndicator();

                appendMessage("Chatbot", "left", data.response);
            })
            .fail(function() {
                // Hide the typing indicator in case of an error
                hideTypingIndicator();

                appendMessage("Chatbot", "left", "An error occurred while processing your request");
            });
        }

        document.getElementById('refresh').addEventListener('click', function() {
            // Refresh the page
            location.reload();
        });
