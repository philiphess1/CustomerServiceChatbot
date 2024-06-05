function copyCode(element) {
    var textToCopy = element.previousElementSibling.textContent; // Get the text from the preceding pre tag
    navigator.clipboard.writeText(textToCopy).then(function() {
        var tooltip = element.nextElementSibling;
        tooltip.textContent = "Copied!";
        tooltip.style.display = "block";
        tooltip.style.backgroundColor = "#88bf46";
        tooltip.style.color = "white";
        setTimeout(function() {
            tooltip.style.display = "none";
            tooltip.textContent = "Copy to Clipboard";
            tooltip.style.backgroundColor = "";
            tooltip.style.color = "";
        }, 2000); // Hide the tooltip after 2 seconds
    }, function(err) {
        console.error('Could not copy text: ', err);
    });
}

function copyIframeCode(element) {
    var textToCopy = element.previousElementSibling.textContent; // Get the text from the preceding pre tag
    navigator.clipboard.writeText(textToCopy).then(function() {
        var tooltip = element.nextElementSibling;
        tooltip.textContent = "Copied!";
        tooltip.style.display = "block";
        tooltip.style.backgroundColor = "#88bf46";
        tooltip.style.color = "white";
        setTimeout(function() {
            tooltip.style.display = "none";
            tooltip.textContent = "Copy to Clipboard";
            tooltip.style.backgroundColor = "";
            tooltip.style.color = "";
        }, 2000); // Hide the tooltip after 2 seconds
    }, function(err) {
        console.error('Could not copy text: ', err);
    });
}
function showTooltip(element) {
    var tooltip = element.nextElementSibling;
    tooltip.style.display = "block";
}

function hideTooltip(element) {
    var tooltip = element.nextElementSibling;
    tooltip.style.display = "none";
}