"""
Session manager to handle archive_url caching and session conflicts
"""

import os
import json
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
            "user": os.environ.get("RENKU_USERNAME", os.environ.get("USER", "unknown")),
            "workspace": os.environ.get("RENKU_PROJECT_NAME", "unknown"),
            "pod_name": os.environ.get("HOSTNAME", "unknown"),
        }

        session_string = json.dumps(session_data, sort_keys=True)
        return hashlib.md5(session_string.encode()).hexdigest()[:12]

    def load_current_session(self):
        """Load current session information"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def save_current_session(self, archive_url):
        """Save current session information"""
        session_data = {
            "session_id": self.get_session_id(),
            "archive_url": archive_url,
            "timestamp": datetime.utcnow().isoformat(),
            "pid": os.getpid(),
        }

        with open(self.session_file, "w") as f:
            json.dump(session_data, f, indent=2)

    def check_session_conflict(self, current_archive_url):
        """Check if there's a session conflict and return appropriate action"""
        existing_session = self.load_current_session()
        current_session_id = self.get_session_id()

        if not existing_session:
            # No existing session
            return "new_session", None

        if existing_session["session_id"] == current_session_id:
            # Same session - check if archive_url changed
            if existing_session.get("archive_url") == current_archive_url:
                return "same_session", existing_session
            else:
                return "url_changed", existing_session
        else:
            # Different session - potential conflict
            return "session_conflict", existing_session

    def get_archive_info(self, url):
        """Extract readable archive information from URL"""
        if not url:
            return "None"

        # Try to extract filename and record ID for better display
        import re
        from urllib.parse import urlparse, unquote

        try:
            parsed = urlparse(url)

            # Extract filename
            files_match = re.search(r"/files/([^/?]+)", parsed.path)
            if files_match:
                filename = unquote(files_match.group(1))

                # Extract record ID
                records_match = re.search(r"/records/([^/]+)/", parsed.path)
                if records_match:
                    record_id = records_match.group(1)
                    return f"{filename} (record: {record_id})"
                else:
                    return filename

            # Fallback to last part of path
            path_parts = parsed.path.strip("/").split("/")
            if path_parts:
                return path_parts[-1]

        except Exception:
            pass

        # Final fallback - truncate URL
        return url[:50] + "..." if len(url) > 50 else url

    def generate_conflict_message(self, conflict_type, existing_session, current_archive_url):
        """Generate appropriate message for session conflicts"""
        existing_info = self.get_archive_info(existing_session.get("archive_url"))
        current_info = self.get_archive_info(current_archive_url)

        if conflict_type == "session_conflict":
            return f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                               SESSION CONFLICT DETECTED                        ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  You may have another active RenkuLab session running.                         ║
║                                                                                ║
║  Previous session details:                                                     ║
║    • Archive: {existing_info:<60} ║
║    • Started: {existing_session.get("timestamp", "Unknown")[:19]:<59} ║
║                                                                                ║
║  Current request:                                                              ║
║    • Archive: {current_info:<60} ║
║                                                                                ║
║  RECOMMENDED ACTION:                                                           ║
║  1. Close any other RenkuLab sessions by clicking the trash button             ║
║  2. Wait a few seconds for the session to fully terminate                      ║
║  3. Refresh this page or restart this session                                  ║
║                                                                                ║
║  If you're sure this is the only session, you can continue but you'll be       ║
║  exploring the previous archive instead of the one you just clicked on.        ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
        elif conflict_type == "url_changed":
            return f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                            ARCHIVE URL CHANGED                                 ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  The archive URL for this session has changed.                                 ║
║                                                                                ║
║  Previous: {existing_info:<62} ║
║  Current:  {current_info:<62} ║
║                                                                                ║
║  This usually means you clicked on a different archive link while this         ║
║  session was already running. The session will be updated to use the new       ║
║  archive information, but you may want to restart for a clean setup.           ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

        return ""


def main():
    """Main session management logic"""
    current_archive_url = os.environ.get("archive_url")
    session_manager = SessionManager()

    # Check for session conflicts
    conflict_type, existing_session = session_manager.check_session_conflict(current_archive_url)

    # Handle different conflict scenarios
    if conflict_type == "session_conflict":
        message = session_manager.generate_conflict_message(conflict_type, existing_session, current_archive_url)
        print(message)

        # Create a warning file that can be displayed in the notebook
        warning_file = "/tmp/session_warning.txt"
        with open(warning_file, "w") as f:
            f.write(message)

        # Also create a summary for easy checking
        summary_file = "/tmp/session_conflict_summary.json"
        with open(summary_file, "w") as f:
            json.dump(
                {
                    "conflict_type": conflict_type,
                    "existing_archive": existing_session.get("archive_url"),
                    "current_archive": current_archive_url,
                    "existing_started": existing_session.get("timestamp"),
                    "detected_at": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )

        print("Warning files created:")
        print(f"  - {warning_file}")
        print(f"  - {summary_file}")

    elif conflict_type == "url_changed":
        message = session_manager.generate_conflict_message(conflict_type, existing_session, current_archive_url)
        print(message)

        # Still create a warning for URL changes
        warning_file = "/tmp/session_warning.txt"
        with open(warning_file, "w") as f:
            f.write(message)

    elif conflict_type == "same_session":
        print("✅ Same session and archive URL - no conflicts detected")

        # Clean up any old warning files
        for warning_file in [
            "/tmp/session_warning.txt",
            "/tmp/session_conflict_notice.md",
            "/tmp/session_conflict_summary.json",
        ]:
            if os.path.exists(warning_file):
                os.remove(warning_file)
                print(f"Cleaned up old warning: {warning_file}")

    else:  # new_session
        print("✅ New session detected")

        # Clean up any old warning files
        for warning_file in [
            "/tmp/session_warning.txt",
            "/tmp/session_conflict_notice.md",
            "/tmp/session_conflict_summary.json",
        ]:
            if os.path.exists(warning_file):
                os.remove(warning_file)

    # Save/update current session
    if current_archive_url:
        session_manager.save_current_session(current_archive_url)
        print("✅ Session information saved")
        print(f"Archive URL: {current_archive_url}")
    else:
        print("ℹ️  No archive URL provided - session saved without archive")
        session_manager.save_current_session("")


if __name__ == "__main__":
    main()
