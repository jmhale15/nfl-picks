import json
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

class NFLScoreUpdater:
    def __init__(self):
        self.setup_google_sheets()
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
    def setup_google_sheets(self):
        """Setup Google Sheets API connection"""
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds_file = 'google-credentials.json'
        if not os.path.exists(creds_file):
            print(f"❌ Google credentials file '{creds_file}' not found!")
            exit(1)
            
        creds = Credentials.from_service_account_file(creds_file, scopes=scope)
        self.gc = gspread.authorize(creds)
    
    def get_nfl_scores(self, week=None):
        """
        Get NFL scores from ESPN API
        Returns list of completed games with scores
        """
        try:
            # ESPN NFL scoreboard API
            current_year = datetime.now().year
            if week:
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&week={week}"
            else:
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            
            print(f"🏈 Fetching scores from ESPN API...")
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            for event in data.get('events', []):
                game_info = {
                    'date': event.get('date', ''),
                    'status': event['status']['type']['name'],  # 'STATUS_FINAL', 'STATUS_IN_PROGRESS', etc.
                    'away_team': event['competitions'][0]['competitors'][1]['team']['displayName'],
                    'home_team': event['competitions'][0]['competitors'][0]['team']['displayName'],
                    'away_score': None,
                    'home_score': None
                }
                
                # Only get scores for completed games
                if event['status']['type']['name'] == 'STATUS_FINAL':
                    game_info['away_score'] = int(event['competitions'][0]['competitors'][1]['score'])
                    game_info['home_score'] = int(event['competitions'][0]['competitors'][0]['score'])
                
                games.append(game_info)
            
            completed_games = [g for g in games if g['away_score'] is not None]
            print(f"✅ Found {len(completed_games)} completed games out of {len(games)} total")
            
            return completed_games
            
        except Exception as e:
            print(f"❌ Error fetching NFL scores: {e}")
            return []
    
    def update_sheet_scores(self, scores, week_filter=None):
        """
        Update Google Sheet with final scores
        """
        try:
            # Open the Google Sheet
            sheet = self.gc.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet('Season Data')
            print(f"✅ Connected to Google Sheet: {sheet.title}")
            
            # Get all current data
            all_values = worksheet.get_all_values()
            headers = all_values[0]
            
            # Find relevant column indices
            away_team_col = headers.index('Away Team')
            home_team_col = headers.index('Home Team')
            away_score_col = headers.index('Away Score')
            home_score_col = headers.index('Home Score')
            status_col = headers.index('Game Status')
            week_col = headers.index('Week') if 'Week' in headers else None
            
            updates_made = 0
            
            # Go through each row and try to match with scores
            for i, row in enumerate(all_values[1:], start=2):  # Start from row 2 (skip header)
                if len(row) <= max(away_team_col, home_team_col):
                    continue  # Skip empty/incomplete rows
                
                away_team = row[away_team_col] if away_team_col < len(row) else ''
                home_team = row[home_team_col] if home_team_col < len(row) else ''
                current_status = row[status_col] if status_col < len(row) else ''
                
                # Skip if already scored
                if current_status == 'Final':
                    continue
                    
                # Skip if week filter specified and doesn't match
                if week_filter and week_col is not None:
                    row_week = row[week_col] if week_col < len(row) else ''
                    if str(row_week) != str(week_filter):
                        continue
                
                # Try to find matching score
                for score in scores:
                    if (self.team_name_match(away_team, score['away_team']) and 
                        self.team_name_match(home_team, score['home_team'])):
                        
                        print(f"📊 Updating: {away_team} @ {home_team} = {score['away_score']}-{score['home_score']}")
                        
                        # Update the scores and status
                        worksheet.update_cell(i, away_score_col + 1, score['away_score'])
                        worksheet.update_cell(i, home_score_col + 1, score['home_score'])
                        worksheet.update_cell(i, status_col + 1, 'Final')
                        
                        updates_made += 1
                        break
            
            print(f"✅ Updated {updates_made} games in Google Sheet")
            
            if updates_made > 0:
                print("\n📋 Next steps:")
                print("1. Review the updated scores in your Google Sheet")
                print("2. Calculate points for each player manually or with formulas")
                print("3. Verify everything looks correct")
            
        except Exception as e:
            print(f"❌ Error updating Google Sheet: {e}")
    
    def team_name_match(self, sheet_name, api_name):
        """
        Try to match team names between sheet and API
        (ESPN uses full names, your sheet might use city or abbreviations)
        """
        if not sheet_name or not api_name:
            return False
            
        sheet_name = sheet_name.lower().strip()
        api_name = api_name.lower().strip()
        
        # Direct match
        if sheet_name == api_name:
            return True
        
        # Check if sheet name is contained in API name or vice versa
        if sheet_name in api_name or api_name in sheet_name:
            return True
            
        # Common team name mappings
        team_mappings = {
            'kansas city': ['chiefs', 'kc'],
            'new england': ['patriots'],
            'green bay': ['packers'],
            'new orleans': ['saints'],
            'san francisco': ['49ers'],
            'los angeles': ['rams', 'chargers'],
            'new york': ['giants', 'jets'],
            'tampa bay': ['buccaneers', 'bucs']
        }
        
        for full_name, short_names in team_mappings.items():
            if full_name in api_name.lower():
                if any(short in sheet_name.lower() for short in short_names):
                    return True
            if full_name in sheet_name.lower():
                if any(short in api_name.lower() for short in short_names):
                    return True
        
        return False
    
    def run(self, week=None):
        """Main function to update scores"""
        print(f"🏈 NFL Score Updater Starting...")
        
        if week:
            print(f"📅 Fetching scores for Week {week}")
        else:
            print(f"📅 Fetching scores for current week")
        
        # Get scores from ESPN
        scores = self.get_nfl_scores(week)
        
        if not scores:
            print("⚠️ No completed games found")
            return
        
        print(f"\n📋 Completed games found:")
        for score in scores:
            print(f"   {score['away_team']} {score['away_score']} - {score['home_score']} {score['home_team']}")
        
        # Update Google Sheet
        print(f"\n📊 Updating Google Sheet...")
        self.update_sheet_scores(scores, week)
        
        print(f"\n🎉 Score update completed!")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Update NFL game scores in Google Sheet')
    parser.add_argument('--week', type=int, help='Specific week to update (optional)')
    args = parser.parse_args()
    
    updater = NFLScoreUpdater()
    updater.run(args.week)

if __name__ == "__main__":
    main()