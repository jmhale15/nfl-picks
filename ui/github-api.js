class GitHubAPI {
    constructor() {
        this.owner = null;
        this.repo = null;
        this.token = null;
        
        this.baseURL = 'https://api.github.com';
        
        // Initialize configuration
        this.initConfig();
    }

    async initConfig() {
        try {
            // Try to get config from Netlify function (production)
            const response = await fetch('/.netlify/functions/github-config');
            if (response.ok) {
                const config = await response.json();
                this.token = config.token;
                this.owner = config.owner;
                this.repo = config.repo;
                console.log('✅ GitHub config loaded from Netlify');
                return;
            }
        } catch (error) {
            console.log('Netlify function not available, trying localStorage...');
        }

        // Fallback to localStorage for local testing
        this.token = localStorage.getItem('github_token');
        this.owner = 'jmhale15';
        this.repo = 'nfl-picks';
        
        if (this.token) {
            console.log('✅ GitHub config loaded from localStorage (local testing)');
        } else {
            console.log('⚠️ No GitHub token found. Set via setToken() for local testing.');
        }
    }

    // Method to set token for local testing
    setToken(token) {
        this.token = token;
        localStorage.setItem('github_token', token);
        console.log('✅ GitHub token set for local testing');
    }

    // Check if GitHub is ready
    isReady() {
        return this.token && this.owner && this.repo;
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Authorization': `token ${this.token}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json',
            }
        };

        const response = await fetch(url, {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Unknown error' }));
            throw new Error(`GitHub API Error: ${error.message}`);
        }

        return response.json();
    }

    async getFile(path) {
        try {
            const endpoint = `/repos/${this.owner}/${this.repo}/contents/${path}`;
            const data = await this.makeRequest(endpoint);
            
            // Decode base64 content
            const content = atob(data.content);
            return {
                content: JSON.parse(content),
                sha: data.sha // Needed for updates
            };
        } catch (error) {
            if (error.message.includes('404')) {
                return null; // File doesn't exist
            }
            throw error;
        }
    }

    async saveFile(path, content, message = 'Update file', sha = null) {
        const endpoint = `/repos/${this.owner}/${this.repo}/contents/${path}`;
        
        const payload = {
            message: message,
            content: btoa(JSON.stringify(content, null, 2)), // Base64 encode
        };

        if (sha) {
            payload.sha = sha; // Required for updates
        }

        return await this.makeRequest(endpoint, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
    }

    async savePicks(player, week, picks) {
        const filePath = `picks/${player}.json`;
        const picksData = {
            player: player,
            week: week,
            picks: picks,
            saved_at: new Date().toISOString()
        };

        try {
            // Always try to get existing file first to get SHA
            let sha = null;
            try {
                const existing = await this.getFile(filePath);
                sha = existing ? existing.sha : null;
            } catch (error) {
                // File doesn't exist yet, that's fine
                console.log('File does not exist yet, creating new file');
            }
            
            const result = await this.saveFile(
                filePath, 
                picksData, 
                `Update ${player}'s picks for Week ${week}`,
                sha
            );
            
            return { success: true, result: result };
        } catch (error) {
            throw new Error(`Failed to save picks: ${error.message}`);
        }
    }

    async loadPicks(player, week) {
        try {
            const filePath = `picks/${player}.json`;
            const data = await this.getFile(filePath);
            
            if (!data) {
                return null; // No picks found
            }

            // Verify it's for the correct week
            if (data.content.week === week) {
                return data.content;
            }
            
            return null; // Wrong week
        } catch (error) {
            throw new Error(`Failed to load picks: ${error.message}`);
        }
    }

    async getAllPicks(week) {
        const players = ['jeff', 'teddy', 'will']; // Could also read from config
        const allPicks = {};

        for (const player of players) {
            try {
                const picks = await this.loadPicks(player, week);
                if (picks) {
                    allPicks[player] = picks;
                }
            } catch (error) {
                console.warn(`Could not load picks for ${player}:`, error.message);
            }
        }

        return allPicks;
    }

    async loadGames() {
        try {
            const data = await this.getFile('games.json');
            return data ? data.content : null;
        } catch (error) {
            throw new Error(`Failed to load games: ${error.message}`);
        }
    }
}