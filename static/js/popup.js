    // chatbot.js

    // Function to inject the chatbot GUI into the website
    function injectChatbot() {{
        console.log('injectChatbot function called');
        var chatbotContainer = document.createElement('div');
        chatbotContainer.id = 'chatbotContainer';
        chatbotContainer.style.position = 'fixed';
        chatbotContainer.style.bottom = '20px';
        chatbotContainer.style.right = '20px';
        chatbotContainer.style.zIndex = '9999';
        chatbotContainer.style.backgroundColor = '#ffffff';
        chatbotContainer.style.border = '1px solid #ccc';
        chatbotContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
        
        var chatbotIframe = document.createElement('iframe');
        chatbotIframe.src = 'http://127.0.0.1:5000/{user_id}/{chatbot_id}';
        chatbotIframe.width = '360.5';
        chatbotIframe.height = '600';
        chatbotIframe.style.border = 'none';
        chatbotIframe.id = 'e';
        chatbotIframe.style.display = 'None';
        chatbotIframe.style.position = 'fixed';
        chatbotIframe.style.bottom = '100px';
        chatbotIframe.style.right = '0';
        chatbotIframe.style.zIndex = '9999';
        chatbotIframe.style.overflow = 'hidden';
        
        var toggleButton = document.createElement('img');
        toggleButton.id = 'b';
        toggleButton.src = 'https://app.eccoai.org//static/images/{settings["widget_icon"]}';
        toggleButton.alt = 'Chat';
        toggleButton.style.width = '80px';
        toggleButton.style.height = '80px';
        toggleButton.style.position = 'fixed';
        toggleButton.style.bottom = '10px';
        toggleButton.style.right = '10px';
        toggleButton.style.zIndex = '1000';
        toggleButton.style.cursor = 'pointer';
        toggleButton.style.transition = 'transform 0.3s ease-in-out';

        var welcomeMessage = document.createElement('div');
        welcomeMessage.id = 'p';
        welcomeMessage.textContent = '{settings["popup_message"]}';
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
        closeButton.textContent = 'X';

        chatbotContainer.appendChild(welcomeMessage);
        chatbotContainer.appendChild(closeButton);
        chatbotContainer.appendChild(toggleButton);
        chatbotContainer.appendChild(chatbotIframe);
        document.body.appendChild(chatbotContainer);

        var p=document.getElementById('p'),c=document.getElementById('c'),b=document.getElementById('b');
        p.onmouseover=c.onmouseover=function(){{c.style.display='block'}};
        p.onmouseout=function(){{c.style.display='none'}};
        c.onclick=function(){{p.style.display=c.style.display='none'}};
        b.addEventListener('mouseover', function() {{
            this.style.transform = 'scale(1.1)';
        }});
        b.addEventListener('mouseout', function() {{
            this.style.transform = 'scale(1)';
        }});
        b.addEventListener('click', function() {{
            var iframe = document.getElementById('e');
            if (iframe.style.display === 'none') {{
                iframe.style.display = 'block';
                p.style.display = 'none'; // hide the 'p' element
            }} else {{
                iframe.style.display = 'none';
            }}
        }});
        function closeChatbot() {{
            var iframe = document.getElementById('e');
            iframe.style.display = 'none';
        }}
    }}
    document.addEventListener('DOMContentLoaded', function() {{
        console.log('DOMContentLoaded event fired');
        injectChatbot();
    }});