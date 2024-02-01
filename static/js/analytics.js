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

// Define the chart
var ctx = document.getElementById('myChart').getContext('2d');
var myChart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: ['Likes', 'Dislikes', 'None'],
        datasets: [{
            data: [0, 0, 0], // Initialize with 0, will be updated with fetched data
            backgroundColor: [
                'rgba(75, 192, 192, 0.2)',
                'rgba(255, 99, 132, 0.2)',
                'rgba(128, 128, 128, 0.2)' // Add a color for 'None' feedback
            ],
            borderColor: [
                'rgba(75, 192, 192, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(128, 128, 128, 1)' // Add a color for 'None' feedback
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
    }
});

// Initialize the likes, dislikes, and none counts
var likesCount = 0;
var dislikesCount = 0;
var noneCount = 0;

// Function to calculate the initial likes, dislikes, and none counts
function calculateInitialCounts() {
    var questions = document.querySelectorAll('.question-row');

    questions.forEach(function(question) {
        var feedbackType = question.classList.contains('like') ? 'Like' : (question.classList.contains('dislike') ? 'Dislike' : 'None');

        // Update likes, dislikes, and none counts based on feedback type
        if (feedbackType === 'Like') {
            likesCount++;
        } else if (feedbackType === 'Dislike') {
            dislikesCount++;
        } else if (feedbackType === 'None') {
            noneCount++;
        }
    });
}
// Function to update the chart data
function updateChartData() {
    // Update the dataset with new data
    myChart.data.datasets[0].data = [likesCount, dislikesCount, noneCount];

    // Update the chart
    myChart.update();
}

// Function to handle topic selection
function sendTopic(topic) {
    var questions = document.querySelectorAll('.question-row');
    
    // Reset likes, dislikes, and none counts when a new topic is selected
    likesCount = 0;
    dislikesCount = 0;
    noneCount = 0;

    questions.forEach(function(question) {
        var userQuestion = question.querySelector('.user-question').innerText;
        var feedbackType = question.classList.contains('like') ? 'Like' : (question.classList.contains('dislike') ? 'Dislike' : 'None');
        
        // Check if the topic is present in the user's question
        if (userQuestion.includes(topic)) {
            question.style.display = '';  // Show the question

            // Update likes, dislikes, and none counts based on feedback type
            if (feedbackType === 'Like') {
                likesCount++;
            } else if (feedbackType === 'Dislike') {
                dislikesCount++;
            } else if (feedbackType === 'None') {
                noneCount++;
            }
        } else {
            question.style.display = 'none';  // Hide the question
        }
    });

    // Update the chart with the new likes, dislikes, and none counts
    updateChartData();
}

// Calculate the initial likes and dislikes counts when the page loads
calculateInitialCounts();

// Update the chart with the initial likes and dislikes counts when the page loads
updateChartData();

// Function to reset the list
function resetList() {
    var questions = document.querySelectorAll('.question-row');

    questions.forEach(function(question) {
        question.style.display = '';  // Show the question
    });

    likesCount = 0;
    dislikesCount = 0;

    // Calculate the initial likes and dislikes counts
    calculateInitialCounts();

    // Update the chart with the initial likes and dislikes counts
    updateChartData();
}
