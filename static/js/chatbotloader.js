function createChatbotWidget() {
    var widgetHTML = `<head>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <meta charset="UTF-8">
    <title>Chatbot Widget</title>
    <link rel="stylesheet" type="text/css" href="https://hr-bot-beast-aa887886e420.herokuapp.com/static/css/index.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <meta charset="UTF-8">
    <title>Chatbot</title>
</head>
<body>
    <div class="widget">
        <div class="widget-button" id="widget-button"></div>
        <div class="chatbot" id="chatbot">
            <div class="chatbox">
                <div class="chatbox-header">
                    <span class="chatbox-title">
                        <div class="chatbox-icon">
                            <img src="https://hr-bot-beast-aa887886e420.herokuapp.com/static/images/Indiana_University_seal.png" alt="HR Assistant" width="150" height="150">
                        </div>
                        <div class="chatbox-top">HR Assistant</div> 
                    </span>
                    <div class="chatbox-close">
                        <div id="refresh">
                            <img src="https://hr-bot-beast-aa887886e420.herokuapp.com/static/images/refresh.png" alt="Refresh" width="20" height="20">
                        </div>
                    </div>
                    <div class="chatbox-close" id="chatbox-close">X</div>
                </div>
                <div class="chatbox-body">
                    <!-- Chat messages go here -->
                </div>
                <div class="chatbox-input">
                    <div class="input-wrapper">
                        <input type="text" id="user-input" placeholder="Ask a question...">
                        <button id="send-button">Send</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://hr-bot-beast-aa887886e420.herokuapp.com/static/js/index.js"></script>
</body>`;  // Your chatbot HTML goes here
    document.body.insertAdjacentHTML('beforeend', widgetHTML);
}

// function loadChatbotCSS() {
//     var link = document.createElement('link');
//     link.href = 'https://hr-bot-beast-aa887886e420.herokuapp.com/static/css/index.css';  // URL of your CSS file
//     link.rel = 'stylesheet';
//     document.head.appendChild(link);
// }

