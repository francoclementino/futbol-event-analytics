# Streamlit Cloud Configuration

## 🚀 Deployment Notes

This app is designed to work in two modes:

### 1. **Streamlit Cloud Mode** (Default)
- Uses **file uploader** for JSON files
- No large data files in repository
- Users upload their own match JSON files
- Lightweight and fast deployment

### 2. **Local Mode** (with full database)
- Requires local JSONs organized in `data/raw/`
- Run `python generate_metadata.py` to index matches
- Enables advanced filtering (country/competition/season)
- Sidebar with full navigation

## Environment Detection

The app automatically detects if `matches_metadata.json` exists:
- ✅ **Exists**: Shows advanced filters with sidebar
- ❌ **Missing**: Shows file uploader interface

## Files NOT in Repository

The following are excluded from git (see `.gitignore`):
- `data/raw/**/*.json` - Individual match files (too large)
- `data/processed/` - Processed data files
- Backup files (`*_BACKUP*.py`)

## Files INCLUDED in Repository

- ✅ `data/raw/matches_metadata.json` - Small index file (~1-2 MB)
- ✅ All Python scripts and notebooks
- ✅ Requirements and configuration
- ✅ Documentation

## Size Limits

- Max file size: 100 MB (GitHub)
- Recommended repo size: < 1 GB
- Match JSONs: ~1.5 MB each
- With 1800+ matches: ~3 GB (excluded)

## For Contributors

If you want to test locally with full database:
1. Clone the repository
2. Add your JSON files to `data/raw/` following folder structure
3. Run `python generate_metadata.py`
4. Metadata files will be created (can be committed)
5. JSON files stay local only (gitignored)
