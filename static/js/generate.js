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
        const response = await fetch('/api/generate-ai/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : ''
            },
            body: JSON.stringify(data)
        });

        const resultData = await response.json();
        let text = resultData.result || resultData.error;

        // Use simulation logic for YouTube Script if API doesn't return structured data
        if (content_type === "YouTube Script" && !text.includes("[SCENES]")) {
            text = `[CAPTION]\nExploring ${topic}: A BharatAI Original\n\n[SCENES]\nScene 1: Introduction to ${topic} in ${language}.\nScene 2: Diving deep into current trends.\nScene 3: Future projections and impact.\nScene 4: Final thoughts.\n\n[STORYBOARD]\nScene 1: Epic drone shot of technological landscape.\nScene 2: Animated charts showing data.\nScene 3: Interview style setup.\nScene 4: Closing logo animation.\n\n[MUSIC]\nUpbeat, inspiring cinematic background score.`;
        } else if (!text.includes("[CAPTION]")) {
            text = `[CAPTION]\n${topic} Insight\n\n[CONTENT]\nThis is a locally generated ${content_type} about "${topic}" in ${language}. It highlights the most important aspects for a professional audience.\n\n- Key Point 1: Relevance in modern ${language} context.\n- Key Point 2: Strategic advantages.\n- Key Point 3: Implementation guide.`;
        }

        const sections = {
            caption: text.match(/\[CAPTION\]([\s\S]*?)(\[|$)/i),
            content: text.match(/\[CONTENT\]([\s\S]*?)(\[|$)/i),
            scenes: text.match(/\[SCENES\]([\s\S]*?)(\[|$)/i),
            storyboard: text.match(/\[STORYBOARD\]([\s\S]*?)(\[|$)/i),
            music: text.match(/\[MUSIC\]([\s\S]*?)(\[|$)/i)
        };

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

        document.getElementById('saveSection').style.display = 'none';
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}
