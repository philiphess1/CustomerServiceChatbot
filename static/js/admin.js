let fileArray = []; // this will hold the selected files

document.getElementById("upload-form").addEventListener("submit", function(event) {
    event.preventDefault();
    uploadFiles();
});

function uploadFiles() {
    document.getElementById("form-content").style.display = "none";  // Hide form content
    document.getElementById("loading").style.display = "block";  // Show loading icon
    let formData = new FormData();

    for (let i = 0; i < fileArray.length; i++) {
        formData.append("file", fileArray[i]);
    }

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("loading").style.display = "none";  // Hide loading icon
        document.getElementById("form-content").style.display = "block";  // Show form content
        if (data.status === "success") {
            // Redirect to the admin page
            window.location.href = '/admin';  
        } else {
            // Handle errors or show an error message to the user
            console.error(data.message);
        }
    })
    .catch(error => {
        document.getElementById("loading").style.display = "none";  // Hide loading icon
        document.getElementById("form-content").style.display = "block";  // Show form content
        console.error('There was an error!', error);
    });
}

document.getElementById("file").addEventListener("change", function() {
    const fileList = document.getElementById("file-list");
    fileList.innerHTML = ""; // clear current file list
    
    // Add newly selected files to fileArray
    for (let i = 0; i < this.files.length; i++) {
        fileArray.push(this.files[i]);
    }

    updateFileListDisplay();
});

function updateFileListDisplay() {
    const fileList = document.getElementById("file-list");
    fileList.innerHTML = ""; // clear current file list
    
    // Update displayed file list
    for (let i = 0; i < fileArray.length; i++) {
        const fileItem = document.createElement("div");
        fileItem.innerText = fileArray[i].name;

        const removeBtn = document.createElement("button");
        removeBtn.innerText = "Remove";
        removeBtn.addEventListener("click", function() {
            fileArray.splice(i, 1);
            updateFileListDisplay();
            // update the file count display
            document.getElementById('file-label').innerHTML = fileArray.length + ' file(s) selected';
        });

        fileItem.appendChild(removeBtn);
        fileList.appendChild(fileItem);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
}

function handleDrop(event) {
    event.preventDefault();
    var files = event.dataTransfer.files;
    document.getElementById("file").files = files;
}

document.body.addEventListener("dragover", handleDragOver);
document.body.addEventListener("drop", handleDrop);