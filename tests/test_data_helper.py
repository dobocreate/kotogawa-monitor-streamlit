"""
Unit tests for data_helper module.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_helper import get_latest_history_file, load_latest_data, get_latest_file_mtime


class TestDataHelper:
    """Test suite for data helper functions."""
    
    @pytest.fixture
    def temp_history_dir(self):
        """Create a temporary history directory structure."""
        temp_dir = tempfile.mkdtemp()
        history_dir = Path(temp_dir) / "history"
        history_dir.mkdir()
        
        yield history_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def create_test_file(self, history_dir: Path, date_str: str, time_str: str, 
                        is_error: bool = False, content: dict = None):
        """Helper to create test JSON files."""
        year, month, day = date_str.split("-")
        date_dir = history_dir / year / month / day
        date_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"error_{time_str}.json" if is_error else f"{time_str}.json"
        file_path = date_dir / filename
        
        if content is None:
            content = {
                "timestamp": f"{date_str}T{time_str[:2]}:{time_str[2:]}:00+09:00",
                "data_time": f"{date_str}T{time_str[:2]}:{time_str[2:]}:00+09:00",
                "test": True
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f)
        
        return file_path
    
    def test_find_latest_file_single_day(self, temp_history_dir):
        """Test finding the latest file within a single day."""
        # Create test files
        today = datetime.now().strftime("%Y-%m-%d")
        self.create_test_file(temp_history_dir, today, "0900")
        self.create_test_file(temp_history_dir, today, "1200")
        latest = self.create_test_file(temp_history_dir, today, "1500")
        
        result = get_latest_history_file(temp_history_dir)
        assert result == latest
    
    def test_skip_error_files(self, temp_history_dir):
        """Test that error_*.json files are skipped."""
        today = datetime.now().strftime("%Y-%m-%d")
        normal = self.create_test_file(temp_history_dir, today, "0900")
        self.create_test_file(temp_history_dir, today, "1000", is_error=True)
        self.create_test_file(temp_history_dir, today, "1100", is_error=True)
        
        result = get_latest_history_file(temp_history_dir)
        assert result == normal
    
    def test_find_latest_across_days(self, temp_history_dir):
        """Test finding the latest file across multiple days."""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        self.create_test_file(temp_history_dir, yesterday.strftime("%Y-%m-%d"), "2300")
        latest = self.create_test_file(temp_history_dir, today.strftime("%Y-%m-%d"), "0100")
        
        result = get_latest_history_file(temp_history_dir)
        assert result == latest
    
    def test_empty_history_dir(self, temp_history_dir):
        """Test behavior with empty history directory."""
        result = get_latest_history_file(temp_history_dir)
        assert result is None
    
    def test_nonexistent_history_dir(self):
        """Test behavior with non-existent history directory."""
        result = get_latest_history_file(Path("/nonexistent/path"))
        assert result is None
    
    def test_load_latest_data_success(self, temp_history_dir):
        """Test successfully loading latest data."""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {"test": "data", "value": 123}
        self.create_test_file(temp_history_dir, today, "1000", content=test_data)
        
        data_dir = temp_history_dir.parent
        result = load_latest_data(data_dir)
        assert result == test_data
    
    def test_load_latest_data_no_files(self, temp_history_dir):
        """Test loading data when no files exist."""
        data_dir = temp_history_dir.parent
        result = load_latest_data(data_dir)
        assert result is None
    
    def test_get_latest_file_mtime(self, temp_history_dir):
        """Test getting modification time of latest file."""
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = self.create_test_file(temp_history_dir, today, "1000")
        
        data_dir = temp_history_dir.parent
        mtime = get_latest_file_mtime(data_dir)
        
        assert mtime is not None
        assert mtime == file_path.stat().st_mtime
    
    def test_get_latest_file_mtime_no_files(self, temp_history_dir):
        """Test getting mtime when no files exist."""
        data_dir = temp_history_dir.parent
        mtime = get_latest_file_mtime(data_dir)
        assert mtime is None
    
    def test_multiple_files_same_day_ordering(self, temp_history_dir):
        """Test correct ordering of files with similar timestamps."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create files in non-sequential order
        self.create_test_file(temp_history_dir, today, "1400")
        self.create_test_file(temp_history_dir, today, "0900")
        latest = self.create_test_file(temp_history_dir, today, "1530")
        self.create_test_file(temp_history_dir, today, "1000")
        
        result = get_latest_history_file(temp_history_dir)
        assert result == latest
    
    def test_corrupted_json_file(self, temp_history_dir):
        """Test handling of corrupted JSON file."""
        today = datetime.now().strftime("%Y-%m-%d")
        year, month, day = today.split("-")
        date_dir = temp_history_dir / year / month / day
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Create corrupted file
        corrupted = date_dir / "1000.json"
        with open(corrupted, 'w') as f:
            f.write("not valid json{")
        
        data_dir = temp_history_dir.parent
        result = load_latest_data(data_dir)
        assert result is None  # Should handle gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])