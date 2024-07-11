document.addEventListener('DOMContentLoaded', (event) => {
    // Chatbot toggle functionality
    const chatbotButton = document.getElementById('b');
    const mainContent = document.querySelector('.main-content');
    let isChatbotOpen = false;

    function updateChatbotState(isOpen) {
        if (mainContent.classList.contains('shifted') === isOpen) return;
        isChatbotOpen = isOpen;
        mainContent.classList.toggle('shifted', isOpen);
        console.log('Chatbot is now:', isOpen ? 'open' : 'closed');
    }

    if (chatbotButton) {
        chatbotButton.addEventListener('click', function(event) {
            updateChatbotState(!isChatbotOpen);
        });
    } else {
        console.warn('Chatbot toggle button not found');
    }

    // Observer for chatbot state changes
    const observeTarget = document.body;
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const isChatbotVisible = document.body.classList.contains('cb-open');
                updateChatbotState(isChatbotVisible);
            }
        });
    });
    observer.observe(observeTarget, { attributes: true });

    // Auto-open chatbot functionality
    const disableAutoOpenCheckbox = document.getElementById('disable_auto_open');
    if (chatbotButton && (!disableAutoOpenCheckbox || !disableAutoOpenCheckbox.checked)) {
        setTimeout(() => {
            chatbotButton.click();
        }, 100);
    }

    // Tab switching functionality
    const tabLinks = document.querySelectorAll('.list-group-item');
    const tabContent = document.querySelectorAll('.tab-pane');

    function showTab(tabId) {
        tabContent.forEach(content => {
            content.style.display = 'none';
            content.classList.remove('show', 'active');
        });

        tabLinks.forEach(link => link.classList.remove('active'));

        const selectedTab = document.getElementById(tabId);
        const selectedLink = document.querySelector(`[data-target="${tabId}"]`);

        if (selectedTab && selectedLink) {
            selectedTab.style.display = 'block';
            selectedTab.classList.add('show', 'active');
            selectedLink.classList.add('active');
        }
    }

    tabLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const target = this.getAttribute('data-target');
            showTab(target);
        });
    });

    showTab('styling-section');

    //Form Validation
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('settingsForm');
        
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent the default form submission
    
            // Collect all the input values
            const botTemperature = document.getElementById('bot_temperature').value;
            const greetingMessage = document.getElementById('greeting_message').value;
            const chatbotTitle = document.getElementById('chatbot_title').value;
            const jobDescription = document.getElementById('job_description').value;
            const tone1 = document.getElementById('tone_1').value;
            const tone2 = document.getElementById('tone_2').value;
            const restrictions = document.getElementById('user_defined_restrictions').value;
            const uncertaintyResponse = document.getElementById('uncertainty_response').value;
            const supportEmail = document.getElementById('support_email').value;
            const supportPhone = document.getElementById('support_phone').value;
    
            // Validate inputs
            if (!botTemperature || !greetingMessage || !chatbotTitle || !jobDescription || !tone1 || !tone2 || !uncertaintyResponse) {
                alert('All required fields must be filled out.');
                return;
            }
    
            if (botTemperature < 0 || botTemperature > 1) {
                alert('Bot Temperature must be between 0 and 1.');
                return;
            }
    
            if (greetingMessage.length > 250) {
                alert('Greeting Message cannot be more than 250 characters.');
                return;
            }
    
            if (chatbotTitle.length > 20) {
                alert('Chatbot Title cannot be more than 20 characters.');
                return;
            }
    
            // Generate the custom prompt
            const customPrompt = `${jobDescription}
    
    Your role is to provide ${tone1} and ${tone2} customer support for our company. Your knowledge is confined to the context provided, and you should strive to deliver accurate information about our company based on this context. Be as detailed as possible without fabricating answers. Politely decline to respond to any inquiries that are not related to the provided documents or our company. Maintain your character at all times. Respond in the language used in the incoming message. Use simple formatting in your responses and speak as a member of our team, using "we" and "us" instead of "they". Include hyperlinks when necessary.
    
    RESTRICTIONS:
    - Avoid using the phrase "Based on the given information".
    - Do not invent answers.
    ${restrictions ? '- ' + restrictions.split('\n').join('\n- ') : ''}
    
    If you are uncertain about a response, say "${uncertaintyResponse}" and conclude your response there.
    
    For human assistance, direct users to contact our support team:
    Email: ${supportEmail}
    Phone: ${supportPhone}`;
    
            // Set the value of the hidden custom_prompt input
            document.getElementById('custom_prompt').value = customPrompt;
    
            // Now you can submit the form
            form.submit();
        });
    });

    // Bot temperature input handler
    document.getElementById('bot_temperature').addEventListener('input', function() {
        document.getElementById('bot_temperature_value').textContent = this.value;
    });

    // FAQ question management
    // Adding new questions
    document.getElementById('add-premade-question').addEventListener('click', function() {
        var container = document.getElementById('premade-questions-container');
        var index = container.getElementsByClassName('premade-question').length + 1;
        var question = document.createElement('div');
        question.className = 'premade-question';
        question.innerHTML = `
            <label for="premade_question_${index}">Question:</label>
            <textarea id="premade_question_${index}" name="premade_questions[]" required></textarea>
            <label for="premade_response_${index}">Response:</label>
            <textarea id="premade_response_${index}" name="premade_responses[]" required></textarea>
            <button type="button" class="delete-premade-question">
                <i class="fas fa-trash"></i>
            </button>
        `;
        question.dataset.saved = 'false';
        container.appendChild(question);
    });

    // Deleting questions
    document.getElementById('premade-questions-container').addEventListener('click', function(event) {
        const deleteButton = event.target.closest('.delete-premade-question');
        if (!deleteButton) return; // If the click wasn't on a delete button, do nothing
    
        const questionDiv = deleteButton.closest('.premade-question');
        if (!questionDiv) return; // If we couldn't find the parent question div, do nothing
    
        if (questionDiv.dataset.saved === 'true') {
            const questionId = questionDiv.id.split('_')[1];
            fetch('/delete_question', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question_id: questionId }),
            })
            .then(response => {
                if (response.ok) {
                    questionDiv.remove();
                } else {
                    console.error('Failed to delete question:', response.statusText);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        } else {
            questionDiv.remove();
        }
    });

    // Widget icon selection
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

    // Font style selection and preview
    function formatFont(font) {
        if (!font.id) { return font.text; }
        return $('<span>').css({'font-family': font.text, 'font-size': '16px'}).text(font.text);
    }

    $('#font_style').select2({
        templateResult: formatFont,
        templateSelection: formatFont,
        minimumResultsForSearch: Infinity,
        dropdownCssClass: "font-select-dropdown"
    });

    function updateFontPreview(fontFamily) {
        $('#font-preview').css('font-family', fontFamily);
    }

    $('#font_style').on('change', function() {
        updateFontPreview($(this).val());
    });

    updateFontPreview($('#font_style').val());

    // Icon selection
    function formatIcon(icon) {
        if (!icon.id) { return icon.text; }
        var $icon = $(
            '<span><img src="' + $(icon.element).data('icon') + '" class="img-flag" style="width: 30px; height: 30px;" /> ' + icon.text + '</span>'
        );
        return $icon;
    }

    $('#icon-select').select2({
        templateResult: formatIcon,
        templateSelection: formatIcon,
        minimumResultsForSearch: Infinity,
        dropdownCssClass: "icon-select-dropdown"
    });

    $('#icon-select').on('change', function() {
        var selectedOption = $(this).find('option:selected');
        var icon = selectedOption.data('icon');
        console.log('icon:', icon);
        $('#selected-icon').attr('src', icon);
    });

    // Logo file selection
    document.getElementById('logo').addEventListener('change', function() {
        var fileName = this.files[0].name;
        document.getElementById('file-name').textContent = fileName;
    });

    // Auto-open disable checkbox handler
    if (disableAutoOpenCheckbox) {
        disableAutoOpenCheckbox.addEventListener('change', function() {
            console.log('Disable Auto-open:', this.checked);
        });
    }

    // Make switch containers clickable
    document.addEventListener('DOMContentLoaded', (event) => {
        const switches = document.querySelectorAll('.switch');
        switches.forEach(switchEl => {
            const checkbox = switchEl.querySelector('input[type="checkbox"]');
            switchEl.addEventListener('click', (event) => {
                if (event.target !== checkbox) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
        });
    });
});
