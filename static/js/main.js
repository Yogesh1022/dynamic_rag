
document.getElementById("upload-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("file-input");
    if (!fileInput.files.length) {
        document.getElementById("upload-status").textContent = "Please select a file.";
        console.warn("No file selected");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    document.getElementById("upload-status").textContent = "Uploading and processing...";
    console.log("Sending upload request for file:", fileInput.files[0].name);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData,
        });
        console.log("Upload response status:", response.status);
        const data = await response.json();
        console.log("Upload response data:", data);
        document.getElementById("upload-status").textContent = response.ok
            ? data.message
            : `Error: ${data.detail || "Upload failed."} (Status: ${response.status})`;
    } catch (err) {
        console.error("Upload request failed:", err);
        document.getElementById("upload-status").textContent = `Error: Request failed - ${err.message}`;
    }
});

document.getElementById("query-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = document.getElementById("question").value.trim();
    if (!question) {
        document.getElementById("answer").textContent = "Please enter a question.";
        console.warn("No question entered");
        return;
    }

    document.getElementById("answer").textContent = "Generating answer...";
    console.log("Sending query request:", question);

    try {
        const response = await fetch("/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });
        console.log("Query response status:", response.status);
        const data = await response.json();
        console.log("Query response data:", data);
        document.getElementById("answer").innerHTML = response.ok
            ? `<strong>Answer:</strong><br>${data.answer.replace(/\n/g, '<br>')}`
            : `Error: ${data.detail || "Query failed."} (Status: ${response.status})`;
    } catch (err) {
        console.error("Query request failed:", err);
        document.getElementById("answer").textContent = `Error: Request failed - ${err.message}`;
    }
});
