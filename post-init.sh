#!/bin/bash

# ============================================
# AiiDA-RenkuLab Session Initialization Script
# ============================================

set -e

echo "===== AiiDA-RenkuLab Session Setup ====="

project_dir="$(pwd)/work/renku2-aiida-integration"
script_dir="${project_dir}/.scripts"
archive_dir="${project_dir}/data/aiida"

# Export AIIDA_PATH environment variable
export AIIDA_PATH=$HOME

# Make scripts executable
echo "Making scripts executable..."
chmod +x "${script_dir}/fetch_mca_metadata.py" 2>/dev/null || true
chmod +x "${script_dir}/process_notebook.py" 2>/dev/null || true
chmod +x "${script_dir}/session_manager.py" 2>/dev/null || true

# Create necessary directories
echo "Creating directories..."
mkdir -p "$archive_dir"
mkdir -p "/tmp/renku_sessions" 2>/dev/null || true

# =============================================================================
# SESSION CONFLICT DETECTION
# =============================================================================

echo ""
echo "Checking for session conflicts..."

# Run session manager to detect conflicts
if python3 "${script_dir}/session_manager.py"; then
    echo "✓ Session management completed"
else
    echo "⚠ Warning: Session manager encountered issues"
fi

# Check if there's a session warning file
if [ -f "/tmp/session_warning.txt" ]; then
    echo ""
    echo "⚠️  SESSION CONFLICT DETECTED ⚠️"
    cat "/tmp/session_warning.txt"
    echo ""

    # Create a prominent warning file for the notebook to display
    cat > "/tmp/session_conflict_notice.md" << 'EOF'
# ⚠️ SESSION CONFLICT DETECTED

**You may be viewing a different archive than expected!**

This Renku session was started with a different Materials Cloud Archive than the one you just clicked on.

**What happened?**
- Renku allows only one session per user at a time
- When you clicked the new archive link, you were redirected to this existing session
- This session is currently configured for a different archive

**What should you do?**

### Option 1: Close and restart (Recommended)
1. **Close this session** by clicking the 🗑️ trash button in the top-left corner
2. **Wait 10-15 seconds** for the session to fully terminate
3. **Click the archive link again** to start a fresh session with the correct archive

### Option 2: Switch archives in this session
If you want to explore the new archive in this existing session:
1. Scroll down to find the "Manual Setup" section in the notebook
2. Enter the new archive URL in the setup cell
3. Run the setup cells to download and configure the new archive

---
*This message will disappear after you restart the session or manually switch archives.*
EOF

    echo "Session conflict notice created for notebook display"
fi

# =============================================================================
# METADATA PROCESSING
# =============================================================================

if [ -n "$archive_url" ]; then
    echo ""
    echo "Archive URL detected: $archive_url"

    # Normalize URL by removing /content suffix if present
    normalized_url="$archive_url"
    if [[ "$normalized_url" == *"/content" ]]; then
        normalized_url="${normalized_url%/content}"
        echo "Normalized URL (removed /content): $normalized_url"
    fi

    # Verify URL format using normalized URL
    if [[ "$normalized_url" != *"/records/"* ]] || [[ "$normalized_url" != *"/files/"* ]] || [[ "$normalized_url" != *".aiida"* ]]; then
        echo "Error: URL does not match expected Materials Cloud Archive format"
        echo "Expected: https://archive.materialscloud.org/records/{record_id}/files/{filename.aiida}"
        echo ""
        echo "Continuing with manual setup mode..."
        unset archive_url
    else
        # Extract basic info for display using normalized URL
        if [[ "$normalized_url" =~ /files/([^/?]+) ]]; then
            archive_filename="${BASH_REMATCH[1]}"
            archive_filename=$(python3 -c "import urllib.parse; print(urllib.parse.unquote('$archive_filename'))")
            echo "Archive filename: $archive_filename"
        fi

        if [[ "$normalized_url" =~ /records/([^/]+)/ ]]; then
            record_id="${BASH_REMATCH[1]}"
            echo "Record ID: $record_id"
        fi

        # Fetch metadata from Materials Cloud Archive
        echo "Fetching dataset metadata from Materials Cloud Archive..."
        if python3 "${script_dir}/fetch_mca_metadata.py"; then
            echo "✓ Metadata fetched successfully"

        else
            echo "⚠ Warning: Failed to fetch metadata, continuing with basic info"
            # Set basic environment variables from URL parsing
            export MCA_ARCHIVE_FILENAME="$archive_filename"
            export MCA_AIIDA_PROFILE=$(python3 -c "import os; print(os.path.splitext('$archive_filename')[0])" 2>/dev/null || echo "aiida-renku")
        fi
    fi
else
    echo "No archive URL provided - setting up for manual archive import"
fi

# =============================================================================
# NOTEBOOK PROCESSING
# =============================================================================

echo ""
echo "Processing notebook template..."
if python3 "${script_dir}/process_notebook.py"; then
    echo "✓ Notebook processed successfully"
else
    echo "Warning: Failed to process notebook template"
    # Copy template as fallback
    if [ -f "${project_dir}/notebooks/.explore_template.ipynb" ] && [ ! -f "${project_dir}/notebooks/explore.ipynb" ]; then
        cp "${project_dir}/notebooks/.explore_template.ipynb" "${project_dir}/notebooks/explore.ipynb"
        echo "✓ Used template notebook as fallback"
    fi
fi

echo ""
echo "===== Setup Complete ====="
echo ""

# Display appropriate completion message based on session state
if [ -f "/tmp/session_warning.txt" ]; then
    echo "⚠️  IMPORTANT: Please read the session conflict notice in your notebook!"
    echo ""
    echo "You may be exploring a different archive than expected."
    echo "Consider closing this session and clicking your archive link again."
else
    echo "Ready to explore! Open notebooks/explore.ipynb to get started."
    echo ""
    if [ -n "$archive_url" ]; then
        echo "Next steps:"
        echo "  1. Open the notebook to see dataset information"
        echo "  2. Run the archive download cell to fetch the data"
        echo "  3. Run the AiiDA setup cell to create the profile"
        echo "  4. Start exploring your data!"
    else
        echo "Next steps:"
        echo "   1. Open the notebook for manual setup instructions"
        echo "   2. Download or upload your .aiida archive"
        echo "   3. Follow the notebook instructions to import"
    fi
fi
echo ""