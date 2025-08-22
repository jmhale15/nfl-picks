class GitHubAPI {
    constructor() {
        // Replace these with your actual values
        this.owner = 'jmhale15';  // Replace with your GitHub username
        this.repo = 'nfl-picks';  // Your repo name
        this.token = null;
        
        this.baseURL = 'https://api.github.com';
        
        // Try to get token from localStorage (for testing)
        // In production, this would be handled more securely
        this.token = localStorage.getItem('github_token');
    }

    // Method to set token for testing
    setToken(token) {
        this.token = token;
        localStorage.setItem('github_token', token);
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
            // Try to get existing file to get SHA for update
            const existing = await this.getFile(filePath);
            const sha = existing ? existing.sha : null;
            
            await this.saveFile(
                filePath, 
                picksData, 
                `Update ${player}'s picks for Week ${week}`,
                sha
            );
            
            return { success: true };
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