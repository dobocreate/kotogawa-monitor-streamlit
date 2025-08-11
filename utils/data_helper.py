"""
Data helper utilities for finding and loading historical data files.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


def get_latest_history_file(history_dir: Path) -> Optional[Path]:
    """
    Find the most recent data file in the history directory.
    
    Args:
        history_dir: Path to the history directory (data/history)
    
    Returns:
        Path to the most recent JSON file, or None if no files found
        
    Note:
        - Skips error_*.json files
        - Looks back up to 7 days for data
        - Returns the most recent file based on directory structure and filename
    """
    if not history_dir.exists():
        return None
    
    # Look back up to 7 days to find the most recent data
    end_date = datetime.now()
    
    for days_back in range(7):
        check_date = end_date - timedelta(days=days_back)
        year = check_date.strftime("%Y")
        month = check_date.strftime("%m")
        day = check_date.strftime("%d")
        
        date_dir = history_dir / year / month / day
        
        if date_dir.exists():
            # Get all JSON files, excluding error files
            json_files = [
                f for f in date_dir.glob("*.json")
                if not f.name.startswith("error_") and f.is_file()
            ]
            
            if json_files:
                # Sort by filename (HHMM.json format) and return the latest
                latest_file = sorted(json_files, key=lambda x: x.name)[-1]
                return latest_file
    
    return None


def load_latest_data(data_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load the most recent data from the history directory.
    
    Args:
        data_dir: Path to the data directory containing 'history' subdirectory
    
    Returns:
        Dictionary containing the latest data, or None if not found/error
    """
    history_dir = data_dir / "history"
    latest_file = get_latest_history_file(history_dir)
    
    if not latest_file:
        return None
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, Exception):
        return None


def get_latest_file_mtime(data_dir: Path) -> Optional[float]:
    """
    Get the modification time of the most recent history file.
    Used for cache invalidation.
    
    Args:
        data_dir: Path to the data directory
    
    Returns:
        Modification time as float, or None if no file found
    """
    history_dir = data_dir / "history"
    latest_file = get_latest_history_file(history_dir)
    
    if latest_file and latest_file.exists():
        return latest_file.stat().st_mtime
    
    return None