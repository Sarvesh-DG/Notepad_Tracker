
// ==========================================
// 1. DOM ELEMENTS
// ==========================================

const editor = document.getElementById("editor");

const fileList = document.getElementById("fileList");
const directoryList = document.getElementById("directoryList");

const currentFilename = document.getElementById("currentFilename");
const currentDirectory = document.getElementById("currentDirectory");
const saveStatus = document.getElementById("saveStatus");

const wordCount = document.getElementById("wordCount");
const characterCount = document.getElementById("characterCount");

const newFileBtn = document.getElementById("newFileBtn");
const refreshBtn = document.getElementById("refreshBtn");
const deleteFileBtn = document.getElementById("deleteFileBtn");

const chooseFolderBtn = document.getElementById("chooseFolderBtn");
const parentFolderBtn = document.getElementById("parentFolderBtn");

const gitStatusBtn = document.getElementById("gitStatusBtn");
const historyBtn = document.getElementById("historyBtn");
const fileHistoryBtn = document.getElementById("fileHistoryBtn");

const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modalTitle");
const modalBody = document.getElementById("modalBody");
const closeModalBtn = document.getElementById("closeModalBtn");


// ==========================================
// 2. APPLICATION STATE
// ==========================================

let activeFile = null;
let activeDirectory = null;

let saveTimer = null;

let isDirty = false;
let isSaving = false;
let gitReady = true;

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


function jsonOptions(method, body) {

    return {
        method: method,
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    };

}


// ==========================================
// 4. MODAL
// ==========================================

function showModal(title, content) {

    modalTitle.textContent = title;

    modalBody.replaceChildren();

    const message = document.createElement("pre");

    message.textContent = content;

    modalBody.appendChild(message);

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
// 6. UPDATE DIRECTORY DISPLAY
// ==========================================

function updateDirectoryDisplay(directory) {

    activeDirectory = directory;

    currentDirectory.textContent = directory;

}


// ==========================================
// 7. LOAD FILES
// ==========================================

async function loadFiles() {

    try {

        const data = await apiRequest("/api/files");

        fileList.replaceChildren();

        if (data.length === 0) {

            const empty = document.createElement("li");

            empty.textContent = "No files found";

            fileList.appendChild(empty);

            return;

        }

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

        showModal("File Loading Error", error.message);

    }

}


// ==========================================
// 8. LOAD DIRECTORIES
// ==========================================

async function loadDirectories() {

    try {

        const data = await apiRequest("/api/directories");

        directoryList.replaceChildren();

        if (data.length === 0) {

            const empty = document.createElement("li");

            empty.textContent = "No folders found";

            directoryList.appendChild(empty);

            return;

        }

        data.forEach(folder => {

            const li = document.createElement("li");

            li.textContent = `📁 ${folder}`;

            li.addEventListener("click", () => {
                navigateDirectory(folder);
            });

            directoryList.appendChild(li);

        });

    } catch (error) {

        showModal("Directory Loading Error", error.message);

    }

}


// ==========================================
// 9. REFRESH FILES AND DIRECTORIES
// ==========================================

async function refreshWorkspace() {

    await Promise.all([
        loadFiles(),
        loadDirectories()
    ]);

}


// ==========================================
// 10. SAVE FILE
// ==========================================

function saveFile() {

    clearTimeout(saveTimer);

    if (!activeFile || !isDirty) {
        return Promise.resolve();
    }

    if (!gitReady) {
        return Promise.reject(
            new Error("Initialize Git in this folder before editing.")
        );
    }

    const filename = activeFile;
    const content = editor.value;

    isDirty = false;

    saveStatus.textContent = "Saving...";

    const task = saveQueue.catch(() => {}).then(async () => {

        isSaving = true;

        try {

            await apiRequest(
                `/api/files/${encodeURIComponent(filename)}`,
                jsonOptions("PUT", {
                    content: content
                })
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

    saveQueue = task;

    return task.catch(error => {

        if (activeFile === filename) {

            isDirty = true;

            saveStatus.textContent = "Save failed";

        }

        throw error;

    });

}


// ==========================================
// 11. AUTOMATIC SAVE
// ==========================================

function scheduleSave() {

    clearTimeout(saveTimer);

    if (!activeFile) {
        return;
    }

    isDirty = true;

    saveStatus.textContent = "Unsaved changes...";

    saveTimer = setTimeout(() => {

        saveFile().catch(error => {
            console.error("Automatic save failed:", error);
        });

    }, SAVE_DELAY);

}


// ==========================================
// 12. FLUSH PENDING SAVES
// ==========================================

async function flushSave() {

    clearTimeout(saveTimer);

    while (isDirty) {

        await saveFile();

    }

    await saveQueue;

}


// ==========================================
// 13. OPEN FILE
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

        showModal("Unable to Open File", error.message);

    }

}


// ==========================================
// 14. CREATE FILE
// ==========================================

async function createFile() {

    if (!gitReady) {

        showModal(
            "Git Not Initialized",
            "Initialize Git in the selected directory before creating files."
        );

        return;

    }

    const filename = prompt("Enter file name:");

    if (!filename || !filename.trim()) {
        return;
    }

    try {

        await flushSave();

        const cleanFilename = filename.trim();

        await apiRequest(
            "/api/files",
            jsonOptions("POST", {
                filename: cleanFilename,
                content: ""
            })
        );

        await refreshWorkspace();

        await openFile(cleanFilename);

    } catch (error) {

        showModal("Unable to Create File", error.message);

    }

}


// ==========================================
// 15. DELETE FILE
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

        await refreshWorkspace();

    } catch (error) {

        showModal("Delete Failed", error.message);

    }

}


// ==========================================
// 16. SELECT A DIFFERENT FOLDER
// ==========================================

async function chooseFolder() {

    try {

        await flushSave();

        const data = await apiRequest("/api/select-folder", {
            method: "POST"
        });

        if (!data.directory) {
            return;
        }

        gitReady = Boolean(data.git_initialized);

        if (!gitReady) {

            const initialize = confirm(
                "This folder is not a Git repository.\n\n" +
                "Would you like to initialize Git here?"
            );

            if (initialize) {

                await apiRequest("/api/git/init", {
                    method: "POST"
                });

                gitReady = true;

            } else {

                showModal(
                    "Git Not Initialized",
                    "The folder has been selected, but editing and file creation require Git initialization."
                );

            }

        }

        activeFile = null;

        editor.value = "";

        editor.disabled = true;

        currentFilename.textContent = "No file selected";

        saveStatus.textContent = gitReady
            ? "Folder selected"
            : "Git initialization required";

        isDirty = false;

        updateDirectoryDisplay(data.directory);

        updateCounts();

        await refreshWorkspace();

    } catch (error) {

        showModal("Folder Selection Error", error.message);

    }

}


// ==========================================
// 17. NAVIGATE INTO A FOLDER
// ==========================================

async function navigateDirectory(folder) {

    try {

        await flushSave();

        const data = await apiRequest(
            "/api/navigate-directory",
            jsonOptions("POST", {
                directory: folder
            })
        );

        activeFile = null;

        editor.value = "";

        editor.disabled = true;

        currentFilename.textContent = "No file selected";

        saveStatus.textContent = "Folder opened";

        isDirty = false;

        updateDirectoryDisplay(data.directory);

        updateCounts();

        await refreshWorkspace();

    } catch (error) {

        showModal("Navigation Error", error.message);

    }

}


// ==========================================
// 18. NAVIGATE TO PARENT DIRECTORY
// ==========================================

async function navigateParent() {

    try {

        await flushSave();

        const data = await apiRequest(
            "/api/navigate-parent",
            {
                method: "POST"
            }
        );

        activeFile = null;

        editor.value = "";

        editor.disabled = true;

        currentFilename.textContent = "No file selected";

        saveStatus.textContent = "Parent folder opened";

        isDirty = false;

        updateDirectoryDisplay(data.directory);

        updateCounts();

        await refreshWorkspace();

    } catch (error) {

        showModal("Navigation Error", error.message);

    }

}


// ==========================================
// 19. GIT STATUS
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
// 20. REPOSITORY HISTORY
// ==========================================

async function getGitHistory() {

    try {

        const data = await apiRequest("/api/git/history");

        showModal("Repository History", data.output);

    } catch (error) {

        showModal("History Error", error.message);

    }

}


// ==========================================
// 21. FILE HISTORY
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

            modalBody.textContent = "No commit history found.";

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

                details.textContent = `${commitId} - ${message}`;

                const restoreBtn = document.createElement("button");

                restoreBtn.textContent = "Restore this version";

                restoreBtn.disabled = !gitReady;

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
// 22. RESTORE PREVIOUS VERSION
// ==========================================

async function restoreFile(commitId) {

    if (!activeFile || !gitReady) {
        return;
    }

    const filename = activeFile;

    const confirmed = confirm(
        `Restore ${filename} to commit ${commitId}?\n\n` +
        "Your current contents will be replaced."
    );

    if (!confirmed) {
        return;
    }

    try {

        await flushSave();

        await apiRequest(
            `/api/git/restore/${encodeURIComponent(filename)}`,
            jsonOptions("POST", {
                commit_id: commitId
            })
        );

        const data = await apiRequest(
            `/api/files/${encodeURIComponent(filename)}`
        );

        editor.value = data.content;

        isDirty = false;

        saveStatus.textContent = "Version restored and committed";

        updateCounts();

        await refreshWorkspace();

        await getFileHistory();

    } catch (error) {

        showModal("Restore Error", error.message);

    }

}


// ==========================================
// 23. CTRL + S
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
// 24. UNSAVED CHANGE PROTECTION
// ==========================================

window.addEventListener("beforeunload", event => {

    if (isDirty || isSaving) {

        event.preventDefault();

        event.returnValue = "";

    }

});


// ==========================================
// 25. EDITOR INPUT
// ==========================================

editor.addEventListener("input", () => {

    updateCounts();

    scheduleSave();

});


// ==========================================
// 26. BUTTON EVENTS
// ==========================================

newFileBtn.addEventListener("click", createFile);

refreshBtn.addEventListener("click", refreshWorkspace);

deleteFileBtn.addEventListener("click", deleteFile);

chooseFolderBtn.addEventListener("click", chooseFolder);

parentFolderBtn.addEventListener("click", navigateParent);

gitStatusBtn.addEventListener("click", getGitStatus);

historyBtn.addEventListener("click", getGitHistory);

fileHistoryBtn.addEventListener("click", getFileHistory);


// ==========================================
// 27. INITIAL APPLICATION LOAD
// ==========================================

editor.disabled = true;

updateCounts();

refreshWorkspace();

