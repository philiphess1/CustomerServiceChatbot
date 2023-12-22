document.addEventListener('DOMContentLoaded', (event) => {
    // Simulate a click on the chatbot button to open it when the page loads
    document.getElementById('chatbot-button').click();
});

// sidebar JS
/* Set the width of the sidebar to 250px (show it) */
function openNav() {
    document.getElementById("mySidepanel").style.width = "250px";
  }
  
  /* Set the width of the sidebar to 0 (hide it) */
  function closeNav() {
    document.getElementById("mySidepanel").style.width = "0";
  }

//   search bar JS
// Get current page URL
var url = window.location.pathname;

// Get the last part of the URL (after the last '/')
var page = url.substring(url.lastIndexOf('/') + 1);

// Remove the '.html' extension if it exists
if (page.endsWith('.html')) {
    page = page.substring(0, page.length - 5);
}

// Get all links
var links = document.getElementsByClassName('mgn');

// Get all buttons
var btns = document.getElementsByClassName('btns');

// Loop through all links
for (var i = 0; i < links.length; i++) {
    // Get the id of the link
    var id = links[i].id;

    // If the id is the same as the page
    if (id === page) {
        // Change the background color of the link
        links[i].style.color = 'white';
    }
}

// Get all buttons
var btns = document.getElementsByClassName('btns');

// Loop through all buttons
for (var i = 0; i < btns.length; i++) {
    // Get the id of the button
    var id = btns[i].id;

    // If the id is the same as the page
    if (id === page) {
        // Change the background color of the button
        btns[i].style.backgroundColor = '#444';
    }
}

window.onload = function() {
    var labels = document.querySelectorAll('#widget_icon label');
    labels.forEach(function(label) {
        var radio = label.querySelector('input');
        if (radio.checked) {
            label.classList.add('selected');
        }
        radio.addEventListener('change', function() {
            labels.forEach(function(label) {
                label.classList.remove('selected');
            });
            if (this.checked) {
                this.parentElement.classList.add('selected');
            }
        });
    });
};

document.getElementById('settingsForm').addEventListener('submit', function(event) {
    var botTemperature = document.getElementById('bot_temperature').value;
    var customPrompt = document.getElementById('custom_prompt').value;
    var greetingMessage = document.getElementById('greeting_message').value;

    if (botTemperature < 0 || botTemperature > 1) {
        alert('Bot Temperature must be between 0 and 1.');
        event.preventDefault();
    }

    if (customPrompt.length > 1000) {
        alert('Custom Prompt cannot be more than 1000 characters.');
        event.preventDefault();
    }

    if (greetingMessage.length > 250) {
        alert('Greeting Message cannot be more than 250 characters.');
        event.preventDefault();
    }
});

