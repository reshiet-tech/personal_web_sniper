const REPO = "reshiet-tech/personal_web_sniper";
const TARGETS_PATH = "data/targets.json";
let GITHUB_TOKEN = localStorage.getItem("gh_token") || "";
let targetsData = [];
let fileSha = "";

// UI Elements
const loginScreen = document.getElementById("login-screen");
const dashboardScreen = document.getElementById("dashboard-screen");
const tokenInput = document.getElementById("gh-token");
const btnLogin = document.getElementById("btn-login");
const btnLogout = document.getElementById("btn-logout");
const targetsGrid = document.getElementById("targets-grid");
const loading = document.getElementById("loading");
const btnRefresh = document.getElementById("btn-refresh");

// Initialize
if (GITHUB_TOKEN) {
    showDashboard();
}

// Login
btnLogin.addEventListener("click", () => {
    const token = tokenInput.value.trim();
    if (token) {
        GITHUB_TOKEN = token;
        localStorage.setItem("gh_token", token);
        showDashboard();
    }
});

// Logout
btnLogout.addEventListener("click", () => {
    GITHUB_TOKEN = "";
    localStorage.removeItem("gh_token");
    loginScreen.classList.remove("hidden");
    dashboardScreen.classList.add("hidden");
});

function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = "toast show";
    setTimeout(() => { toast.className = toast.className.replace("show", ""); }, 3000);
}

function showDashboard() {
    loginScreen.classList.add("hidden");
    dashboardScreen.classList.remove("hidden");
    loadTargets();
}

btnRefresh.addEventListener("click", loadTargets);

async function loadTargets() {
    loading.classList.remove("hidden");
    targetsGrid.classList.add("hidden");
    try {
        const response = await fetch(`https://api.github.com/repos/${REPO}/contents/${TARGETS_PATH}`, {
            headers: {
                "Authorization": `token ${GITHUB_TOKEN}`,
                "Accept": "application/vnd.github.v3+json"
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                alert("토큰이 유효하지 않습니다. 다시 로그인해주세요.");
                btnLogout.click();
                return;
            }
            throw new Error(`HTTP Error: ${response.status}`);
        }

        const data = await response.json();
        fileSha = data.sha;
        const decodedContent = decodeURIComponent(escape(atob(data.content)));
        targetsData = JSON.parse(decodedContent);
        renderTargets();
    } catch (error) {
        console.error(error);
        alert("데이터를 불러오는데 실패했습니다: " + error.message);
    } finally {
        loading.classList.add("hidden");
    }
}

function renderTargets() {
    targetsGrid.innerHTML = "";
    targetsGrid.classList.remove("hidden");

    targetsData.forEach((target, index) => {
        const domain = new URL(target.url).hostname;
        const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
        
        const card = document.createElement("div");
        card.className = "glass-card target-card";
        
        const successText = (target.success_text && target.success_text.length) ? target.success_text.join(', ') : '없음 (AI 판독)';
        const failureText = (target.failure_text && target.failure_text.length) ? target.failure_text.join(', ') : '없음';
        const aiPrompt = target.ai_prompt ? `🤖 AI 프롬프트: ${target.ai_prompt}` : '';
        const isActive = target.is_active !== false;

        card.innerHTML = `
            <div class="target-header">
                <img src="${faviconUrl}" width="24" style="border-radius:4px;">
                <h3>${target.name}</h3>
            </div>
            
            <div class="switch-container">
                <label class="switch">
                    <input type="checkbox" onchange="toggleActive(${index}, this.checked)" ${isActive ? 'checked' : ''}>
                    <span class="slider"></span>
                </label>
                <span>감시 활성화</span>
            </div>

            <button class="outline-btn" onclick="window.open('${target.url}', '_blank')">🔗 웹사이트 바로가기</button>

            <div class="target-info">
                <p>✅ 성공: ${successText}</p>
                <p>❌ 실패: ${failureText}</p>
                ${aiPrompt ? `<p>${aiPrompt}</p>` : ''}
            </div>

            <div class="target-actions">
                <button class="outline-btn" onclick="openEditModal(${index})">수정 ✏️</button>
                <button class="danger-btn" onclick="deleteTarget(${index})">삭제 🗑️</button>
            </div>
        `;
        targetsGrid.appendChild(card);
    });
}

async function saveTargetsToGithub() {
    const contentStr = JSON.stringify(targetsData, null, 4);
    const encodedContent = btoa(unescape(encodeURIComponent(contentStr)));

    try {
        const response = await fetch(`https://api.github.com/repos/${REPO}/contents/${TARGETS_PATH}`, {
            method: 'PUT',
            headers: {
                "Authorization": `token ${GITHUB_TOKEN}`,
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: "Update targets via Web Dashboard",
                content: encodedContent,
                sha: fileSha
            })
        });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        
        const data = await response.json();
        fileSha = data.content.sha;
        showToast("✅ 클라우드 업데이트 완료!");
        renderTargets();
    } catch (error) {
        console.error(error);
        alert("저장에 실패했습니다: " + error.message);
    }
}

// Actions
window.toggleActive = function(index, isActive) {
    targetsData[index].is_active = isActive;
    saveTargetsToGithub();
}

window.deleteTarget = function(index) {
    if(confirm("정말 이 타겟을 삭제하시겠습니까?")) {
        targetsData.splice(index, 1);
        saveTargetsToGithub();
    }
}

// Add Target
document.getElementById("btn-add-target").addEventListener("click", () => {
    const name = document.getElementById("new-name").value.trim();
    const url = document.getElementById("new-url").value.trim();
    
    if (!name || !url) return alert("이름과 URL은 필수 입력 항목입니다.");

    const parseList = (str) => str.split(",").map(s => s.trim()).filter(s => s);
    const parseLines = (str) => str.split("\n").map(s => s.trim()).filter(s => s);

    targetsData.push({
        name,
        url,
        selector: document.getElementById("new-selector").value.trim() || "body",
        success_text: parseList(document.getElementById("new-success").value),
        failure_text: parseList(document.getElementById("new-failure").value),
        use_simple_fetch: document.getElementById("new-simple-fetch").checked,
        ai_prompt: document.getElementById("new-ai-prompt").value.trim(),
        ignore_selectors: parseLines(document.getElementById("new-ignore-sel").value),
        ignore_regex: parseLines(document.getElementById("new-ignore-reg").value),
        is_active: true
    });

    saveTargetsToGithub().then(() => {
        // Reset form
        ['name', 'url', 'success', 'failure', 'ai-prompt', 'ignore-sel', 'ignore-reg'].forEach(id => {
            document.getElementById(`new-${id}`).value = '';
        });
        document.getElementById("new-selector").value = 'body';
        document.getElementById("new-simple-fetch").checked = false;
    });
});

// Edit Modal
const editModal = document.getElementById("edit-modal");

window.openEditModal = function(index) {
    const target = targetsData[index];
    document.getElementById("edit-idx").value = index;
    document.getElementById("edit-name").value = target.name;
    document.getElementById("edit-url").value = target.url;
    document.getElementById("edit-selector").value = target.selector || 'body';
    document.getElementById("edit-success").value = (target.success_text||[]).join(', ');
    document.getElementById("edit-failure").value = (target.failure_text||[]).join(', ');
    document.getElementById("edit-simple-fetch").checked = target.use_simple_fetch || false;
    document.getElementById("edit-ai-prompt").value = target.ai_prompt || '';
    document.getElementById("edit-ignore-sel").value = (target.ignore_selectors||[]).join('\n');
    document.getElementById("edit-ignore-reg").value = (target.ignore_regex||[]).join('\n');
    
    editModal.classList.remove("hidden");
}

document.getElementById("btn-cancel-edit").addEventListener("click", () => {
    editModal.classList.add("hidden");
});

document.getElementById("btn-save-edit").addEventListener("click", () => {
    const index = parseInt(document.getElementById("edit-idx").value);
    const name = document.getElementById("edit-name").value.trim();
    const url = document.getElementById("edit-url").value.trim();
    
    if (!name || !url) return alert("이름과 URL은 필수입니다.");

    const parseList = (str) => str.split(",").map(s => s.trim()).filter(s => s);
    const parseLines = (str) => str.split("\n").map(s => s.trim()).filter(s => s);

    targetsData[index] = {
        ...targetsData[index],
        name,
        url,
        selector: document.getElementById("edit-selector").value.trim() || "body",
        success_text: parseList(document.getElementById("edit-success").value),
        failure_text: parseList(document.getElementById("edit-failure").value),
        use_simple_fetch: document.getElementById("edit-simple-fetch").checked,
        ai_prompt: document.getElementById("edit-ai-prompt").value.trim(),
        ignore_selectors: parseLines(document.getElementById("edit-ignore-sel").value),
        ignore_regex: parseLines(document.getElementById("edit-ignore-reg").value)
    };

    saveTargetsToGithub().then(() => {
        editModal.classList.add("hidden");
    });
});
