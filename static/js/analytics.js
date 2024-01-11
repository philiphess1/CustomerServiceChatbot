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

var ctx = document.getElementById('myChart').getContext('2d');
var myChart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: ['Likes', 'Dislikes'],
        datasets: [{
            data: [0, 0], // Initialize with 0, will be updated with fetched data
            backgroundColor: [
                'rgba(75, 192, 192, 0.2)',
                'rgba(255, 99, 132, 0.2)'
            ],
            borderColor: [
                'rgba(75, 192, 192, 1)',
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});

fetch('/analytics/data')
    .then(response => response.json())
    .then(data => {
        // Update the chart data
        myChart.data.datasets[0].data = [data.likes, data.dislikes];

        // Update the chart
        myChart.update();
    });
    
    function filterByTopic(topic) {
        // Send an AJAX request to fetch filtered data
        $.ajax({
            type: 'POST',
            url: '/filter_data',  // Update the endpoint to match your server route
            data: { topic: topic },
            success: function(filteredData) {
                // Clear current table rows
                $('table tr:not(:first)').remove();
    
                // Add new rows based on filtered data
                filteredData.forEach(function (item) {
                    $('table').append(`
                        <tr class="${item.feedback_type === 'Like' ? 'like' : (item.feedback_type === 'Dislike' ? 'dislike' : 'none')}">
                            <td>${item.user_question}</td>
                            <td>${item.bot_response}</td>
                            <td>${item.feedback_type}</td>
                            <td>
                                <!-- Add form for delete action -->
                            </td>
                        </tr>
                    `);
                });
            },
            error: function(error) {
                console.error('Error fetching filtered data:', error);
            }
        });
    }
    