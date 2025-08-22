import json
import os
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import requests

# Load environment variables
load_dotenv()

class NFLSheetsSync:
    def __init__(self):
        self.setup_google_sheets()
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPO_OWNER', 'jmhale15')
        self.repo_name = os.getenv('GITHUB_REPO_NAME', 'nfl-picks')
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
    def setup_google_sheets(self):
        """Setup Google Sheets API connection"""
        # Define the scope
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Load credentials from JSON file
        creds_file = 'google-credentials.json'
        if not os.path.exists(creds_file):
            print(f"❌ Google credentials file '{creds_file}' not found!")
            print("Please download your service account JSON file and name it 'google-credentials.json'")
            exit(1)
            
        creds = Credentials.from_service_account_file(creds_file, scopes=scope)
        self.gc = gspread.authorize(creds)
        
    def get_github_file(self, path):
        """Get a file from GitHub repo"""
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            # Decode base64 content
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            return json.loads(content)
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching {path}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {path}: {e}")
            return None
    
    def load_games_data(self):
        """Load games data from GitHub, with mock data fallback"""
        games_data = self.get_github_file('games.json')
        if not games_data or not games_data.get('games'):
            print("⚠️  No real games found in games.json, using mock data for testing...")
            
            # Use the same mock data as the website
            games_data = {
                "week": 1,
                "week_start": "2025-09-05",
                "generated_at": "2025-08-22T00:00:00.000Z",
                "players": ["jeff", "teddy", "will"],
                "games": [
                    {
                        "id": "KC_BAL_2025-09-05 20:20",
                        "week": 1,
                        "game_date": "2025-09-05 20:20",
                        "away_team": "Kansas City",
                        "home_team": "Baltimore",
                        "away_odds": "-110",
                        "home_odds": "-110",
                        "over_under": "47.5"
                    },
                    {
                        "id": "BUF_LAR_2025-09-08 13:00",
                        "week": 1,
                        "game_date": "2025-09-08 13:00",
                        "away_team": "Buffalo",
                        "home_team": "Los Angeles",
                        "away_odds": "+120",
                        "home_odds": "-140",
                        "over_under": "44.0"
                    }
                ]
            }
            
        return games_data
    
    def load_all_picks(self):
        """Load picks for all players from GitHub"""
        players = ['jeff', 'teddy', 'will']
        all_picks = {}
        
        for player in players:
            picks_data = self.get_github_file(f'picks/{player}.json')
            if picks_data:
                all_picks[player] = picks_data.get('picks', {})
                print(f"✅ Loaded picks for {player}")
            else:
                all_picks[player] = {}
                print(f"⚠️  No picks found for {player}")
                
        return all_picks
    
    def format_row_data(self, game, all_picks, week_start_date):
        """Format a single game row for the Google Sheet"""
        game_id = game.get('id', '')
        
        # Extract picks for each player
        jeff_picks = all_picks.get('jeff', {}).get(game_id, {})
        teddy_picks = all_picks.get('teddy', {}).get(game_id, {})
        will_picks = all_picks.get('will', {}).get(game_id, {})
        
        # Format the row according to your sheet structure
        row = [
            game.get('week', ''),                    # Week
            week_start_date,                         # Week Start Date
            game.get('game_date', ''),               # Game Date
            game.get('away_team', ''),               # Away Team
            game.get('home_team', ''),               # Home Team
            game.get('away_odds', ''),               # Away Spread
            game.get('home_odds', ''),               # Home Spread
            game.get('over_under', ''),              # Over/Under
            jeff_picks.get('spread', ''),            # Jeff Spread Pick
            jeff_picks.get('total', ''),             # Jeff O/U Pick
            teddy_picks.get('spread', ''),           # Teddy Spread Pick
            teddy_picks.get('total', ''),            # Teddy O/U Pick
            will_picks.get('spread', ''),            # Will Spread Pick
            will_picks.get('total', ''),             # Will O/U Pick
            '',                                      # Away Score (empty for now)
            '',                                      # Home Score (empty for now)
            '',                                      # Jeff Spread Points (calculated later)
            '',                                      # Jeff O/U Points (calculated later)
            '',                                      # Teddy Spread Points (calculated later)
            '',                                      # Teddy O/U Points (calculated later)
            '',                                      # Will Spread Points (calculated later)
            '',                                      # Will O/U Points (calculated later)
            'Scheduled'                              # Game Status
        ]
        
        return row
    
    def sync_to_sheet(self):
        """Main sync function"""
        print("🏈 NFL Picks Sync to Google Sheets Starting...")
        
        # Load games and picks data
        games_data = self.load_games_data()
        if not games_data:
            return
            
        all_picks = self.load_all_picks()
        
        # Open the Google Sheet
        try:
            sheet = self.gc.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet('Season Data')
            print(f"✅ Connected to Google Sheet: {sheet.title}")
        except Exception as e:
            print(f"❌ Error opening Google Sheet: {e}")
            return
        
        # Prepare data for the sheet
        games = games_data.get('games', [])
        week_start_date = games_data.get('week_start', '')
        current_week = games_data.get('week', 1)
        
        if not games:
            print("⚠️  No games found in games.json")
            return
        
        print(f"📅 Processing Week {current_week} with {len(games)} games")
        
        # Check if this week's data already exists
        try:
            all_values = worksheet.get_all_values()
            existing_weeks = set()
            
            for row in all_values[1:]:  # Skip header row
                if row and row[0]:  # If week column has value
                    existing_weeks.add(int(row[0]) if row[0].isdigit() else 0)
            
            if current_week in existing_weeks:
                print(f"⚠️  Week {current_week} data already exists. Updating...")
                # For now, we'll append. In a full implementation, you might want to update existing rows
        except Exception as e:
            print(f"⚠️  Could not check existing data: {e}")
        
        # Format all game rows
        rows_to_add = []
        for game in games:
            row = self.format_row_data(game, all_picks, week_start_date)
            rows_to_add.append(row)
        
        # Add rows to sheet
        try:
            if rows_to_add:
                worksheet.append_rows(rows_to_add)
                print(f"✅ Added {len(rows_to_add)} games to Google Sheet")
                
                # Log pick summary
                for player in ['jeff', 'teddy', 'will']:
                    picks_count = sum(1 for game in games if all_picks.get(player, {}).get(game.get('id', ''), {}))
                    print(f"   📊 {player.title()}: {picks_count}/{len(games)} games picked")
                
            else:
                print("⚠️  No data to add to sheet")
                
        except Exception as e:
            print(f"❌ Error adding data to sheet: {e}")
            return
        
        print("🎉 Sync completed successfully!")

def main():
    try:
        syncer = NFLSheetsSync()
        syncer.sync_to_sheet()
    except Exception as e:
        print(f"❌ Sync failed: {e}")

if __name__ == "__main__":
    main()