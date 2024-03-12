document.addEventListener('DOMContentLoaded', (event) => {
    // Simulate a click on the chatbot button to open it when the page loads
    document.getElementById('b').click();
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

window.addEventListener('DOMContentLoaded', (event) => {
    var primaryInput = document.getElementById('primary');
    var secondaryInput = document.getElementById('secondary');

    primaryInput.addEventListener('input', function() {
        var primaries = document.querySelectorAll('.primary');
        primaries.forEach(function(primary) {
            primary.style.fill = this.value;
        }, this);
    });

    secondaryInput.addEventListener('input', function() {
        var secondaries = document.querySelectorAll('.secondary');
        secondaries.forEach(function(secondary) {
            secondary.style.fill = this.value;
        }, this);
    });

    // Trigger the input event manually
    primaryInput.dispatchEvent(new Event('input'));
    secondaryInput.dispatchEvent(new Event('input'));

    // Change display property
    var elementToDisplay = document.getElementById('svg_icon'); // replace 'elementId' with the id of your element
    elementToDisplay.style.display = 'block'; // or 'inline', 'flex', etc. depending on your needs
});

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
    var chatbotTitle = document.getElementById('chatbot_title').value;

    // Add this block
    if (!botTemperature || !customPrompt || !greetingMessage || !chatbotTitle) {
        alert('All fields must be filled out.');
        event.preventDefault();
    }

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

    if (chatbotTitle.length > 20) {
        alert('Chatbot Title cannot be more than 20 characters.');
        event.preventDefault();
    }
});

document.getElementById('bot_temperature').addEventListener('input', function() {
    document.getElementById('bot_temperature_value').textContent = this.value;
});

function showPage(pageId) {
    // Hide all subpages
    var subpages = document.getElementsByClassName('subpage');
    for (var i = 0; i < subpages.length; i++) {
        subpages[i].style.display = 'none';
    }

    // Show the selected subpage
    document.getElementById(pageId).style.display = 'block';

    // Remove the 'selected' class from all buttons
    var buttons = document.getElementsByClassName('button-35');
    for (var i = 0; i < buttons.length; i++) {
        buttons[i].classList.remove('selected');
    }

    // Add the 'selected' class to the clicked button
    if (pageId === 'styling-settings') {
        document.querySelector('button[onclick="showPage(\'styling-settings\')"]').classList.add('selected');
    } else if (pageId === 'system-settings') {
        document.querySelector('button[onclick="showPage(\'system-settings\')"]').classList.add('selected');
    } else if (pageId === 'faq-settings') {
        document.querySelector('button[onclick="showPage(\'faq-settings\')"]').classList.add('selected');
    }
}
document.getElementById('add-premade-question').addEventListener('click', function() {
    var container = document.getElementById('premade-questions-container');
    var index = container.getElementsByClassName('premade-question').length + 1;
    var question = document.createElement('div');
    question.className = 'premade-question';
    question.innerHTML = `
        <label for="premade_question_${index}">Question:</label>
        <input type="text" id="premade_question_${index}" name="premade_questions[]" required>
        <label for="premade_response_${index}">Response:</label>
        <input type="text" id="premade_response_${index}" name="premade_responses[]" required>
        <button type="button" class="delete-premade-question">
            <i class="fas fa-trash"></i>
        </button>
    `;
    question.dataset.saved = 'false';
    container.appendChild(question);
});

document.getElementById('premade-questions-container').addEventListener('click', function(event) {
    var target = event.target;
    if (target.tagName !== 'BUTTON') {
        target = target.parentNode;
    }
    if (target.className === 'delete-premade-question') {
        if (target.parentNode.dataset.saved === 'true') {
            // If the question is saved in the database, send a delete request to the server
            var xhr = new XMLHttpRequest();
            xhr.open('DELETE', '/delete_question', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify({
                question_id: target.parentNode.id.split('_')[1] // Extract the question id from the id attribute
            }));

            xhr.onload = function() {
                if (xhr.status == 200) {
                    // If the server responded with a status of 200, remove the question from the DOM
                    target.parentNode.remove();
                } else {
                    // If the server responded with an error status, log the error message
                    console.error('Failed to delete question:', xhr.responseText);
                }
            };
        } else {
            // If the question is not saved in the database, just remove it from the DOM
            target.parentNode.remove();
        }
    }
});

$(document).ready(function() {
    $('#font_style').select2();
});

$(document).ready(function() {
    function formatIcon (icon) {
        var originalOption = icon.element;
        var img = $(originalOption).data('icon');
        if (!icon.id) { return icon.text; }
        var $icon = $(
            '<span><img src="' + img + '" class="img-flag" style="width: 30px; height: 30px;" /> ' + icon.text + '</span>'
        );
        return $icon;
    };

    $('#icon-select').select2({
        templateResult: formatIcon,
        placeholder: "Click to change"
    });

    // Add an event listener for the change event
    $('#icon-select').on('change', function() {
        // Get the selected option
        var selectedOption = $(this).find('option:selected');

        // Get the data-icon attribute of the selected option
        var icon = selectedOption.data('icon');

        // Log the icon variable
        console.log('icon:', icon);

        // Update the src attribute of the img element
        $('#selected-icon').attr('src', icon);
    });
});