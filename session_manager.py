#!/usr/bin/env python3
"""
Session manager to handle archive_url caching and session conflicts
"""

import os
import json
import sys
import hashlib
from datetime import datetime


class SessionManager:
    def __init__(self, cache_dir="/tmp/renku_sessions"):
        self.cache_dir = cache_dir
        self.session_file = os.path.join(cache_dir, "current_session.json")
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_session_id(self):
        """Generate a unique session ID based on environment"""
        # Use combination of user, workspace, and other identifiers
        session_data = {
            'user': os.environ.get('RENKU_USERNAME', os.environ.get('USER', 'unknown')),
            'workspace': os.environ.get('RENKU_PROJECT_NAME', 'unknown'),
            'pod_name': os.environ.get('HOSTNAME', 'unknown')
        }
        
        session_string = json.dumps(session_data, sort_keys=True)
        return hashlib.md5(session_string.encode()).hexdigest()[:12]
    
    def load_current_session(self):
        """Load current session information"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def save_current_session(self, archive_url):
        """Save current session information"""
        session_data = {
            'session_id': self.get_session_id(),
            'archive_url': archive_url,
            'timestamp': datetime.utcnow().isoformat(),
            'pid': os.getpid()
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def check_session_conflict(self, current_archive_url):
        """Check if there's a session conflict and return appropriate action"""
        existing_session = self.load_current_session()
        current_session_id = self.get_session_id()
        
        if not existing_session:
            # No existing session
            return 'new_session', None
        
        if existing_session['session_id'] == current_session_id:
            # Same session - check if archive_url changed
            if existing_session.get('archive_url') == current_archive_url:
                return 'same_session', existing_session
            else:
                return 'url_changed', existing_session
        else:
            # Different session - potential conflict
            return 'session_conflict', existing_session
    
    def generate_conflict_message(self, conflict_type, existing_session, current_archive_url):
        """Generate appropriate message for session conflicts"""
        if conflict_type == 'session_conflict':
            return f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                               SESSION CONFLICT DETECTED                        ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  It appears you may have another active RenkuLab session running.             ║
║                                                                                ║
║  Previous session details:                                                     ║
║    • Archive URL: {existing_session.get('archive_url', 'Unknown')[:50]}{'...' if len(existing_session.get('archive_url', '')) > 50 else ''}  ║
║    • Started: {existing_session.get('timestamp', 'Unknown')[:19]}                                     ║
║                                                                                ║
║  Current session:                                                              ║
║    • Archive URL: {current_archive_url[:50] if current_archive_url else 'None'}{'...' if current_archive_url and len(current_archive_url) > 50 else ''}  ║
║                                                                                ║
║  RECOMMENDED ACTION:                                                           ║
║  1. Close any other RenkuLab sessions by clicking the trash button            ║
║  2. Wait a few seconds for the session to fully terminate                     ║
║  3. Refresh this page or restart this session                                 ║
║                                                                                ║
║  If you're sure this is the only session, this message can be ignored.       ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
        elif conflict_type == 'url_changed':
            return f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                            ARCHIVE URL CHANGED                                 ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  The archive URL for this session has changed.                                ║
║                                                                                ║
║  Previous URL: {existing_session.get('archive_url', 'Unknown')[:45]}{'...' if len(existing_session.get('archive_url', '')) > 45 else ''}     ║
║  Current URL:  {current_archive_url[:45] if current_archive_url else 'None'}{'...' if current_archive_url and len(current_archive_url) > 45 else ''}     ║
║                                                                                ║
║  The session will be updated to use the new archive.                          ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
        
        return ""


def main():
    """Main session management logic"""
    current_archive_url = os.environ.get('archive_url')
    session_manager = SessionManager()
    
    # Check for session conflicts
    conflict_type, existing_session = session_manager.check_session_conflict(current_archive_url)
    
    # Handle different conflict scenarios
    if conflict_type == 'session_conflict':
        message = session_manager.generate_conflict_message(conflict_type, existing_session, current_archive_url)
        print(message)
        
        # Create a warning file that can be displayed in the notebook
        warning_file = "/tmp/session_warning.txt"
        with open(warning_file, 'w') as f:
            f.write(message)
        
        # Don't exit - let the session continue but with warning
        
    elif conflict_type == 'url_changed':
        message = session_manager.generate_conflict_message(conflict_type, existing_session, current_archive_url)
        print(message)
    
    # Save/update current session
    if current_archive_url:
        session_manager.save_current_session(current_archive_url)
    
    print(f"Session management completed. Archive URL: {current_archive_url or 'None'}")


if __name__ == '__main__':
    main()
