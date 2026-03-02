// Authentication (PURE FRONTEND SIMULATION)
async function handleSignup(event) {
    event.preventDefault();
    alert('Signup successful (Simulation)! Redirecting to login.');
    window.location.href = 'login.html';
}

async function handleLogin(event) {
    event.preventDefault();
    alert('Login successful (Simulation)! Redirecting to dashboard.');
    window.location.href = 'index.html';
}

async function handleLogout() {
    alert('Logged out (Simulation).');
    window.location.href = 'login.html';
}

// Content Generation (PURE FRONTEND MOCK)
async function generateContent(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button');
    const originalText = btn.innerText;

    btn.innerText = 'Generating (Local AI)...';
    btn.disabled = true;

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    const { topic, content_type, language } = data;

    try {
        // Simulate local "processing" delay
        await new Promise(resolve => setTimeout(resolve, 2000));

        let text = "";
        if (content_type === "YouTube Script") {
            text = `[CAPTION]\nExploring ${topic}: A BharatAI Original\n\n[SCENES]\nScene 1: Introduction to ${topic} in ${language}.\nScene 2: Diving deep into current trends.\nScene 3: Future projections and impact.\nScene 4: Final thoughts.\n\n[STORYBOARD]\nScene 1: Epic drone shot of technological landscape.\nScene 2: Animated charts showing data.\nScene 3: Interview style setup.\nScene 4: Closing logo animation.\n\n[MUSIC]\nUpbeat, inspiring cinematic background score.`;
        } else {
            text = `[CAPTION]\n${topic} Insight\n\n[CONTENT]\nThis is a locally generated ${content_type} about "${topic}" in ${language}. It highlights the most important aspects for a professional audience.\n\n- Key Point 1: Relevance in modern ${language} context.\n- Key Point 2: Strategic advantages.\n- Key Point 3: Implementation guide.`;
        }

        // Parsing sections (same logic as before)
        const sections = {
            caption: text.match(/\[CAPTION\]([\s\S]*?)(\[|$)/i),
            content: text.match(/\[CONTENT\]([\s\S]*?)(\[|$)/i),
            scenes: text.match(/\[SCENES\]([\s\S]*?)(\[|$)/i),
            storyboard: text.match(/\[STORYBOARD\]([\s\S]*?)(\[|$)/i),
            music: text.match(/\[MUSIC\]([\s\S]*?)(\[|$)/i)
        };

        // Display logic
        if (sections.caption) {
            document.getElementById('captionContent').innerText = sections.caption[1].trim();
            document.getElementById('captionBox').style.display = 'block';
        }

        if (sections.scenes || sections.storyboard || sections.music) {
            document.getElementById('mainContentBox').style.display = 'none';
            document.getElementById('scriptExtras').style.display = 'block';
            if (sections.scenes) document.getElementById('scenesContent').innerText = sections.scenes[1].trim();
            if (sections.storyboard) document.getElementById('storyboardContent').innerText = sections.storyboard[1].trim();
            if (sections.music) document.getElementById('musicContent').innerText = sections.music[1].trim();
        } else {
            document.getElementById('scriptExtras').style.display = 'none';
            document.getElementById('mainContentBox').style.display = 'block';
            document.getElementById('mainContentLabel').innerText = 'Generated Content';
            const cleanContent = sections.content ? sections.content[1].trim() : text;
            document.getElementById('outputArea').innerText = cleanContent;
        }

        // Note: Saving to history still requires a backend call, but we can bypass it for pure frontend "viewing"
        document.getElementById('saveSection').style.display = 'none'; // Hide save for pure frontend demo
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// History
async function fetchHistory() {
    const response = await fetch('/api/history/', { headers: headers });
    if (response.ok) {
        const history = await response.json();
        const container = document.getElementById('historyContainer');
        container.innerHTML = history.map((item, index) => `
            <div class="history-item" style="animation: fadeInUp 0.8s ease-out ${index * 0.1}s both;">
                <h3>${item.topic}</h3>
                <p>
                    <span class="history-tag">${item.content_type}</span>
                    <span class="history-tag">${item.language}</span>
                    <small>${new Date(item.created_at).toLocaleDateString()}</small>
                </p>
                <div class="output-area" style="margin-top: 1rem; max-height: 150px; overflow-y: auto;">
                    ${item.generated_text}
                </div>
                <button class="btn-secondary" onclick="openScheduler(${item.id}, '${item.topic}')">Schedule This</button>
            </div>
        `).join('');
    }
}

// Scheduler
function openScheduler(id, topic) {
    localStorage.setItem('selectedContentId', id);
    localStorage.setItem('selectedContentTopic', topic);
    window.location.href = '/scheduler/';
}

async function handleSchedule(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    data.content_id = localStorage.getItem('selectedContentId');

    const response = await fetch('/api/schedule/', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data)
    });

    if (response.ok) {
        alert('Content scheduled successfully!');
        window.location.href = '/history/';
    } else {
        alert('Failed to schedule content.');
    }
}

// Video Generation (PURE FRONTEND MOCK)
async function handleVideoGenerate(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button');
    const originalText = btn.innerText;

    btn.disabled = true;
    btn.innerText = 'Analyzing Topic...';

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    const topic = data.topic;

    try {
        // UI simulation delays
        await new Promise(resolve => setTimeout(resolve, 1500));
        btn.innerText = 'Enhancing Prompt...';
        await new Promise(resolve => setTimeout(resolve, 1500));

        const enhancedPrompt = `Cinematic wide-angle shot of ${topic}, vibrant hyper-realistic textures, volumetric lighting, slow camera pan, 8k resolution.`;

        btn.innerText = 'Generating Video (AI Simulation)...';
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Result display
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.src = "https://www.w3schools.com/html/mov_bbb.mp4";
        document.getElementById('videoSection').style.display = 'block';

        document.getElementById('enhancedPromptText').innerText = enhancedPrompt;
        document.getElementById('enhancedPromptSection').style.display = 'block';

        document.getElementById('videoSection').scrollIntoView({ behavior: 'smooth' });
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Initialization based on page
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    if (path.includes('history')) fetchHistory();
    if (path.includes('scheduler')) {
        const topic = localStorage.getItem('selectedContentTopic');
        if (topic) document.getElementById('contentTopicDisplay').innerText = topic;
    }
});
