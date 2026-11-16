
// ==========================================
// 1. DOM ELEMENTS
// ==========================================

const editor = document.getElementById("editor");
const fileList = document.getElementById("fileList");

const currentFilename = document.getElementById("currentFilename");
const saveStatus = document.getElementById("saveStatus");

const wordCount = document.getElementById("wordCount");
const characterCount = document.getElementById("characterCount");

const newFileBtn = document.getElementById("newFileBtn");
const refreshBtn = document.getElementById("refreshBtn");
const deleteFileBtn = document.getElementById("deleteFileBtn");
const gitStatusBtn = document.getElementById("gitStatusBtn");
const historyBtn = document.getElementById("historyBtn");

const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modalTitle");
const modalBody = document.getElementById("modalBody");
const closeModalBtn = document.getElementById("closeModalBtn");


// ==========================================
// 2. APPLICATION STATE
// ==========================================

let activeFile = null;
let saveTimer = null;

let isDirty = false;
let isSaving = false;

const SAVE_DELAY = 1000;

let saveQueue = Promise.resolve();


// ==========================================
// 3. API HELPER
// ==========================================

async function apiRequest(url, options = {}) {

    const response = await fetch(url, options);

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Invalid server response");
    }

    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }

    return data;
}


// ==========================================
// 4. MODAL FUNCTIONS
// ==========================================

function showModal(title, content) {

    modalTitle.textContent = title;
    modalBody.textContent = content;

    modal.classList.remove("hidden");
}


function closeModal() {
    modal.classList.add("hidden");
}


closeModalBtn.addEventListener("click", closeModal);


// ==========================================
// 5. WORD AND CHARACTER COUNT
// ==========================================

function updateCounts() {

    const content = editor.value;

    const words = content.trim()
        ? content.trim().split(/\s+/).length
        : 0;

    wordCount.textContent = `${words} words`;

    characterCount.textContent =
        `${content.length} characters`;
}


// ==========================================
// 6. LOAD FILES
// ==========================================

async function loadFiles() {

    try {

        const data = await apiRequest("/api/files");

        fileList.innerHTML = "";

        data.forEach(item => {

            const li = document.createElement("li");

            li.textContent = item.file;

            if (item.file === activeFile) {
                li.classList.add("active");
            }

            li.addEventListener("click", () => {
                openFile(item.file);
            });

            fileList.appendChild(li);

        });

    } catch (error) {

        showModal("Error", error.message);

    }
}


// ==========================================
// 7. SAVE FILE
// ==========================================

function saveFile() {

    clearTimeout(saveTimer);

    if (!activeFile || !isDirty) {
        return Promise.resolve();
    }

    const filename = activeFile;
    const content = editor.value;

    isDirty = false;

    saveStatus.textContent = "Saving...";

    const task = saveQueue.then(async () => {

        isSaving = true;

        try {

            await apiRequest(
                `/api/files/${encodeURIComponent(filename)}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        content: content
                    })
                }
            );

            if (activeFile === filename) {

                if (editor.value === content) {

                    saveStatus.textContent = "Saved successfully";

                } else {

                    isDirty = true;
                    scheduleSave();

                }

            }

        } finally {

            isSaving = false;

        }

    });

    // Keep the queue usable even if one save fails.
    saveQueue = task.catch(error => {

        console.error("Save error:", error);

    });

    return task.catch(error => {

        if (activeFile === filename) {

            isDirty = true;

            saveStatus.textContent = "Save failed";

        }

        throw error;

    });

}


// ==========================================
// 8. AUTOMATIC SAVE
// ==========================================

function scheduleSave() {

    clearTimeout(saveTimer);

    if (!activeFile) {
        return;
    }

    isDirty = true;

    saveStatus.textContent = "Unsaved changes...";

    saveTimer = setTimeout(() => {

        saveFile().catch(() => {
            // Error is reflected in the save status.
        });

    }, SAVE_DELAY);

}


// ==========================================
// 9. FLUSH PENDING SAVES
// ==========================================

async function flushSave() {

    clearTimeout(saveTimer);

    while (isDirty) {

        await saveFile();

    }

    await saveQueue;

}


// ==========================================
// 10. OPEN FILE
// ==========================================

async function openFile(filename) {

    try {

        await flushSave();

        const data = await apiRequest(
            `/api/files/${encodeURIComponent(filename)}`
        );

        activeFile = filename;

        editor.value = data.content;

        editor.disabled = false;

        currentFilename.textContent = filename;

        isDirty = false;

        saveStatus.textContent = "Saved";

        updateCounts();

        await loadFiles();

    } catch (error) {

        showModal("Unable to open file", error.message);

    }

}


// ==========================================
// 11. CREATE NEW FILE
// ==========================================

async function createFile() {

    const filename = prompt("Enter file name:");

    if (!filename || !filename.trim()) {
        return;
    }

    try {

        await flushSave();

        const cleanFilename = filename.trim();

        await apiRequest("/api/files", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                filename: cleanFilename,

                content: ""

            })

        });

        await loadFiles();

        await openFile(cleanFilename);

    } catch (error) {

        showModal("Unable to create file", error.message);

    }

}


// ==========================================
// 12. DELETE FILE
// ==========================================

async function deleteFile() {

    if (!activeFile) {

        alert("Select a file first.");

        return;

    }

    if (!confirm(`Delete ${activeFile}?`)) {
        return;
    }

    try {

        await flushSave();

        const filename = activeFile;

        await apiRequest(
            `/api/files/${encodeURIComponent(filename)}`,
            {
                method: "DELETE"
            }
        );

        activeFile = null;

        editor.value = "";

        editor.disabled = true;

        currentFilename.textContent = "No file selected";

        saveStatus.textContent = "Ready";

        isDirty = false;

        updateCounts();

        await loadFiles();

    } catch (error) {

        showModal("Delete failed", error.message);

    }

}


// ==========================================
// 13. GIT STATUS
// ==========================================

async function getGitStatus() {

    try {

        const data = await apiRequest("/api/git/status");

        showModal("Git Status", data.output);

    } catch (error) {

        showModal("Git Status Error", error.message);

    }

}


// ==========================================
// 14. COMPLETE GIT HISTORY
// ==========================================

async function getGitHistory() {

    try {

        const data = await apiRequest("/api/git/history");

        showModal("Git Commit History", data.output);

    } catch (error) {

        showModal("History Error", error.message);

    }

}


// ==========================================
// 15. FILE-SPECIFIC HISTORY
// ==========================================

async function getFileHistory() {

    if (!activeFile) {

        alert("Select a file first.");

        return;

    }

    try {

        await flushSave();

        const filename = activeFile;

        const data = await apiRequest(
            `/api/git/history/${encodeURIComponent(filename)}`
        );

        modalTitle.textContent = `History: ${filename}`;

        modalBody.replaceChildren();

        const commits = data.output
            .trim()
            .split("\n")
            .filter(Boolean);

        if (commits.length === 0) {

            modalBody.textContent =
                "No commit history found for this file.";

        } else {

            commits.forEach(line => {

                const match = line.match(/^(\S+)\s+(.*)$/);

                if (!match) {
                    return;
                }

                const commitId = match[1];

                const message = match[2];

                const entry = document.createElement("div");

                entry.className = "history-entry";

                const details = document.createElement("p");

                details.textContent =
                    `${commitId} - ${message}`;

                const restoreBtn = document.createElement("button");

                restoreBtn.textContent = "Restore this version";

                restoreBtn.className = "secondary-btn";

                restoreBtn.addEventListener("click", () => {

                    restoreFile(commitId);

                });

                entry.appendChild(details);

                entry.appendChild(restoreBtn);

                modalBody.appendChild(entry);

            });

        }

        modal.classList.remove("hidden");

    } catch (error) {

        showModal("File History Error", error.message);

    }

}


// ==========================================
// 16. RESTORE PREVIOUS VERSION
// ==========================================

async function restoreFile(commitId) {

    if (!activeFile) {
        return;
    }

    const filename = activeFile;

    const confirmed = confirm(

        `Restore ${filename} to commit ${commitId}?\n\n` +

        "Your current version will be replaced."

    );

    if (!confirmed) {
        return;
    }

    try {

        await flushSave();

        await apiRequest(
            `/api/git/restore/${encodeURIComponent(filename)}`,
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    commit_id: commitId
                })

            }
        );

        // Retrieve restored contents.

        const data = await apiRequest(
            `/api/files/${encodeURIComponent(filename)}`
        );

        activeFile = filename;

        editor.value = data.content;

        editor.disabled = false;

        currentFilename.textContent = filename;

        isDirty = false;

        saveStatus.textContent =
            "Version restored and committed";

        updateCounts();

        await loadFiles();

        // Display refreshed history.

        await getFileHistory();

    } catch (error) {

        showModal("Restore Error", error.message);

    }

}


// ==========================================
// 17. MANUAL SAVE - CTRL + S
// ==========================================

document.addEventListener("keydown", async event => {

    if (
        (event.ctrlKey || event.metaKey) &&
        event.key.toLowerCase() === "s"
    ) {

        event.preventDefault();

        try {

            await flushSave();

            if (activeFile) {
                saveStatus.textContent = "Saved successfully";
            }

        } catch (error) {

            showModal("Save Error", error.message);

        }

    }

});


// ==========================================
// 18. UNSAVED CHANGE PROTECTION
// ==========================================

window.addEventListener("beforeunload", event => {

    if (isDirty || isSaving) {

        event.preventDefault();

        event.returnValue = "";

    }

});


// ==========================================
// 19. EDITOR EVENTS
// ==========================================

editor.addEventListener("input", () => {

    updateCounts();

    scheduleSave();

});


// ==========================================
// 20. FILE HISTORY BUTTON
// ==========================================

// Create the button dynamically.

const fileHistoryBtn = document.createElement("button");

fileHistoryBtn.id = "fileHistoryBtn";

fileHistoryBtn.textContent = "File History";

fileHistoryBtn.className = deleteFileBtn.className;

deleteFileBtn.insertAdjacentElement(
    "afterend",
    fileHistoryBtn
);


// ==========================================
// 21. BUTTON EVENTS
// ==========================================

newFileBtn.addEventListener("click", createFile);

refreshBtn.addEventListener("click", loadFiles);

deleteFileBtn.addEventListener("click", deleteFile);

gitStatusBtn.addEventListener("click", getGitStatus);

historyBtn.addEventListener("click", getGitHistory);

fileHistoryBtn.addEventListener("click", getFileHistory);


// ==========================================
// 22. INITIAL APPLICATION LOAD
// ==========================================

editor.disabled = true;

loadFiles();

updateCounts();
