#!/bin/bash

# =============================================================================
# AiiDA-RenkuLab Session Initialization Script
# Consolidated setup and initialization for Materials Cloud Archive exploration
# =============================================================================

set -e

echo "===== AiiDA-RenkuLab Session Setup ====="

# Set some variables
first_name=aiida
last_name=renku
email="aiida@renku2"
aiida_profile="aiida-renku"
institution="AiiDA-RenkuLab"

project_dir="$(pwd)"
repo_dir="${project_dir}/aiida_data"

# Export AIIDA_PATH environment variable
export AIIDA_PATH=$HOME

# =============================================================================
# DEPENDENCY INSTALLATION
# =============================================================================

echo "Installing required Python packages..."
pip install -q jinja2 requests || {
    echo "Warning: Failed to install some packages, trying alternative method..."
    python3 -m pip install --user jinja2 requests
}

# Make scripts executable
echo "Making scripts executable..."
chmod +x "${project_dir}/fetch_mca_metadata.py" 2>/dev/null || true
chmod +x "${project_dir}/session_manager.py" 2>/dev/null || true
chmod +x "${project_dir}/process_notebook.py" 2>/dev/null || true

# Create necessary directories
echo "Creating directories..."
mkdir -p "$repo_dir"
mkdir -p "/tmp/renku_sessions" 2>/dev/null || true

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

echo "Checking session status..."
python3 "${project_dir}/session_manager.py"

# =============================================================================
# METADATA PROCESSING
# =============================================================================

if [ -n "$archive_url" ]; then
    echo ""
    echo "Archive URL detected: $archive_url"

    # Verify URL format
    if [[ "$archive_url" != *"/records/"* ]] || [[ "$archive_url" != *"/files/"* ]] || [[ "$archive_url" != *".aiida"* ]]; then
        echo "Error: URL does not match expected Materials Cloud Archive format"
        echo "Expected: https://archive.materialscloud.org/records/{record_id}/files/{filename.aiida}"
        echo ""
        echo "Continuing with manual setup mode..."
        unset archive_url
    else
        # Extract basic info for display
        if [[ "$archive_url" =~ /files/([^/?]+) ]]; then
            archive_filename="${BASH_REMATCH[1]}"
            archive_filename=$(python3 -c "import urllib.parse; print(urllib.parse.unquote('$archive_filename'))")
            echo "Archive filename: $archive_filename"
        fi

        if [[ "$archive_url" =~ /records/([^/]+)/ ]]; then
            record_id="${BASH_REMATCH[1]}"
            echo "Record ID: $record_id"
        fi

        # Fetch metadata from Materials Cloud Archive
        echo "Fetching dataset metadata from Materials Cloud Archive..."
        if python3 "${project_dir}/fetch_mca_metadata.py"; then
            echo "✓ Metadata fetched successfully"

            # Export metadata as environment variables for notebook processing
            if [ -f "/tmp/mca_metadata.json" ]; then
                export MCA_METADATA_FILE="/tmp/mca_metadata.json"

                # Extract key values for easy access
                export MCA_TITLE=$(python3 -c "import json; data=json.load(open('/tmp/mca_metadata.json')); print(data.get('title', ''))")
                export MCA_DOI=$(python3 -c "import json; data=json.load(open('/tmp/mca_metadata.json')); print(data.get('doi', ''))")
                export MCA_ENTRY=$(python3 -c "import json; data=json.load(open('/tmp/mca_metadata.json')); print(data.get('mca_entry', ''))")
                export MCA_ARCHIVE_FILENAME=$(python3 -c "import json; data=json.load(open('/tmp/mca_metadata.json')); print(data.get('archive_filename', ''))")
                export MCA_AIIDA_PROFILE=$(python3 -c "import json; data=json.load(open('/tmp/mca_metadata.json')); print(data.get('aiida_profile', 'aiida-renku'))")

                echo "✓ Environment variables set"
                echo "  Title: $MCA_TITLE"
                echo "  DOI: $MCA_DOI"
                echo "  Archive: $MCA_ARCHIVE_FILENAME"
            fi
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
# AIIDA BASIC SETUP (WITHOUT ARCHIVE)
# =============================================================================

echo ""
echo "Setting up basic AiiDA environment..."

# Only set up a basic profile for manual use - no archive loading during startup
if [ -z "$archive_url" ]; then
    # Standard setup with RabbitMQ for manual use
    echo "Setting up full AiiDA environment for manual archive import..."

    # RMQ
    rabbitmq-server -detached 2>/dev/null || echo "RabbitMQ may already be running"
    verdi profile configure-rabbitmq 2>/dev/null || echo "RabbitMQ already configured"
    verdi config set warnings.rabbitmq_version False 2>/dev/null || true

    # Create profile if it doesn't exist
    if ! verdi profile show $aiida_profile >/dev/null 2>&1; then
        verdi profile setup core.sqlite_dos \
            --profile-name $aiida_profile \
            --first-name "$first_name" \
            --last-name "$last_name" \
            --email "$email" \
            --institution "$institution" \
            --set-as-default \
            --non-interactive
        echo "✓ AiiDA profile '$aiida_profile' created"
    else
        echo "✓ AiiDA profile '$aiida_profile' already exists"
    fi
else
    echo "Archive mode detected - AiiDA profile will be created when archive is loaded"
    echo "  (Profile creation moved to notebook for faster startup)"
fi

# =============================================================================
# NOTEBOOK PROCESSING
# =============================================================================

echo ""
echo "Processing notebook template..."
if python3 "${project_dir}/process_notebook.py"; then
    echo "✓ Notebook processed successfully"
else
    echo "⚠ Warning: Failed to process notebook template"
    # Copy template as fallback
    if [ -f "${project_dir}/notebooks/explore_template_claude.ipynb" ] && [ ! -f "${project_dir}/notebooks/explore.ipynb" ]; then
        cp "${project_dir}/notebooks/explore_template_claude.ipynb" "${project_dir}/notebooks/explore.ipynb"
        echo "✓ Used template notebook as fallback"
    fi
fi

# =============================================================================
# SESSION WARNINGS AND COMPLETION
# =============================================================================

# Display session warning if it exists
if [ -f "/tmp/session_warning.txt" ]; then
    echo ""
    echo "===== SESSION WARNING ====="
    cat /tmp/session_warning.txt
    echo "============================"
    echo ""
fi

echo ""
echo "===== Setup Complete ====="
echo ""
echo "Session Information:"
echo "  Mode: $([ -n "$archive_url" ] && echo "Archive Mode" || echo "Manual Import Mode")"
echo "  Archive URL: ${archive_url:-'None (manual setup)'}"
if [ -n "$archive_url" ]; then
    echo "  Archive File: ${MCA_ARCHIVE_FILENAME:-'Unknown'}"
    echo "  Dataset: ${MCA_TITLE:-'Unknown'}"
    echo "  DOI: ${MCA_DOI:-'Not available'}"
fi
echo "  AiiDA Profile: ${MCA_AIIDA_PROFILE:-$aiida_profile}"
echo ""
echo "🚀 Ready to explore! Open notebooks/explore.ipynb to get started."
echo ""
if [ -n "$archive_url" ]; then
    echo "📋 Next steps:"
    echo "   1. Open the notebook to see dataset information"
    echo "   2. Run the archive download cell to fetch the data"
    echo "   3. Run the AiiDA setup cell to create the profile"
    echo "   4. Start exploring your data!"
else
    echo "📋 Next steps:"
    echo "   1. Open the notebook for manual setup instructions"
    echo "   2. Download or upload your .aiida archive"
    echo "   3. Follow the notebook instructions to import"
fi
echo ""
