# NFL Picks System - Admin Guide

## Overview
You've built a complete automated NFL picks system! This guide covers how to run and maintain it throughout the season.

## Weekly Workflow

### Step 1: Get Latest Games (Tuesday/Wednesday)
Run this every week to get the latest NFL games and betting lines:

```bash
# Navigate to your project folder
cd ~/Documents/gh/nfl-picks

# Activate virtual environment
source myenv/bin/activate

# Run the scraper
python3 scrape.py
```

**What this does:**
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
# Same directory and virtual environment as Step 1
python3 sync-to-sheets.py
```

**What this does:**
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

### Step 4: Score Games (Sunday/Monday)
- Open your Google Sheet: [NFL Picks 2025](https://docs.google.com/spreadsheets/d/1xpXbCePRXldopPgpVjERMRWLos70MF1nZa2zpNoXdxI/edit)
- Add final scores to "Away Score" and "Home Score" columns
- Calculate points manually or with formulas (same as your old process)

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
├── scrape.py             # Gets NFL games
├── sync-to-sheets.py     # Pushes to Google Sheet
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
# If you need to re-sync to Google Sheets
python3 sync-to-sheets.py

# This is safe to run multiple times
# It will append new rows, not overwrite
```

## Success Metrics
✅ **Zero manual spreadsheet work**  
✅ **Friends pick via clean web interface**  
✅ **All data automatically synced**  
✅ **Historical data preserved in Google Sheets**  
✅ **Mobile-friendly for picking on the go**

You've eliminated the weekly coordination overhead and created a professional system that will work reliably all season long! 🏈