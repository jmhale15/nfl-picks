class NFLPicks {
    constructor() {
        this.games = [];
        this.players = [];
        this.currentPlayer = '';
        this.picks = {};
        this.github = new GitHubAPI();
        
        this.init();
    }

    async init() {
        try {
            // Wait for GitHub config to load
            await this.github.initConfig();
            
            await this.loadGames();
            this.setupEventListeners();
            this.renderPlayerSelect();
            this.renderGames();
        } catch (error) {
            this.showMessage('Error loading games: ' + error.message, 'error');
        }
    }

    async loadGames() {
        try {
            // Try to load from GitHub first (if available)
            if (this.github.isReady()) {
                const data = await this.github.loadGames();
                if (data) {
                    this.games = data.games || [];
                    this.players = data.players || [];
                    this.currentWeek = data.week || 1;
                    this.weekStart = data.week_start || '';
                    
                    // Update week display
                    document.getElementById('week-display').textContent = 
                        `Week ${this.currentWeek} - ${new Date(this.weekStart).toLocaleDateString()}`;
                    return;
                }
            }
            
            // Fallback to local fetch
            const response = await fetch('../games.json');
            if (!response.ok) {
                throw new Error('Could not load games data');
            }
            
            const data = await response.json();
            this.games = data.games || [];
            this.players = data.players || [];
            this.currentWeek = data.week || 1;
            this.weekStart = data.week_start || '';
            
            // Update week display
            document.getElementById('week-display').textContent = 
                `Week ${this.currentWeek} - ${new Date(this.weekStart).toLocaleDateString()}`;
                
        } catch (error) {
            // For local testing, show mock data
            console.log('Loading mock data for testing...');
            this.loadMockData();
        }
    }

    loadMockData() {
        // Mock data for testing when games.json is empty or unavailable
        this.games = [
            {
                id: "KC_BAL_2025-09-05 20:20",
                week: 1,
                game_date: "2025-09-05 20:20",
                away_team: "Kansas City",
                home_team: "Baltimore",
                away_odds: "-110",
                home_odds: "-110",
                over_under: "47.5"
            },
            {
                id: "BUF_LAR_2025-09-08 13:00",
                week: 1,
                game_date: "2025-09-08 13:00",
                away_team: "Buffalo",
                home_team: "Los Angeles",
                away_odds: "+120",
                home_odds: "-140",
                over_under: "44.0"
            }
        ];
        this.players = ["jeff", "teddy", "will"];
        this.currentWeek = 1;
        this.weekStart = "2025-09-05";
        
        document.getElementById('week-display').textContent = 
            `Week ${this.currentWeek} - ${new Date(this.weekStart).toLocaleDateString()} (Mock Data)`;
    }

    setupEventListeners() {
        const playerSelect = document.getElementById('player-select');
        const saveButton = document.getElementById('save-picks');
        const loadButton = document.getElementById('load-picks');

        playerSelect.addEventListener('change', (e) => {
            this.currentPlayer = e.target.value;
            this.toggleButtons();
            if (this.currentPlayer) {
                this.loadPlayerPicks();
            }
        });

        saveButton.addEventListener('click', () => this.savePicks());
        loadButton.addEventListener('click', () => this.loadPlayerPicks());
    }

    renderPlayerSelect() {
        const select = document.getElementById('player-select');
        select.innerHTML = '<option value="">Select your name...</option>';
        
        this.players.forEach(player => {
            const option = document.createElement('option');
            option.value = player;
            option.textContent = player.charAt(0).toUpperCase() + player.slice(1);
            select.appendChild(option);
        });
    }

    renderGames() {
        const container = document.getElementById('games-container');
        
        if (this.games.length === 0) {
            container.innerHTML = `
                <div class="loading">
                    <p>No games available yet for this week.</p>
                    <p style="font-size: 0.9rem; margin-top: 10px; color: #888;">
                        Games will appear here once the week's lines are published.
                    </p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.games.map(game => this.renderGameCard(game)).join('');
        this.attachPickListeners();
    }

    renderGameCard(game) {
        const gameDate = new Date(game.game_date);
        const formattedDate = gameDate.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });

        return `
            <div class="game-card" data-game-id="${game.id}">
                <div class="game-header">
                    <div class="teams">${game.away_team} @ ${game.home_team}</div>
                    <div class="game-date">${formattedDate}</div>
                </div>
                
                <div class="picks-section">
                    <div class="pick-group">
                        <h4>Spread Pick</h4>
                        <div class="spread-info">
                            ${game.away_team} ${game.away_odds} | ${game.home_team} ${game.home_odds}
                        </div>
                        <div class="pick-options">
                            <div class="pick-option" data-pick-type="spread" data-pick-value="${game.away_team}">
                                ${game.away_team}
                            </div>
                            <div class="pick-option" data-pick-type="spread" data-pick-value="${game.home_team}">
                                ${game.home_team}
                            </div>
                        </div>
                    </div>
                    
                    <div class="pick-group">
                        <h4>Over/Under Pick</h4>
                        <div class="over-under-info">Total: ${game.over_under}</div>
                        <div class="pick-options">
                            <div class="pick-option" data-pick-type="total" data-pick-value="over">
                                Over ${game.over_under}
                            </div>
                            <div class="pick-option" data-pick-type="total" data-pick-value="under">
                                Under ${game.over_under}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    attachPickListeners() {
        document.querySelectorAll('.pick-option').forEach(option => {
            option.addEventListener('click', (e) => {
                if (!this.currentPlayer) {
                    this.showMessage('Please select your name first!', 'error');
                    return;
                }

                const gameCard = e.target.closest('.game-card');
                const gameId = gameCard.dataset.gameId;
                const pickType = e.target.dataset.pickType;
                const pickValue = e.target.dataset.pickValue;

                // Clear other selections in this pick group
                const pickGroup = e.target.closest('.pick-group');
                pickGroup.querySelectorAll('.pick-option').forEach(opt => {
                    opt.classList.remove('selected');
                });

                // Select this option
                e.target.classList.add('selected');

                // Store the pick
                if (!this.picks[gameId]) {
                    this.picks[gameId] = {};
                }
                this.picks[gameId][pickType] = pickValue;

                this.showMessage('Pick updated! Don\'t forget to save.', 'info');
            });
        });
    }

    toggleButtons() {
        const saveButton = document.getElementById('save-picks');
        const loadButton = document.getElementById('load-picks');
        
        const enabled = this.currentPlayer !== '';
        saveButton.disabled = !enabled;
        loadButton.disabled = !enabled;
    }

    async savePicks() {
        if (!this.currentPlayer) return;

        try {
            this.showMessage('Saving picks...', 'info');
            
            if (this.github.token) {
                // Save to GitHub
                await this.github.savePicks(this.currentPlayer, this.currentWeek, this.picks);
                this.showMessage('Picks saved to GitHub! ✅', 'success');
            } else {
                // Fallback to localStorage for local testing
                const picksData = {
                    player: this.currentPlayer,
                    week: this.currentWeek,
                    picks: this.picks,
                    saved_at: new Date().toISOString()
                };

                localStorage.setItem(`picks_${this.currentPlayer}_week_${this.currentWeek}`, 
                    JSON.stringify(picksData));
                this.showMessage('Picks saved locally! ✅ (GitHub not configured)', 'success');
            }
        } catch (error) {
            this.showMessage('Error saving picks: ' + error.message, 'error');
        }
    }

    async loadPlayerPicks() {
        if (!this.currentPlayer) return;

        try {
            this.showMessage('Loading picks...', 'info');
            
            let picksData = null;
            
            if (this.github.token) {
                // Load from GitHub
                picksData = await this.github.loadPicks(this.currentPlayer, this.currentWeek);
            } else {
                // Fallback to localStorage
                const saved = localStorage.getItem(`picks_${this.currentPlayer}_week_${this.currentWeek}`);
                if (saved) {
                    picksData = JSON.parse(saved);
                }
            }
            
            if (picksData) {
                this.picks = picksData.picks || {};
                this.applyPicksToUI();
                this.showMessage('Previous picks loaded! ✅', 'success');
            } else {
                this.showMessage('No previous picks found for this week.', 'info');
            }
        } catch (error) {
            this.showMessage('Error loading picks: ' + error.message, 'error');
        }
    }

    applyPicksToUI() {
        // Clear all selections
        document.querySelectorAll('.pick-option').forEach(opt => {
            opt.classList.remove('selected');
        });

        // Apply saved picks
        Object.entries(this.picks).forEach(([gameId, gamePicks]) => {
            const gameCard = document.querySelector(`[data-game-id="${gameId}"]`);
            if (!gameCard) return;

            Object.entries(gamePicks).forEach(([pickType, pickValue]) => {
                const option = gameCard.querySelector(
                    `[data-pick-type="${pickType}"][data-pick-value="${pickValue}"]`
                );
                if (option) {
                    option.classList.add('selected');
                }
            });
        });
    }

    showMessage(message, type = 'info') {
        const messageEl = document.getElementById('status-message');
        messageEl.textContent = message;
        messageEl.className = `status-message ${type}`;
        
        // Auto-hide after 3 seconds for non-error messages
        if (type !== 'error') {
            setTimeout(() => {
                messageEl.textContent = '';
                messageEl.className = 'status-message';
            }, 3000);
        }
    }
}

// Initialize the app when page loads
document.addEventListener('DOMContentLoaded', () => {
    new NFLPicks();
});