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
        await new Promise(resolve => setTimeout(resolve, 1500));
        btn.innerText = 'Enhancing Prompt...';
        await new Promise(resolve => setTimeout(resolve, 1500));

        const enhancedPrompt = `Cinematic wide-angle shot of ${topic}, vibrant hyper-realistic textures, volumetric lighting, slow camera pan, 8k resolution.`;

        btn.innerText = 'Generating Video (AI Simulation)...';
        await new Promise(resolve => setTimeout(resolve, 3000));

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
