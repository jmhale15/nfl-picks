# NFL Picks System - Admin Guide

## Overview
I've built a complete automated NFL picks system. This guide covers how to run and maintain it throughout the season.

## Weekly Workflow

### Step 1: Get Latest Games (Tuesday/Wednesday)
Run this every week to get the latest NFL games and betting lines:

```bash
# Navigate to your project folder
cd ~/Documents/gh/nfl-picks

# Run the setup script (handles virtual environment automatically)
./setup.sh
```

**What this does:**
- Creates/activates virtual environment automatically
- Installs any missing dependencies  
- Runs `python3 scrape.py`
- Fetches current week's NFL games from OddsShark
- Gets betting lines (spreads and over/unders)
- Saves to `games.json` 
- Automatically pushes to GitHub
- Website updates automatically via Netlify

**Expected output:**
```
🏈 NFL Picks Scraper Starting...
📅 Processing Week 5 with 16 games
✅ Saved 16 games to games.json
```

### Step 2: Monitor Picks (Wednesday-Thursday)
- **Website:** `colby-picks.netlify.app` (admin dashboard)
- **Direct picks:** `colby-picks.netlify.app/picks.html`
- **Check GitHub:** Your repo's `picks/` folder shows who has made picks

### Step 3: Sync to Google Sheets (Thursday/Friday)
After everyone has made their picks:

```bash
./sync.sh
```

**What this does:**
- Activates virtual environment automatically
- Reads all picks from GitHub (`picks/jeff.json`, `picks/teddy.json`, `picks/will.json`)
- Combines with games data
- Pushes everything to your Google Sheet
- Shows summary of who picked what

**Expected output:**
```
🏈 NFL Picks Sync to Google Sheets Starting...
✅ Loaded picks for jeff
✅ Loaded picks for teddy
✅ Loaded picks for will
✅ Connected to Google Sheet: NFL Picks 2025
📅 Processing Week 5 with 16 games
✅ Added 16 games to Google Sheet
   📊 Jeff: 16/16 games picked
   📊 Teddy: 14/16 games picked
   📊 Will: 16/16 games picked
🎉 Sync completed successfully!
```

### Step 4: Update Game Scores (Sunday/Monday)
After games are played, automatically fetch final scores:

```bash
./score.sh
```

**What this does:**
- Activates virtual environment automatically
- Fetches completed NFL game scores from ESPN API
- Matches team names between ESPN and your Google Sheet
- Updates "Away Score" and "Home Score" columns automatically
- Changes "Game Status" to "Final" for completed games
- Shows summary of games updated

**Expected output:**
```
🏈 NFL Score Updater Starting...
📅 Fetching scores for current week
✅ Found 12 completed games out of 16 total
📊 Updating: Kansas City @ Baltimore = 24-17
📊 Updating: Buffalo @ Los Angeles = 31-14
✅ Updated 12 games in Google Sheet
🎉 Score update completed!
```

**For specific weeks:**
```bash
# Update scores for a particular week
./score.sh --week 5
```

### Step 5: Calculate Points (Monday)
- Open your Google Sheet: [NFL Picks 2025](https://docs.google.com/spreadsheets/d/1xpXbCePRXldopPgpVjERMRWLos70MF1nZa2zpNoXdxI/edit)
- Review the auto-populated scores for accuracy
- Calculate points for spread and over/under picks (manually or with formulas)
- Verify everything looks correct and share results

## System Maintenance

### URLs to Bookmark
- **Admin Dashboard:** `colby-picks.netlify.app`
- **Picks Interface:** `colby-picks.netlify.app/picks.html`
- **GitHub Repo:** `https://github.com/jmhale15/nfl-picks`
- **Google Sheet:** `https://docs.google.com/spreadsheets/d/1xpXbCePRXldopPgpVjERMRWLos70MF1nZa2zpNoXdxI/edit`

### Troubleshooting

**If scraper fails:**
```bash
# Check for errors
python3 scrape.py

# If no games found, try specific week
python3 scrape.py --week 6

# Check if virtual environment is active
which python3  # Should show path with 'myenv'
```

**If sync fails:**
- Check that `google-credentials.json` exists in your project folder
- Verify Google Sheet is shared with the service account
- Check `.env` file has correct `GOOGLE_SHEET_ID`

**If website is down:**
- Check Netlify dashboard for deployment status
- GitHub commits automatically trigger new deployments
- Custom domain (`colby-picks.jhale.ai`) may take time for SSL

### File Structure
```
nfl-picks/
├── .env                    # Your secrets (not in GitHub)
├── google-credentials.json # Google API key (not in GitHub)
├── games.json             # Current week's games
├── picks/                 # Everyone's picks
│   ├── jeff.json
│   ├── teddy.json
│   └── will.json
├── setup.sh               # Get NFL games (./setup.sh)
├── sync.sh                # Sync picks to Google Sheets (./sync.sh)
├── score.sh               # Update final scores (./score.sh)
├── scrape.py             # Gets NFL games
├── sync-to-sheets.py     # Pushes picks to Google Sheet
├── score-games.py        # Fetches final scores from ESPN
└── ui/                   # Website files
```

### Season Preparation

**Before season starts:**
1. Update `season_start_date` in `config.json` if needed
2. Test the full workflow with preseason games
3. Send the picks URL to Jeff, Teddy, and Will

**During season:**
- Run scraper Tuesday/Wednesday each week
- Monitor picks Wednesday/Thursday  
- Sync to sheets Thursday/Friday
- Score games Sunday/Monday

## Advanced Features

### Manual Week Override
```bash
# Get specific week games
python3 scrape.py --week 10

# Useful for:
# - Catching up missed weeks
# - Getting games early
# - Testing the system
```

### Checking Pick Status
```bash
# See what's in GitHub
ls -la picks/

# Quick check of picks
cat picks/jeff.json | grep -o '"spread"' | wc -l  # Count Jeff's picks
```

### Re-syncing Data
```bash
# Re-sync picks to Google Sheets
./sync.sh

# Update scores for current week
./score.sh

# Update scores for specific week
./score.sh --week 8

# Get fresh games data
./setup.sh

# All scripts are safe to run multiple times
```

## Success Metrics
✅ **Zero manual spreadsheet work**  
✅ **Friends pick via clean web interface**  
✅ **All data automatically synced**  
✅ **Historical data preserved in Google Sheets**  
✅ **Mobile-friendly for picking on the go**

You've eliminated the weekly coordination overhead and created a professional system that will work reliably all season long! 🏈