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

    // Form validation
    document.getElementById('settingsForm').addEventListener('submit', function(event) {
        var botTemperature = document.getElementById('bot_temperature').value;
        var customPrompt = document.getElementById('custom_prompt').value;
        var greetingMessage = document.getElementById('greeting_message').value;
        var chatbotTitle = document.getElementById('chatbot_title').value;

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

        // TODO: Add code here to collect and format FAQ questions for submission
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
        var target = event.target;
        if (target.tagName !== 'BUTTON') {
            target = target.parentNode;
        }
        if (target.className === 'delete-premade-question') {
            if (target.parentNode.dataset.saved === 'true') {
                var xhr = new XMLHttpRequest();
                xhr.open('DELETE', '/delete_question', true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.send(JSON.stringify({
                    question_id: target.parentNode.id.split('_')[1]
                }));

                xhr.onload = function() {
                    if (xhr.status == 200) {
                        target.parentNode.remove();
                    } else {
                        console.error('Failed to delete question:', xhr.responseText);
                    }
                };
            } else {
                target.parentNode.remove();
            }
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
    const customSwitches = document.querySelectorAll('.custom-switch');
    customSwitches.forEach(switchEl => {
        switchEl.addEventListener('click', function(event) {
            if (event.target !== this.querySelector('input[type="checkbox"]')) {
                const checkbox = this.querySelector('input[type="checkbox"]');
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            }
        });
    });
});
