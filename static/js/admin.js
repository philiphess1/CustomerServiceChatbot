let fileArray = []; // this will hold the selected files

document.getElementById("upload-form").addEventListener("submit", function(event) {
    event.preventDefault();
    uploadFiles();
});

document.getElementById('upload-area').addEventListener('click', function(e) {
    if (e.target.id !== 'file') {
        document.getElementById('file').click();
    }
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
    
    let totalSize = 0; // Initialize total size

    // Update displayed file list
    for (let i = 0; i < fileArray.length; i++) {
        const fileSize = (fileArray[i].size / 1024 / 1024).toFixed(2); // Convert to MB and round to 2 decimal places
        totalSize += parseFloat(fileSize); // Add file size to total size

        const fileItem = document.createElement("div");
        fileItem.innerText = fileArray[i].name + ' - ' + fileSize + ' MB';
        fileItem.id = 'file-' + i; // Set a unique id for the file item
        fileItem.addEventListener('dragstart', function(event) {
            event.dataTransfer.setData('text', this.id); // Set the id of the dragged file
        });

        const removeBtn = document.createElement("img");
        removeBtn.src = "static/images/X-icon.png";
        removeBtn.alt = "Remove";
        removeBtn.classList.add('remove-button');
        removeBtn.addEventListener("click", function() {
            totalSize -= parseFloat(fileSize); // Subtract file size from total size
            fileArray.splice(i, 1);
            updateFileListDisplay();
            // update the file count display
            document.getElementById('file-label').innerHTML = fileArray.length + ' file(s) selected, total size: ' + totalSize.toFixed(2) + ' MB';
        });

        fileItem.appendChild(removeBtn);
        fileList.appendChild(fileItem);
    }
    if (fileArray.length === 0) {
        document.getElementById('uploading').style.display = 'none';
    }
    
}

document.getElementById('file').addEventListener('change', function() {
    if (this.files.length > 0) {
        document.getElementById('uploading').style.display = 'block';
    } else {
        document.getElementById('uploading').style.display = 'none';
    }
});

// After files are processed and removed from fileArray

let uploadArea = document.getElementById('upload-area');

uploadArea.addEventListener('dragenter', function() {
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', function() {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('dragover', function(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
});

uploadArea.addEventListener('drop', function(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
    let files = event.dataTransfer.files;
    for (let i = 0; i < files.length; i++) {
        fileArray.push(files[i]);
    }
    document.getElementById("file").files = files;
    updateFileListDisplay();
    updateFileSizeAndCount();
});


function updateFileSizeAndCount() {
    var fileInput = document.getElementById('file');
    var totalSize = 0;
    for (var i = 0; i < fileInput.files.length; i++) {
        totalSize += fileInput.files[i].size;
    }
    // Convert the total size to megabytes
    totalSize = totalSize / 1024 / 1024;

    document.getElementById('file-label').innerHTML = fileInput.files.length + ' file(s) selected, total size: ' + totalSize.toFixed(2) + ' MB';

    if (totalSize > 10) {
        alert('The total size of all files must be less than 10 MB.');
        fileInput.value = '';
    }
}