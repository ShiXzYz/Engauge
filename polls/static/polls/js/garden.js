// Knowledge Garden - 3x3 Grid System with Drag & Drop
(function() {
    // Constants
    const GRID_SIZE = 6; // 3x3 grid
    const MAX_STAGE = 4; // 5 stages total: 0 (empty) to 4 (blooming)
    const XP_PER_ANSWER = 10;
    const XP_TO_WATER = 50; // Need 50 XP to water a plant

    // Plant stage names and emojis (fallback)
    const STAGE_INFO = {
        0: { name: 'Empty Pot', emoji: '🪴', file: 'plant-stage-0.png' },
        1: { name: 'Planted Seed', emoji: '🌱', file: 'plant-stage-1.png' },
        2: { name: 'Sprout', emoji: '🌿', file: 'plant-stage-2.png' },
        3: { name: 'Seedling', emoji: '☘️', file: 'plant-stage-3.png' },
        4: { name: 'Blooming', emoji: '🌸', file: 'plant-stage-4.png' }
    };

    // DOM Elements
    const plantGrid = document.getElementById('plant-grid');
    const waterBarFill = document.getElementById('water-bar-fill');
    const currentWaterSpan = document.getElementById('current-water');
    const totalXpSpan = document.getElementById('total-xp');
    const bloomingCountSpan = document.getElementById('blooming-count');
    const readyMessage = document.getElementById('ready-message');
    const particleContainer = document.getElementById('particle-container');

    // Seed inventory state
    let seedsUsed = 0;
    const MAX_SEEDS = 3;

    // State
    let gardenState = {
        plants: new Array(GRID_SIZE).fill(null), // null = no plant, 0-5 = growth stage
        currentXP: 0,
        totalXP: 0,
        canWater: false
    };

    // Initialize garden on load
    function initGarden() {
        loadGardenState();
        createPlantGrid();
        updateUI();
        setupDragAndDrop();
        checkForNewXP(); // Check if XP was added from poll
    }

    // Load state from localStorage
    function loadGardenState() {
        const saved = localStorage.getItem('engauge_garden_state');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                gardenState.plants = parsed.plants || new Array(GRID_SIZE).fill(null);
                seedsUsed = parsed.seedsUsed || 0;
            } catch (e) {
                console.warn('Failed to load garden state:', e);
            }
        }

        // Load XP
        gardenState.totalXP = parseInt(localStorage.getItem('engauge_xp') || '0');
        gardenState.currentXP = parseInt(localStorage.getItem('engauge_current_water_xp') || '0');
        gardenState.canWater = gardenState.currentXP >= XP_TO_WATER;
    }

    // Save state to localStorage
    function saveGardenState() {
        localStorage.setItem('engauge_garden_state', JSON.stringify({
            plants: gardenState.plants,
            seedsUsed: seedsUsed
        }));
        localStorage.setItem('engauge_current_water_xp', gardenState.currentXP.toString());
    }

    // Check for new XP from polls
    function checkForNewXP() {
        const totalXP = parseInt(localStorage.getItem('engauge_xp') || '0');
        if (totalXP > gardenState.totalXP) {
            const gained = totalXP - gardenState.totalXP;
            gardenState.totalXP = totalXP;
            gardenState.currentXP = Math.min(gardenState.currentXP + gained, XP_TO_WATER);
            gardenState.canWater = gardenState.currentXP >= XP_TO_WATER;
            saveGardenState();
            updateUI();

            // Show XP gain notification
            showNotification(`+${gained} XP earned! 💧`);
        }
    }

    // Create 3x3 plant grid
    function createPlantGrid() {
        plantGrid.innerHTML = '';

        for (let i = 0; i < GRID_SIZE; i++) {
            const cell = document.createElement('div');
            cell.className = 'plant-cell';
            cell.dataset.index = i;

            const stage = gardenState.plants[i];
            if (stage === null) {
                cell.classList.add('empty');
            } else {
                cell.classList.add(`stage-${stage}`);
                if (stage === MAX_STAGE) {
                    cell.classList.add('blooming');
                }
                renderPlant(cell, stage);
            }

            // Click to water (if can water and plant exists and not max)
            cell.addEventListener('click', () => handlePlantClick(i));

            plantGrid.appendChild(cell);
        }
    }

    // Render plant sprite
    function renderPlant(cell, stage) {
        cell.innerHTML = '';

        const info = STAGE_INFO[stage];
        const img = document.createElement('img');
        img.className = 'plant-sprite';
        img.src = `/static/polls/images/plants/${info.file}`;
        img.alt = info.name;

        // Fallback to emoji if image fails
        img.onerror = function() {
            this.style.display = 'none';
            const placeholder = document.createElement('div');
            placeholder.className = 'plant-placeholder';
            placeholder.textContent = info.emoji;
            cell.appendChild(placeholder);
        };

        cell.appendChild(img);
    }

    // Handle plant click (watering)
    function handlePlantClick(index) {
        const stage = gardenState.plants[index];

        // Can only water if: have enough XP, plant exists, and not fully grown
        if (!gardenState.canWater || stage === null || stage >= MAX_STAGE) {
            if (stage !== null && stage < MAX_STAGE && !gardenState.canWater) {
                showNotification('Need 50 XP to water! Answer more questions! 💧');
            }
            return;
        }

        // Water the plant (grow it)
        growPlant(index);
    }

    // Grow plant to next stage
    function growPlant(index) {
        const currentStage = gardenState.plants[index];
        const newStage = Math.min(currentStage + 1, MAX_STAGE);

        gardenState.plants[index] = newStage;
        gardenState.currentXP = 0; // Reset water can
        gardenState.canWater = false;

        saveGardenState();

        // Visual update
        const cell = plantGrid.children[index];
        cell.classList.add('growing');
        cell.classList.remove(`stage-${currentStage}`);
        cell.classList.add(`stage-${newStage}`);

        if (newStage === MAX_STAGE) {
            cell.classList.add('blooming');
        }

        renderPlant(cell, newStage);

        // Particle burst
        createParticleBurst(cell);

        // Remove growing animation after it completes
        setTimeout(() => {
            cell.classList.remove('growing');
        }, 800);

        updateUI();

        // Check if all plants are blooming
        if (gardenState.plants.filter(s => s === MAX_STAGE).length === GRID_SIZE) {
            celebrateFullGarden();
        }
    }

    // Setup drag and drop for seed planting
    function setupDragAndDrop() {
        // Seed packet drag events (for all seed packets)
        const seedPackets = document.querySelectorAll('.seed-packet');

        seedPackets.forEach(packet => {
            packet.addEventListener('dragstart', (e) => {
                // Check if seed is already used
                if (packet.classList.contains('used')) {
                    e.preventDefault();
                    return;
                }

                // Check if we've used all seeds
                if (seedsUsed >= MAX_SEEDS) {
                    e.preventDefault();
                    showNotification('All seeds used! 🌱');
                    return;
                }

                packet.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'copy';
                e.dataTransfer.setData('text/plain', 'seed');
            });

            packet.addEventListener('dragend', () => {
                packet.classList.remove('dragging');
                // Remove drag-over class from all cells
                document.querySelectorAll('.plant-cell').forEach(cell => {
                    cell.classList.remove('drag-over');
                });
            });
        });

        // Plant cell drop targets
        plantGrid.addEventListener('dragover', (e) => {
            e.preventDefault();
            const cell = e.target.closest('.plant-cell');
            if (cell && cell.classList.contains('empty')) {
                e.dataTransfer.dropEffect = 'copy';
                cell.classList.add('drag-over');
            }
        });

        plantGrid.addEventListener('dragleave', (e) => {
            const cell = e.target.closest('.plant-cell');
            if (cell) {
                cell.classList.remove('drag-over');
            }
        });

        plantGrid.addEventListener('drop', (e) => {
            e.preventDefault();
            const cell = e.target.closest('.plant-cell');
            if (cell && cell.classList.contains('empty')) {
                const index = parseInt(cell.dataset.index);
                plantSeed(index);
                cell.classList.remove('drag-over');
            }
        });
    }

    // Plant a seed in empty pot
    function plantSeed(index) {
        if (gardenState.plants[index] !== null) return;

        // Check if we have seeds left
        if (seedsUsed >= MAX_SEEDS) {
            showNotification('All seeds used! 🌱');
            return;
        }

        gardenState.plants[index] = 0; // Stage 0 = empty pot (ready for seed)
        // Actually plant it (go to stage 1)
        gardenState.plants[index] = 1; // Stage 1 = planted seed
        seedsUsed++; // Use one seed

        saveGardenState();

        const cell = plantGrid.children[index];
        cell.classList.remove('empty');
        cell.classList.add('stage-1', 'growing');

        renderPlant(cell, 1);

        // Small particle effect
        createParticleBurst(cell, 5);

        setTimeout(() => {
            cell.classList.remove('growing');
        }, 800);

        updateUI();

        const remainingSeeds = MAX_SEEDS - seedsUsed;
        if (remainingSeeds > 0) {
            showNotification(`Seed planted! ${remainingSeeds} seed${remainingSeeds > 1 ? 's' : ''} left. 🌱`);
        } else {
            showNotification('Last seed planted! Water your plants to grow them! 🌱💧');
        }
    }

    // Update all UI elements
    function updateUI() {
        // Total XP
        totalXpSpan.textContent = gardenState.totalXP;

        // Water bar level
        const waterPercentage = (gardenState.currentXP / XP_TO_WATER) * 100;
        waterBarFill.style.width = waterPercentage + '%';
        currentWaterSpan.textContent = gardenState.currentXP;

        // Add 'full' class when at 100%
        if (gardenState.canWater) {
            waterBarFill.classList.add('full');
        } else {
            waterBarFill.classList.remove('full');
        }

        // Ready to water message
        if (gardenState.canWater) {
            readyMessage.style.display = 'block';
            // Highlight plants that can be watered
            gardenState.plants.forEach((stage, i) => {
                if (stage !== null && stage < MAX_STAGE) {
                    plantGrid.children[i].classList.add('can-water');
                }
            });
        } else {
            readyMessage.style.display = 'none';
            document.querySelectorAll('.plant-cell').forEach(cell => {
                cell.classList.remove('can-water');
            });
        }

        // Blooming count
        const bloomingCount = gardenState.plants.filter(s => s === MAX_STAGE).length;
        bloomingCountSpan.textContent = bloomingCount;

        // Update seed inventory display
        updateSeedInventory();
    }

    // Update seed inventory UI
    function updateSeedInventory() {
        const seedPackets = document.querySelectorAll('.seed-packet');
        seedPackets.forEach((packet, index) => {
            if (index < seedsUsed) {
                packet.classList.add('used');
                packet.draggable = false;
            } else {
                packet.classList.remove('used');
                packet.draggable = true;
            }
        });
    }

    // Create particle burst effect
    function createParticleBurst(element, count = 12) {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const particles = ['✨', '💧', '🌟', '⭐'];

        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.textContent = particles[Math.floor(Math.random() * particles.length)];

            const angle = (Math.PI * 2 * i) / count;
            const distance = 50 + Math.random() * 30;
            const tx = Math.cos(angle) * distance;
            const ty = Math.sin(angle) * distance;

            particle.style.left = centerX + 'px';
            particle.style.top = centerY + 'px';
            particle.style.setProperty('--tx', tx + 'px');
            particle.style.setProperty('--ty', ty + 'px');

            particleContainer.appendChild(particle);

            setTimeout(() => particle.remove(), 1500);
        }
    }

    // Show notification message
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 32px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 18px;
            z-index: 10000;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            animation: fadeInScale 0.3s ease;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Celebrate full garden
    function celebrateFullGarden() {
        const celebration = document.createElement('div');
        celebration.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: #654321;
            padding: 40px 60px;
            border-radius: 20px;
            font-size: 36px;
            font-weight: bold;
            z-index: 10001;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
            text-align: center;
            animation: fadeInScale 0.5s ease;
        `;
        celebration.innerHTML = '🎉🌸🎉<br>Garden Complete!<br>🎉🌸🎉';

        document.body.appendChild(celebration);

        // Massive particle burst
        for (let i = 0; i < 50; i++) {
            setTimeout(() => {
                const x = window.innerWidth * Math.random();
                const y = window.innerHeight * Math.random();
                const fakeEl = { getBoundingClientRect: () => ({ left: x, top: y, width: 0, height: 0 }) };
                createParticleBurst(fakeEl, 8);
            }, i * 100);
        }

        setTimeout(() => {
            celebration.style.animation = 'fadeOut 0.5s ease';
            setTimeout(() => celebration.remove(), 500);
        }, 5000);
    }

    // DEBUG: Press 'g' to cycle through plant stages for testing
    let debugPlantIndex = 0;

    document.addEventListener('keydown', function(e) {
        if (e.key === 'g' || e.key === 'G') {
            // Find next plant to debug
            let found = false;
            for (let i = 0; i < GRID_SIZE; i++) {
                debugPlantIndex = (debugPlantIndex + 1) % GRID_SIZE;
                if (gardenState.plants[debugPlantIndex] !== null) {
                    found = true;
                    break;
                }
            }

            if (!found) {
                showNotification('No plants to cycle! Plant some seeds first.');
                return;
            }

            // Cycle to next stage
            const currentStage = gardenState.plants[debugPlantIndex];
            const newStage = (currentStage + 1) % (MAX_STAGE + 1);

            // If cycling back to 0, remove plant instead
            if (newStage === 0) {
                gardenState.plants[debugPlantIndex] = null;
                const cell = plantGrid.children[debugPlantIndex];
                cell.className = 'plant-cell empty';
                cell.innerHTML = '';
                cell.dataset.index = debugPlantIndex;
                showNotification(`🔧 DEBUG: Plant ${debugPlantIndex + 1} removed`);
            } else {
                gardenState.plants[debugPlantIndex] = newStage;
                const cell = plantGrid.children[debugPlantIndex];
                cell.classList.remove(`stage-${currentStage}`);
                cell.classList.add(`stage-${newStage}`);
                if (newStage === MAX_STAGE) {
                    cell.classList.add('blooming');
                }
                renderPlant(cell, newStage);
                showNotification(`Plant ${debugPlantIndex + 1} → Stage ${newStage}`);
            }

            saveGardenState();
            updateUI();
        } else if (e.key === 'x' || e.key === 'X') {
            // DEBUG: Add 10 XP
            gardenState.totalXP += XP_PER_ANSWER;
            gardenState.currentXP = Math.min(gardenState.currentXP + XP_PER_ANSWER, XP_TO_WATER);
            gardenState.canWater = gardenState.currentXP >= XP_TO_WATER;
            localStorage.setItem('engauge_xp', gardenState.totalXP.toString());
            saveGardenState();
            updateUI();
            showNotification('QUESTION CORRECT: +10 XP added');
        }
    });

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInScale {
            from {
                opacity: 0;
                transform: translate(-50%, -50%) scale(0.8);
            }
            to {
                opacity: 1;
                transform: translate(-50%, -50%) scale(1);
            }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    // Reset garden button
    function setupResetButton() {
        const resetBtn = document.getElementById('reset-garden-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to reset your entire garden? This will delete all plants and XP!')) {
                    // Clear all localStorage
                    localStorage.removeItem('engauge_garden_state');
                    localStorage.removeItem('engauge_xp');
                    localStorage.removeItem('engauge_current_water_xp');
                    localStorage.removeItem('engauge_plant_level');

                    // Reload page
                    location.reload();
                }
            });
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initGarden();
            setupResetButton();
        });
    } else {
        initGarden();
        setupResetButton();
    }

    // Refresh garden every 3 seconds (check for new XP from polls)
    setInterval(() => {
        checkForNewXP();
    }, 3000);

})();
