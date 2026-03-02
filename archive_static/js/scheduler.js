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

document.addEventListener('DOMContentLoaded', () => {
    const topic = localStorage.getItem('selectedContentTopic');
    if (topic) document.getElementById('contentTopicDisplay').innerText = topic;
});
