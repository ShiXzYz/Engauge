// Student Poll Logic with Knowledge Garden
(function() {
    // Use relative path since we're on the same domain
    const API_BASE = '';
    
    // DOM Elements
    const loadingDiv = document.getElementById('loading');
    const pollContent = document.getElementById('poll-content');
    const submittedView = document.getElementById('submitted-view');
    const questionText = document.getElementById('question-text');
    const choicesContainer = document.getElementById('choices-container');
    const xpMessage = document.getElementById('xp-message');
    const plantVisual = document.getElementById('plant-visual');
    const plantLevelSpan = document.getElementById('plant-level');
    const totalXpSpan = document.getElementById('total-xp');

    // Initialize
    loadPoll();

    function loadPoll() {
        fetch(`${API_BASE}/api/active-poll/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('No active poll');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    loadingDiv.textContent = data.error;
                    return;
                }
                displayPoll(data);
            })
            .catch(error => {
                console.error('Failed to load poll:', error);
                loadingDiv.textContent = 'No active poll at the moment. Please wait for your instructor.';
            });
    }

    function displayPoll(poll) {
        loadingDiv.style.display = 'none';
        pollContent.style.display = 'block';
        pollContent.classList.add('fade-in');
        
        questionText.textContent = poll.question;
        
        // Clear previous choices
        choicesContainer.innerHTML = '';
        
        // Parse choices (handle both string and array formats)
        let choices = poll.choices;
        if (typeof choices === 'string') {
            try {
                choices = JSON.parse(choices);
            } catch (e) {
                choices = choices.split(',').map(c => c.trim());
            }
        }
        
        // Create buttons for each choice
        choices.forEach((choice, index) => {
            const button = document.createElement('button');
            button.className = 'choice-btn';
            button.textContent = choice;
            button.onclick = () => submitAnswer(poll.id, choice);
            choicesContainer.appendChild(button);
        });
    }

    function submitAnswer(pollId, choice) {
        // Disable all buttons to prevent double submission
        document.querySelectorAll('.choice-btn').forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        });

        fetch(`${API_BASE}/api/submit-answer/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ 
                poll_id: pollId,
                choice: choice 
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Award XP
                const currentXP = parseInt(localStorage.getItem('engauge_xp') || '0');
                const xpAward = data.xp_award || 10;
                const newXP = currentXP + xpAward;
                localStorage.setItem('engauge_xp', newXP);
                
                // Show success view
                showSubmittedView(newXP, xpAward);
            } else {
                alert('Failed to submit answer: ' + (data.error || 'Unknown error'));
                // Re-enable buttons
                document.querySelectorAll('.choice-btn').forEach(btn => {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                });
            }
        })
        .catch(error => {
            console.error('Failed to submit answer:', error);
            alert('Failed to submit answer. Please try again.');
            // Re-enable buttons
            document.querySelectorAll('.choice-btn').forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            });
        });
    }

    function showSubmittedView(totalXP, earnedXP) {
        pollContent.style.display = 'none';
        submittedView.style.display = 'block';
        submittedView.classList.add('fade-in');
        
        xpMessage.textContent = `+${earnedXP} XP earned! 🌱`;
        totalXpSpan.textContent = totalXP;
        
        // Update garden
        updateGarden(totalXP);
    }

    function updateGarden(xp) {
        // Calculate plant level (0-4)
        const level = Math.min(Math.floor(xp / 50), 4);
        
        plantLevelSpan.textContent = level;
        
        // Update plant visual
        const previousLevel = parseInt(localStorage.getItem('engauge_plant_level') || '0');
        plantVisual.className = `plant-stage-${level}`;
        
        // Celebration on level up
        if (level > previousLevel) {
            celebrateLevelUp();
            localStorage.setItem('engauge_plant_level', level);
        }
    }

    function celebrateLevelUp() {
        // Simple celebration effect
        plantVisual.style.animation = 'bounce 0.6s';
        
        // Show level up message
        const levelUpMsg = document.createElement('div');
        levelUpMsg.textContent = '🎉 Your garden grew!';
        levelUpMsg.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #48bb78;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: bold;
            z-index: 1000;
            animation: fadeIn 0.3s;
        `;
        document.body.appendChild(levelUpMsg);
        
        setTimeout(() => {
            plantVisual.style.animation = '';
            levelUpMsg.remove();
        }, 2000);
    }

    function getCSRFToken() {
        // Get CSRF token from cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Show current XP and level on page load (if student has visited before)
    window.addEventListener('DOMContentLoaded', function() {
        const currentXP = parseInt(localStorage.getItem('engauge_xp') || '0');
        const currentLevel = Math.min(Math.floor(currentXP / 50), 4);
        
        if (currentXP > 0) {
            console.log(`Welcome back! Current XP: ${currentXP}, Level: ${currentLevel}`);
        }
    });
})();