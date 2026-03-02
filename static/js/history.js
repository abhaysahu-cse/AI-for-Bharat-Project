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

function openScheduler(id, topic) {
    localStorage.setItem('selectedContentId', id);
    localStorage.setItem('selectedContentTopic', topic);
    window.location.href = '/scheduler/';
}

document.addEventListener('DOMContentLoaded', fetchHistory);
