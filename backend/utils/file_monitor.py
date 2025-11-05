"""
File Monitor for AI Financial Statement Generation System
Watches input directory for new files and triggers processing
"""
import os
import time
import threading
from typing import Callable, Dict, Any
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..config.settings import config


class FileMonitorHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, callback: Callable[[str, str], None]):
        """Initialize with callback function"""
        self.callback = callback
        self.processed_files = set()  # Track processed files to avoid duplicates
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self._process_file(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self._process_file(event.src_path)
    
    def _process_file(self, file_path: str):
        """Process a file if it hasn't been processed yet"""
        file_path = os.path.abspath(file_path)
        
        # Check if file is of supported type
        if not self._is_supported_file(file_path):
            return
        
        # Check if already processed (avoid duplicate processing)
        file_hash = self._get_file_hash(file_path)
        if file_hash in self.processed_files:
            return
        
        # Wait a moment to ensure file is fully written
        time.sleep(1)
        
        # Add to processed set
        self.processed_files.add(file_hash)
        
        # Trigger callback with file info
        try:
            file_info = self._analyze_file(file_path)
            self.callback(file_path, file_info)
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
    
    def _is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported"""
        supported_extensions = {'.pdf', '.xlsx', '.xls'}
        return Path(file_path).suffix.lower() in supported_extensions
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate simple hash for file tracking"""
        try:
            stat = os.stat(file_path)
            return f"{file_path}_{stat.st_size}_{stat.st_mtime}"
        except:
            return file_path
    
    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze file to determine processing parameters"""
        file_ext = Path(file_path).suffix.lower()
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path).lower()
        
        # Determine if it's a template or new data
        is_template = '2024' in filename or 'template' in filename
        year = 2024 if is_template else 2025
        
        return {
            'type': file_ext,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'is_template': is_template,
            'year': year,
            'filename': filename
        }


class FileMonitor:
    """File monitoring system for automatic processing"""
    
    def __init__(self):
        """Initialize file monitor"""
        self.observer = None
        self.handler = None
        self.monitoring = False
        self.thread = None
        
        # Ensure input directory exists
        os.makedirs(config.input_directory, exist_ok=True)
    
    def start_monitoring(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Start monitoring the input directory"""
        if self.monitoring:
            print("File monitoring is already running")
            return
        
        try:
            # Create event handler
            self.handler = FileMonitorHandler(callback)
            
            # Create observer
            self.observer = Observer()
            self.observer.schedule(
                self.handler, 
                config.input_directory, 
                recursive=False
            )
            
            # Start monitoring in separate thread
            self.thread = threading.Thread(target=self._run_observer, daemon=True)
            self.monitoring = True
            self.thread.start()
            
            print(f"Started monitoring {config.input_directory} for new files")
            
        except Exception as e:
            print(f"Failed to start file monitoring: {str(e)}")
            self.monitoring = False
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if not self.monitoring:
            return
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            
            self.monitoring = False
            print("Stopped file monitoring")
            
        except Exception as e:
            print(f"Error stopping file monitoring: {str(e)}")
    
    def _run_observer(self):
        """Run the observer in the thread"""
        try:
            if self.observer:
                self.observer.start()
                
                # Keep thread alive
                while self.monitoring:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Error in file monitor thread: {str(e)}")
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active"""
        return self.monitoring
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'monitoring': self.monitoring,
            'input_directory': config.input_directory,
            'supported_extensions': ['.pdf', '.xlsx', '.xls'],
            'thread_alive': self.thread.is_alive() if self.thread else False
        }
    
    def scan_existing_files(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Scan existing files in input directory"""
        try:
            input_path = Path(config.input_directory)
            
            for file_path in input_path.glob('*'):
                if file_path.is_file() and self._is_supported_file(str(file_path)):
                    try:
                        file_info = self._analyze_file(str(file_path))
                        callback(str(file_path), file_info)
                    except Exception as e:
                        print(f"Error scanning existing file {file_path}: {str(e)}")
                        
        except Exception as e:
            print(f"Error scanning existing files: {str(e)}")
    
    def _is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported"""
        supported_extensions = {'.pdf', '.xlsx', '.xls'}
        return Path(file_path).suffix.lower() in supported_extensions
    
    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze file to determine processing parameters"""
        file_ext = Path(file_path).suffix.lower()
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path).lower()
        
        # Determine if it's a template or new data
        is_template = '2024' in filename or 'template' in filename
        year = 2024 if is_template else 2025
        
        return {
            'type': file_ext,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'is_template': is_template,
            'year': year,
            'filename': filename
        }
