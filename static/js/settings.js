document.addEventListener('DOMContentLoaded', (event) => {
    // Chatbot toggle functionality
    const mainContent = document.querySelector('.main-content');
    let isChatbotOpen = false;

    function updateChatbotState(isOpen) {
        if (mainContent.classList.contains('shifted') === isOpen) return;
        mainContent.classList.toggle('shifted', isOpen);
        console.log('Chatbot is now:', isOpen ? 'open' : 'closed');
    }

    // Assuming the iframe has an ID of 'e'
    const iframe = document.getElementById('e');
    if (iframe) {
        // Observer for iframe visibility changes
        const styleObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    // Check if the iframe is visible
                    const isVisible = iframe.style.display !== 'none' && iframe.style.opacity !== '0';
                    updateChatbotState(isVisible);
                }
            });
        });
        styleObserver.observe(iframe, { attributes: true, attributeFilter: ['style'] });
    } else {
        console.warn('Chatbot iframe not found');
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

    const phoneInput = document.getElementById('support_phone');
    phoneInput.addEventListener('input', function (e) {
        let x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
        e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
    });

    // Handle exclude sources checkbox
    const excludeSourcesCheckbox = document.getElementById('exclude_sources');
    if (excludeSourcesCheckbox) {
        excludeSourcesCheckbox.addEventListener('change', function() {
            console.log('Exclude Sources:', this.checked);
        });
    }

    // Form validation and custom prompt generation
    document.getElementById('settingsForm').addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent default submission

        const requiredFields = [
            { id: 'bot_temperature', name: 'Bot Temperature' },
            { id: 'greeting_message', name: 'Greeting Message' },
            { id: 'chatbot_title', name: 'Chatbot Title' },
            { id: 'job_description', name: 'Job Description' },
            { id: 'tone_1', name: 'Tone 1' },
            { id: 'tone_2', name: 'Tone 2' },
            { id: 'user_defined_restrictions', name: 'Additional Restrictions' },
            { id: 'uncertainty_response', name: 'Uncertainty Response' }
        ];

        const noSupportEmail = document.getElementById('no_support_email').checked;
        const noSupportPhone = document.getElementById('no_support_phone').checked;

        if (!noSupportEmail) {
            requiredFields.push({ id: 'support_email', name: 'Support Email' });
        }
        if (!noSupportPhone) {
            requiredFields.push({ id: 'support_phone', name: 'Support Phone' });
        }

        const missingFields = requiredFields.filter(field => {
            const element = document.getElementById(field.id);
            return !element || element.value.trim() === '';
        });

        if (missingFields.length > 0) {
            const missingFieldNames = missingFields.map(field => field.name).join(', ');
            alert(`The following fields are missing: ${missingFieldNames}`);
            return;
        }

        const botTemperature = parseFloat(document.getElementById('bot_temperature').value);
        if (isNaN(botTemperature) || botTemperature < 0 || botTemperature > 1) {
            alert('Bot Temperature must be between 0 and 1.');
            return;
        }

        const greetingMessage = document.getElementById('greeting_message').value;
        if (greetingMessage.length > 250) {
            alert('Greeting Message cannot be more than 250 characters.');
            return;
        }

        const chatbotTitle = document.getElementById('chatbot_title').value;
        if (chatbotTitle.length > 20) {
            alert('Chatbot Title cannot be more than 20 characters.');
            return;
        }

        // Generate custom prompt
        const jobDescription = document.getElementById('job_description').value;
        const tone1 = document.getElementById('tone_1').value;
        const tone2 = document.getElementById('tone_2').value;
        const restrictions = document.getElementById('user_defined_restrictions').value;
        const uncertaintyResponse = document.getElementById('uncertainty_response').value;
        const supportEmail = document.getElementById('support_email').value;
        const supportPhone = document.getElementById('support_phone').value;
        const excludeSources = document.getElementById('exclude_sources').checked;

        let humanAssistanceInfo = '';
        if (!noSupportEmail && !noSupportPhone) {
            humanAssistanceInfo = `For human assistance, direct users to contact our support team:
Email: ${supportEmail}
Phone: ${supportPhone}`;
        } else if (!noSupportEmail) {
            humanAssistanceInfo = `For human assistance, direct users to contact our support team:
Email: ${supportEmail}`;
        } else if (!noSupportPhone) {
            humanAssistanceInfo = `For human assistance, direct users to contact our support team:
Phone: ${supportPhone}`;
        } else {
            humanAssistanceInfo = 'For human assistance, direct users to check out our company website for contact information.';
        }

        const customPrompt = `${jobDescription}

Your role is to provide ${tone1} and ${tone2} customer support for our company. Your knowledge is confined to the context provided, and you should strive to deliver accurate information about our company based on this context. Be as detailed as possible without fabricating answers. Politely decline to respond to any inquiries that are not related to the provided documents or our company. Maintain your character at all times. Respond in the language used in the incoming message. Use simple formatting in your responses and speak as a member of our team, using "we" and "us" instead of "they". Include hyperlinks when necessary.

RESTRICTIONS:
- Avoid using the phrase "Based on the given information".
- Do not invent answers.
- If the question is a short phrase such as "Hello", "What's up", etc., respond with a greeting.
${restrictions ? '- ' + restrictions.split('\n').join('\n- ') : ''}

If you are uncertain about a response, say "${uncertaintyResponse}" and conclude your response there.

${humanAssistanceInfo}`;

        document.getElementById('custom_prompt').value = customPrompt;

        // Include the exclude sources setting
        document.getElementById('exclude_sources_hidden').value = excludeSources;

        // Submit the form
        this.submit();
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