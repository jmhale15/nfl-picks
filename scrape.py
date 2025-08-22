import requests
import json
import os
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import urllib3

# Load environment variables
load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found. Please create it with player names and settings.")
        exit(1)

def get_season_start_date(config):
    """Get season start date from config"""
    try:
        return datetime.strptime(config['season_start_date'], '%Y-%m-%d')
    except (KeyError, ValueError):
        print("Invalid or missing season_start_date in config.json")
        exit(1)

def calculate_nfl_week(config, override_week=None):
    """
    Calculate which NFL week to fetch based on current date and season start.
    Returns week number and the date range for that week.
    """
    if override_week:
        print(f"🔧 Using manual week override: Week {override_week}")
        return override_week, get_week_date_range(config, override_week)
    
    season_start = get_season_start_date(config)
    today = datetime.now()
    
    # If before season starts, default to Week 1
    if today < season_start:
        print(f"📅 Before season start ({season_start.strftime('%m/%d/%Y')}), defaulting to Week 1")
        return 1, get_week_date_range(config, 1)
    
    # Calculate which week we're in based on season start
    days_since_start = (today - season_start).days
    current_week = (days_since_start // 7) + 1
    
    # Cap at reasonable week numbers (regular season is ~18 weeks)
    current_week = min(current_week, 18)
    
    print(f"📅 Season started {season_start.strftime('%m/%d/%Y')}, currently Week {current_week}")
    return current_week, get_week_date_range(config, current_week)

def get_week_date_range(config, week_number):
    """
    Get the date range for a specific NFL week.
    NFL weeks typically run Thursday to Wednesday.
    """
    season_start = get_season_start_date(config)
    
    # Calculate the start of the requested week
    # Week 1 starts on season_start_date, subsequent weeks are 7 days apart
    week_start = season_start + timedelta(weeks=week_number - 1)
    
    # Ensure we start on a Thursday (NFL week start)
    # Adjust if season_start isn't a Thursday
    days_to_thursday = (3 - week_start.weekday()) % 7  # Thursday is 3
    if week_start.weekday() != 3:  # If not Thursday
        week_start = week_start - timedelta(days=week_start.weekday()) + timedelta(days=3)
        if week_number > 1:
            week_start += timedelta(weeks=week_number - 1)
    
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Week ends next Wednesday
    week_end = week_start + timedelta(days=6, hours=23, minutes=59)
    
    return week_start, week_end

def fetch_games():
    """Fetch NFL games from OddsShark API"""
    try:
        r = requests.get(
            'https://io.oddsshark.com/ticker/nfl',
            headers={
                'referer': 'https://www.oddsshark.com/nfl/scores'
            },
            verify=False
        )
        r.raise_for_status()
        return r.json()['matchups']
    except requests.exceptions.RequestException as e:
        print(f"An error occurred fetching games: {e}")
        exit(1)

def filter_games_by_week(matchups, min_date, max_date, week_number):
    """Filter games to specified week and format data"""
    min_date_str = min_date.strftime("%Y-%m-%d %H:%M")
    max_date_str = max_date.strftime("%Y-%m-%d %H:%M")
    
    print(f"🔍 Filtering games between {min_date.strftime('%m/%d/%Y')} and {max_date.strftime('%m/%d/%Y')}")
    
    games = []
    for matchup in matchups:
        if (matchup["type"] == "matchup" and 
            matchup["event_date"] >= min_date_str and 
            matchup["event_date"] <= max_date_str):
            
            game = {
                "id": f"{matchup['away_name']}_{matchup['home_name']}_{matchup['event_date']}",
                "week": week_number,
                "game_date": matchup["event_date"],
                "away_team": matchup["away_name"],
                "home_team": matchup["home_name"],
                "away_odds": matchup["away_odds"],
                "home_odds": matchup["home_odds"],
                "over_under": matchup["total"],
                "matchup_link": f"https://www.oddsshark.com{matchup['matchup_link']}"
            }
            games.append(game)
    
    return games

def save_games_json(games, config, week_number, week_start):
    """Save games data to JSON file"""
    output_data = {
        "week": week_number,
        "week_start": week_start.strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "players": config["players"],
        "games": games
    }
    
    with open('games.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Saved {len(games)} games to games.json")
    print(f"📅 Week {week_number} starting: {week_start.strftime('%B %d, %Y')}")

def main():
    parser = argparse.ArgumentParser(description='NFL Picks Scraper')
    parser.add_argument('--week', type=int, help='Override which week to fetch (1-18)')
    args = parser.parse_args()
    
    print("🏈 NFL Picks Scraper Starting...")
    
    # Load configuration
    config = load_config()
    
    # Calculate which week to fetch
    week_number, (min_date, max_date) = calculate_nfl_week(config, args.week)
    
    # Fetch all matchups
    all_matchups = fetch_games()
    print(f"🔍 Found {len(all_matchups)} total matchups from API")
    
    # Filter to specified week games
    current_week_games = filter_games_by_week(all_matchups, min_date, max_date, week_number)
    
    if not current_week_games:
        print(f"⚠️  No games found for Week {week_number}.")
        print(f"   Date range: {min_date.strftime('%m/%d/%Y')} to {max_date.strftime('%m/%d/%Y')}")
        print("   This might be normal during off-season or if the week hasn't been published yet.")
        
        # Still save an empty structure for consistency
        save_games_json([], config, week_number, min_date)
        return
    
    # Save to JSON
    save_games_json(current_week_games, config, week_number, min_date)
    
    print(f"\n📋 Games found for Week {week_number}:")
    for game in current_week_games:
        print(f"   {game['away_team']} @ {game['home_team']} - {game['game_date']}")

if __name__ == "__main__":
    main()