// chatbot.js

// Function to inject the chatbot GUI into the website
function injectChatbot() {
    // Create a container div for the chatbot
    var chatbotContainer = document.createElement('div');
    chatbotContainer.id = 'chatbotContainer';
    chatbotContainer.style.position = 'fixed';
    chatbotContainer.style.bottom = '20px';
    chatbotContainer.style.right = '20px';
    chatbotContainer.style.zIndex = '9999';
    chatbotContainer.style.backgroundColor = '#ffffff';
    chatbotContainer.style.border = '1px solid #ccc';
    chatbotContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
    
    // Create an iframe for the chatbot GUI
    var chatbotIframe = document.createElement('iframe');
    chatbotIframe.src = 'http://127.0.0.1:5000/72/91';  // This will need to be a variable passed in
    chatbotIframe.width = '360.5';
    chatbotIframe.height = '600';
    chatbotIframe.style.border = 'none';
    chatbotIframe.id = 'e';
    chatbotIframe.style.display = 'None';
    chatbotIframe.style.position = 'fixed';
    chatbotIframe.style.bottom = '100px'; // Adjust this value to move the iframe up or down
    chatbotIframe.style.right = '30px'; // Adjust this value to move the iframe left or right
    chatbotIframe.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.5)'; // Add a box shadow
    chatbotIframe.style.borderRadius = '10px'; // Add rounded corners

    // Create a button to toggle the chatbot visibility
    var toggleButton = document.createElement('img');
    toggleButton.id = 'b';
    toggleButton.src = 'https://app.eccoai.org//static/images/ecco_icon_black.svg'; // This will need to be a variable passed in
    toggleButton.alt = 'Chat';
    toggleButton.style.width = '80px';
    toggleButton.style.height = '80px';
    toggleButton.style.position = 'fixed';
    toggleButton.style.bottom = '10px';
    toggleButton.style.right = '10px';
    toggleButton.style.zIndex = '1000';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.transition = 'transform 0.3s ease-in-out';
    toggleButton.addEventListener('click', function() {
        chatbotIframe.style.display = (chatbotIframe.style.display === 'none') ? 'block' : 'none';
    });

    // Create a welcome message
    var welcomeMessage = document.createElement('div');
    welcomeMessage.id = 'p';
    welcomeMessage.style.display = 'block';
    welcomeMessage.style.position = 'fixed';
    welcomeMessage.style.bottom = '100px';
    welcomeMessage.style.right = '15px';
    welcomeMessage.style.zIndex = '10000';
    welcomeMessage.style.background = '#fff';
    welcomeMessage.style.border = '1px solid #ccc';
    welcomeMessage.style.padding = '10px';
    welcomeMessage.style.borderRadius = '5px';
    welcomeMessage.style.boxShadow = '0 0 10px rgba(0,0,0,.1)';
    welcomeMessage.textContent = 'hello, ask questions here'; // This will need to be a variable passed in

    // Create a close button for the welcome message
    var closeButton = document.createElement('span');
    closeButton.id = 'c';
    closeButton.style.display = 'none';
    closeButton.style.position = 'fixed';
    closeButton.style.bottom = '128px';
    closeButton.style.right = '10px';
    closeButton.style.zIndex = '10001';
    closeButton.style.cursor = 'pointer';
    closeButton.style.padding = '2px 6px';
    closeButton.style.borderRadius = '10px';
    closeButton.style.backgroundColor = '#dadada';
    closeButton.style.fontFamily = 'arial';
    closeButton.style.color = '#4e4e4e';
    closeButton.textContent = 'x';

    // Add mouseover and mouseout event listeners to the welcome message and close button
    welcomeMessage.onmouseover = closeButton.onmouseover = function() {
        closeButton.style.display = 'block';
    };
    welcomeMessage.onmouseout = function() {
        closeButton.style.display = 'none';
    };
    closeButton.onclick = function() {
        welcomeMessage.style.display = closeButton.style.display = 'none';
    };

    // Append elements to the container
    chatbotContainer.appendChild(welcomeMessage);
    chatbotContainer.appendChild(closeButton);
    chatbotContainer.appendChild(toggleButton);
    chatbotContainer.appendChild(chatbotIframe);

    // Append the container to the document body
    document.body.appendChild(chatbotContainer);
}

// Call the injectChatbot function when the DOM content is loaded
document.addEventListener('DOMContentLoaded', function() {
    injectChatbot();
});