
const API_BASE = "/api/notebooks";

let activeNotebookId = null;
let activeNotebookName = null;
let statusPollingTimer = null;
let isAsking = false;

const elements = {
    notebookList: document.getElementById("notebook-list"),
    documentList: document.getElementById("document-list"),
    documentCount: document.getElementById("document-count"),
    activeNotebookName: document.getElementById("active-notebook-name"),
    chatSubtitle: document.getElementById("chat-subtitle"),
    chatContent: document.getElementById("chat-content"),
    welcomeScreen: document.getElementById("welcome-screen"),
    chatForm: document.getElementById("chat-form"),
    questionInput: document.getElementById("question-input"),
    sendButton: document.getElementById("send-question-btn"),
    addDocumentButton: document.getElementById("add-document-btn"),
    fileInput: document.getElementById("document-file-input"),
    createNotebookButton: document.getElementById("create-notebook-btn"),
    clearChatButton: document.getElementById("clear-chat-btn")
};


// --------------------------------------------------
// API helper
// --------------------------------------------------

async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("The server returned an invalid response.");
    }

    if (!response.ok) {
        throw new Error(data.error || data.message || "Request failed.");
    }

    return data;
}


// --------------------------------------------------
// Notifications
// --------------------------------------------------

function showError(message) {
    alert(message);
}


// --------------------------------------------------
// Notebook management
// --------------------------------------------------

async function loadNotebooks() {
    try {
        const data = await apiRequest(API_BASE);

        renderNotebooks(data.notebooks || []);

    } catch (error) {
        showError(`Could not load notebooks: ${error.message}`);
    }
}


function renderNotebooks(notebooks) {
    elements.notebookList.replaceChildren();

    if (notebooks.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "No notebooks yet. Create one to get started.";
        elements.notebookList.appendChild(empty);
        return;
    }

    notebooks.forEach(notebook => {
        const item = document.createElement("div");

        item.className = "notebook-item";
        item.textContent = notebook.name;
        item.dataset.id = notebook.id;

        if (notebook.id === activeNotebookId) {
            item.classList.add("active");
        }

        item.addEventListener("click", () => {
            selectNotebook(notebook.id, notebook.name);
        });

        elements.notebookList.appendChild(item);
    });
}


async function selectNotebook(notebookId, notebookName) {
    activeNotebookId = notebookId;
    activeNotebookName = notebookName;

    elements.activeNotebookName.textContent = notebookName;
    elements.chatSubtitle.textContent = "Ask questions about your sources";

    elements.questionInput.disabled = false;
    elements.sendButton.disabled = false;
    elements.addDocumentButton.disabled = false;

    // Clear previous conversation when switching notebooks.
    clearChat();

    await loadNotebooks();
    await loadDocuments(notebookId);

    startStatusPolling();
}



// --------------------------------------------------
// Create notebook modal
// --------------------------------------------------

const modal = document.getElementById("create-notebook-modal");

const notebookForm = document.getElementById("create-notebook-form");
const notebookNameInput = document.getElementById("notebook-name");

const modalFileInput = document.getElementById("modal-file-input");
const modalDocumentList = document.getElementById("modal-document-list");

const modalAddButton = document.getElementById("modal-add-documents-btn");
const modalCreateButton = document.getElementById("submit-notebook-btn");

const closeModalButton = document.getElementById("close-notebook-modal");
const cancelModalButton = document.getElementById("cancel-notebook-btn");

let selectedNotebookFiles = [];


function openNotebookModal() {
    selectedNotebookFiles = [];
    notebookForm.reset();
    renderModalFiles();

    modal.showModal();
    notebookNameInput.focus();
}


function closeNotebookModal() {
    modal.close();
    selectedNotebookFiles = [];
    notebookForm.reset();
    renderModalFiles();
}

function renderMarkdown(content) {
    const html = marked.parse(content);

    return DOMPurify.sanitize(html);
}


elements.createNotebookButton.addEventListener(
    "click",
    openNotebookModal
);

closeModalButton.addEventListener(
    "click",
    closeNotebookModal
);

cancelModalButton.addEventListener(
    "click",
    closeNotebookModal
);


// Close when clicking outside the modal content.
modal.addEventListener("click", event => {
    if (event.target === modal) {
        closeNotebookModal();
    }
});


// Open file selector.
modalAddButton.addEventListener("click", () => {
    modalFileInput.click();
});


// Add selected files to the list.
modalFileInput.addEventListener("change", () => {
    const newFiles = Array.from(modalFileInput.files || []);

    for (const file of newFiles) {
        const alreadyExists = selectedNotebookFiles.some(
            existing =>
                existing.name === file.name &&
                existing.size === file.size &&
                existing.lastModified === file.lastModified
        );

        if (!alreadyExists) {
            selectedNotebookFiles.push(file);
        }
    }

    renderModalFiles();

    // Allows selecting the same file again after removing it.
    modalFileInput.value = "";
});


// Render selected documents.
function renderModalFiles() {
    modalDocumentList.replaceChildren();

    if (selectedNotebookFiles.length === 0) {
        const empty = document.createElement("div");
        empty.className = "modal-empty-state";
        empty.textContent = "No documents added yet.";

        modalDocumentList.appendChild(empty);
        return;
    }

    selectedNotebookFiles.forEach((file, index) => {
        const item = document.createElement("div");
        item.className = "modal-file-item";

        const extension = file.name.split(".").pop().toUpperCase();

        const icon = document.createElement("div");
        icon.className = "modal-file-icon";
        icon.textContent = extension;

        const name = document.createElement("div");
        name.className = "modal-file-name";
        name.textContent = file.name;
        name.title = file.name;

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.className = "modal-remove-btn";
        removeButton.textContent = "Remove";
        removeButton.title = "Remove document";

        removeButton.addEventListener("click", () => {
            selectedNotebookFiles.splice(index, 1);
            renderModalFiles();
        });

        item.append(icon, name, removeButton);
        modalDocumentList.appendChild(item);
    });
}


// Submit notebook creation.
notebookForm.addEventListener("submit", async event => {
    event.preventDefault();

    const notebookName = notebookNameInput.value.trim();

    if (!notebookName) {
        showError("Enter a notebook name.");
        notebookNameInput.focus();
        return;
    }

    if (selectedNotebookFiles.length === 0) {
        showError("Add at least one document.");
        return;
    }

    const formData = new FormData();

    formData.append("name", notebookName);

    selectedNotebookFiles.forEach(file => {
        formData.append("files", file);
    });

    modalCreateButton.disabled = true;
    modalAddButton.disabled = true;
    cancelModalButton.disabled = true;
    closeModalButton.disabled = true;

    modalCreateButton.textContent = "Creating...";

    try {
        const data = await apiRequest(API_BASE, {
            method: "POST",
            body: formData
        });

        modal.close();

        selectedNotebookFiles = [];
        notebookForm.reset();
        renderModalFiles();

        await loadNotebooks();

        if (data.notebook) {
            await selectNotebook(
                data.notebook.id,
                data.notebook.name
            );
        }

    } catch (error) {
        showError(`Could not create notebook: ${error.message}`);

    } finally {
        modalCreateButton.disabled = false;
        modalAddButton.disabled = false;
        cancelModalButton.disabled = false;
        closeModalButton.disabled = false;

        modalCreateButton.textContent = "Create notebook";
    }
});

// --------------------------------------------------
// Document management
// --------------------------------------------------

async function loadDocuments(notebookId) {
    try {
        const data = await apiRequest(
            `${API_BASE}/${notebookId}/documents`
        );

        renderDocuments(data.documents || []);

        elements.documentCount.textContent =
            `${data.total_documents || 0} documents`;

    } catch (error) {
        showError(`Could not load documents: ${error.message}`);
    }
}



function renderDocuments(documents) {
    elements.documentList.replaceChildren();

    if (documents.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "No documents in this notebook yet.";

        elements.documentList.appendChild(empty);
        return;
    }

    documents.forEach(doc => {
        const item = document.createElement("div");
        item.className = "document-item";

        const extension = doc.original_filename
            .split(".")
            .pop()
            .toUpperCase();

        const icon = document.createElement("div");
        icon.className = "document-icon";
        icon.textContent = extension;

        const info = document.createElement("div");
        info.className = "document-info";

        const name = document.createElement("div");
        name.className = "document-name";
        name.textContent = doc.original_filename;
        name.title = doc.original_filename;

        const status = document.createElement("div");
        status.className = "document-status";
        status.textContent = formatStatus(doc.processing_status);

        info.append(name, status);
        item.append(icon, info);

        elements.documentList.appendChild(item);
    });
}



function formatStatus(status) {
    const labels = {
        pending: "Waiting to process",
        processing: "Processing...",
        completed: "Processed",
        success: "Processed",
        failed: "Processing failed"
    };

    return labels[status] || status || "Unknown status";
}


elements.addDocumentButton.addEventListener("click", () => {
    if (!activeNotebookId) {
        showError("Select a notebook first.");
        return;
    }

    elements.fileInput.click();
});


elements.fileInput.addEventListener("change", async () => {
    const files = Array.from(elements.fileInput.files || []);

    if (!activeNotebookId || files.length === 0) {
        return;
    }

    const formData = new FormData();

    files.forEach(file => {
        formData.append("files", file);
    });

    elements.addDocumentButton.disabled = true;
    elements.addDocumentButton.textContent = "Uploading...";

    try {
        await apiRequest(
            `${API_BASE}/${activeNotebookId}/documents`,
            {
                method: "POST",
                body: formData
            }
        );

        await loadDocuments(activeNotebookId);
        await loadNotebooks();

        startStatusPolling();

    } catch (error) {
        showError(`Upload failed: ${error.message}`);

    } finally {
        elements.addDocumentButton.disabled = false;
        elements.addDocumentButton.innerHTML =
            "<span>+</span> Add document";

        elements.fileInput.value = "";
    }
});


// --------------------------------------------------
// Document status polling
// --------------------------------------------------

function startStatusPolling() {
    if (statusPollingTimer) {
        clearInterval(statusPollingTimer);
    }

    if (!activeNotebookId) {
        return;
    }

    statusPollingTimer = setInterval(async () => {
        if (!activeNotebookId) {
            return;
        }

        await loadDocuments(activeNotebookId);
    }, 5000);
}


// --------------------------------------------------
// Chat management
// --------------------------------------------------

function clearChat() {
    elements.chatContent.replaceChildren();

    const welcome = document.createElement("div");
    welcome.className = "welcome-screen";

    const icon = document.createElement("div");
    icon.className = "welcome-icon";
    icon.textContent = "K";

    const heading = document.createElement("h1");
    heading.textContent = "What would you like to learn?";

    const description = document.createElement("p");
    description.textContent =
        "Ask questions about the documents in this notebook.";

    welcome.append(icon, heading, description);
    elements.chatContent.appendChild(welcome);
}


elements.clearChatButton.addEventListener("click", clearChat);


elements.chatForm.addEventListener("submit", async event => {
    event.preventDefault();

    const question = elements.questionInput.value.trim();

    if (!question || !activeNotebookId || isAsking) {
        return;
    }

    await askQuestion(question);
});

// Enter submits the question.
// Shift + Enter inserts a new line.
elements.questionInput.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();

        elements.chatForm.requestSubmit();
    }
});


async function askQuestion(question) {
    isAsking = true;

    elements.questionInput.value = "";
    elements.sendButton.disabled = true;

    removeWelcomeScreen();

    appendMessage("user", question);

    const loadingMessage = appendMessage(
        "assistant",
        "Thinking..."
    );

    try {
        const data = await apiRequest(
            `${API_BASE}/${activeNotebookId}/ask`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ question })
            }
        );

        loadingMessage.remove();

        appendMessage(
            "assistant",
            data.answer || "No answer was returned.",
            data.sources || []
        );

    } catch (error) {
        loadingMessage.textContent =
            `Could not generate an answer: ${error.message}`;

    } finally {
        isAsking = false;
        elements.sendButton.disabled = false;
        elements.questionInput.focus();
    }
}


function removeWelcomeScreen() {
    const welcome = elements.chatContent.querySelector(".welcome-screen");

    if (welcome) {
        welcome.remove();
    }
}


function appendMessage(role, content, sources = []) {
    const message = document.createElement("div");
    message.className = `chat-message ${role}-message`;

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = role === "user" ? "You" : "Knowvia";

    const body = document.createElement("div");
    body.className = "message-content";
    body.innerHTML  = renderMarkdown(content);

    message.append(label, body);

    if (role === "assistant" && sources.length > 0) {
        const sourceContainer = document.createElement("div");
        sourceContainer.className = "message-sources";

        const heading = document.createElement("div");
        heading.className = "sources-heading";
        heading.textContent = `Sources (${sources.length})`;

        sourceContainer.appendChild(heading);

        sources.forEach((source, index) => {
            const sourceItem = document.createElement("details");
            sourceItem.className = "source-item";

            const summary = document.createElement("summary");
            const page = source.page_number
                ? ` · Page ${source.page_number}`
                : "";

            summary.textContent =
                `Source ${index + 1} · Document ${source.document_id}${page}`;

            const excerpt = document.createElement("p");
            excerpt.textContent = source.content || "";

            sourceItem.append(summary, excerpt);
            sourceContainer.appendChild(sourceItem);
        });

        message.appendChild(sourceContainer);
    }

    elements.chatContent.appendChild(message);
    elements.chatContent.scrollTop = elements.chatContent.scrollHeight;

    return message;
}


// --------------------------------------------------
// Initial application load
// --------------------------------------------------

async function initializeApp() {
    elements.questionInput.disabled = true;
    elements.sendButton.disabled = true;
    elements.addDocumentButton.disabled = true;

    await loadNotebooks();
}

initializeApp();
