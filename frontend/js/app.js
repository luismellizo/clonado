const API_URL = window.location.origin + "/api";

let currentJobId = null;
let currentTaskId = null;

async function startCloning() {
    const urlInput = document.getElementById('targetUrl');
    const url = urlInput.value.trim();

    if (!url) {
        showNotification("URL_INVALID: Please enter a correct http/https URL", "error");
        return;
    }

    if (!url.startsWith('http')) {
        showNotification("PROTOCOL_ERROR: URL must start with http:// or https://", "error");
        return;
    }

    try {
        // Reset UI
        resetUI();
        document.getElementById('terminalArea').classList.remove('hidden');
        document.getElementById('resultsSection').classList.add('hidden');
        document.getElementById('cloneBtn').disabled = true;
        document.getElementById('cloneBtn').innerText = "EXECUTING...";

        log(`> SYSTEM_INIT: Target=${url}`);
        log(`> HANDSHAKE: Connecting to server...`);

        // Start Job
        const response = await fetch(`${API_URL}/clone`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!response.ok) throw new Error("Connection Refused / Server Error");

        const data = await response.json();
        currentTaskId = data.task_id;
        currentJobId = data.job_id;

        log(`> TASK_CREATED: ID [${currentTaskId.substring(0, 8)}]`);
        log(`> PROCESS_START: Analyzing vectors...`);

        // Poll Status
        pollStatus(currentTaskId, currentJobId);

    } catch (error) {
        log(`> FATAL_ERROR: ${error.message}`);
        enableButton();
        showNotification(error.message, "error");
    }
}

async function pollStatus(taskId, jobId) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_URL}/status/${taskId}`);
            const data = await response.json();

            if (data.status === 'PENDING') {
                updateProgress(5, "QUEUEING...");
            } else if (data.status === 'PROGRESS') {
                const meta = data.result || {};
                const progress = meta.progress || 10;
                const statusMsg = meta.status || "PROCESSING...";
                updateProgress(progress, statusMsg.toUpperCase());
            } else if (data.status === 'SUCCESS') {
                clearInterval(pollInterval);
                updateProgress(100, "COMPLETED");
                log(`> PROCESS_COMPLETE: Success.`);

                // Show analysis results
                if (data.analysis) {
                    displayAnalysis(data.analysis);
                }

                // Show download button
                const downloadBtn = document.getElementById('downloadLink');
                downloadBtn.href = `${API_URL}/download/${jobId}`;
                document.getElementById('resultAction').classList.remove('hidden');

                enableButton();
                showNotification("MISSION SUCCESS: Site cloned.", "success");

            } else if (data.status === 'FAILURE') {
                clearInterval(pollInterval);
                updateProgress(0, "FAILURE");
                log(`> SYSTEM_FAILURE: ${data.result}`);
                enableButton();
                showNotification("Process Failed", "error");
            }

        } catch (error) {
            console.error(error);
        }
    }, 1500);
}

function displayAnalysis(analysis) {
    document.getElementById('resultsSection').classList.remove('hidden');

    // SEO Score
    const score = analysis.seo?.score || 0;
    const scoreCircle = document.getElementById('scoreCircle');
    const scoreValue = document.getElementById('scoreValue');

    // Animate score circle (circumference = 283)
    const offset = 283 - (283 * score / 100);
    scoreCircle.style.strokeDashoffset = offset;
    scoreValue.textContent = score;

    // SEO Details (Text list)
    const seoDetails = document.getElementById('seoDetails');
    const seoData = analysis.seo || {};

    // Tech Stack
    const techStack = document.getElementById('techStack');
    const techs = analysis.technologies || {};
    let techHtml = '';

    const categoryIcons = {
        'frameworks': '⚡',
        'cms': '🏗️',
        'css_frameworks': '🎨',
        'analytics': '📊',
        'cdn': '🌍',
        'libraries': '📚',
        'ecommerce': '🛍️',
        'hosting': '☁️'
    };

    for (const [category, items] of Object.entries(techs)) {
        const icon = categoryIcons[category] || '🔧';
        for (const item of items) {
            techHtml += `
                <div class="tech-badge px-3 py-2 flex items-center gap-2 border border-gray-800 bg-black text-gray-300">
                    <span class="text-amber-500">${icon}</span>
                    <span class="font-mono text-xs uppercase">${item}</span>
                </div>
            `;
        }
    }

    if (!techHtml) {
        techHtml = '<p class="text-gray-600 font-mono text-xs p-2">> NO_STACK_DETECTED</p>';
    }
    techStack.innerHTML = techHtml;

    // Quality Certification
    const quality = analysis.quality || {};
    const qualityBadge = document.getElementById('qualityBadge');

    if (qualityBadge) {
        // Reset classes
        qualityBadge.className = 'hidden inline-block mb-2 font-mono text-xs border px-2 py-1';

        if (quality.overall >= 90) {
            qualityBadge.classList.add('border-emerald-500', 'text-emerald-500', 'bg-emerald-900/10');
            qualityBadge.innerHTML = `★ CERTIFIED QUALITY (${quality.overall}%)`;
            qualityBadge.classList.remove('hidden');
        } else if (quality.overall >= 70) {
            qualityBadge.classList.add('border-amber-500', 'text-amber-500', 'bg-amber-900/10');
            qualityBadge.innerHTML = `⚠ GOOD QUALITY (${quality.overall}%)`;
            qualityBadge.classList.remove('hidden');
        } else if (quality.overall > 0) {
            qualityBadge.classList.add('border-red-500', 'text-red-500', 'bg-red-900/10');
            qualityBadge.innerHTML = `✖ LOW QUALITY (${quality.overall}%)`;
            qualityBadge.classList.remove('hidden');
        } else {
            qualityBadge.classList.add('hidden');
        }

        // Console hint
        if (quality.overall < 100 && quality.images?.issues?.length > 0) {
            log(`> WARN: Detected ${quality.images.issues.length} image optimization issues.`);
        }
    }

    // Meta Info
    const metaInfo = document.getElementById('metaInfo');
    const title = seoData.title?.content || 'N/A';
    const desc = seoData.description?.content || 'N/A';

    metaInfo.innerHTML = `
        <div class="mb-2">
            <span class="text-gray-600 block mb-1">> TITLE_TAG</span>
            <p class="text-white border-l-2 border-gray-800 pl-2">${title}</p>
        </div>
        <div class="mb-2">
            <span class="text-gray-600 block mb-1">> META_DESC</span>
            <p class="text-gray-400 border-l-2 border-gray-800 pl-2 line-clamp-2">${desc}</p>
        </div>
        <div class="grid grid-cols-2 gap-4 mt-4 border-t border-gray-800 pt-2">
            <div>
                <span class="text-gray-600">> INT_LINKS</span>: <span class="text-white">${seoData.links?.internal || 0}</span>
            </div>
            <div>
                <span class="text-gray-600">> EXT_LINKS</span>: <span class="text-white">${seoData.links?.external || 0}</span>
            </div>
        </div>
    `;

    // Social Meta (Open Graph)
    const socialMeta = document.getElementById('socialMeta');
    const og = analysis.social?.open_graph || {};
    if (Object.keys(og).length > 0) {
        let ogHtml = '';
        for (const [key, value] of Object.entries(og)) {
            if (key === 'image') {
                ogHtml += `<div class="mb-2 border border-gray-800 p-1"><img src="${value}" class="w-full h-32 object-cover grayscale opacity-70 hover:grayscale-0 hover:opacity-100 transition-all" onerror="this.style.display='none'"></div>`;
            } else {
                ogHtml += `<div class="mb-1"><span class="text-gray-600">og:${key}</span> <span class="text-gray-400 truncate block border-b border-gray-900 pb-1">${value}</span></div>`;
            }
        }
        socialMeta.innerHTML = ogHtml;
    } else {
        socialMeta.innerHTML = '<p class="text-gray-600">> NO_OG_TAGS_FOUND</p>';
    }

    // Performance Hints
    const hints = analysis.performance_hints || [];
    if (hints.length > 0) {
        document.getElementById('hintsSection').classList.remove('hidden');
        const hintsContainer = document.getElementById('performanceHints');
        hintsContainer.innerHTML = hints.map(hint => `
            <div class="mb-1 text-amber-500/80 border-l-2 border-amber-900/50 pl-2">
                > ${hint}
            </div>
        `).join('');
    }

    log(`> ANALYSIS_DONE: SEO Score ${score}/100`);
}

function resetUI() {
    document.getElementById('logs').innerHTML = '';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').innerText = '0%';
    document.getElementById('statusText').innerText = 'WAITING...';
    document.getElementById('resultAction').classList.add('hidden');
    document.getElementById('hintsSection').classList.add('hidden');

    // Reset score circle
    const scoreCircle = document.getElementById('scoreCircle');
    if (scoreCircle) {
        scoreCircle.style.strokeDashoffset = 283;
    }

    // Reset quality badge
    const qualityBadge = document.getElementById('qualityBadge');
    if (qualityBadge) qualityBadge.classList.add('hidden');
}

function updateProgress(percent, text) {
    const bar = document.getElementById('progressBar');
    if (bar) bar.style.width = `${percent}%`;

    const txt = document.getElementById('progressText');
    if (txt) txt.innerText = `${percent}%`;

    const sts = document.getElementById('statusText');
    if (sts) sts.innerText = text;

    // Log significant status changes
    const logs = document.getElementById('logs');
    const lastLog = logs.lastElementChild?.innerText;
    if (!lastLog?.includes(text)) {
        log(`> ${text}`);
    }
}

function log(message) {
    const logs = document.getElementById('logs');
    const entry = document.createElement('div');
    entry.className = "mb-1";
    entry.innerText = message;
    logs.appendChild(entry);
    logs.scrollTop = logs.scrollHeight;
}

function enableButton() {
    const btn = document.getElementById('cloneBtn');
    btn.disabled = false;
    btn.innerText = "INITIALIZE CLONE";
}

function showNotification(message, type) {
    // Simple notification
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Ideally update a status line in UI instead of toast for retro feel
    const statusText = document.getElementById('statusText');
    if (statusText) statusText.innerText = message.toUpperCase();
}

// Enter key to submit
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('targetUrl');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                startCloning();
            }
        });
        input.focus();
    }
});
