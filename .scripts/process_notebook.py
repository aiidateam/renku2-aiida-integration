#!/usr/bin/env python3
"""
Process the notebook template with metadata and conditional cell visibility
"""

import json
import os
import sys
from jinja2 import Template


def load_metadata():
    """Load metadata from JSON file"""
    metadata_file = '/tmp/mca_metadata.json'
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return None


def process_notebook(template_path, output_path, has_archive_url=False, metadata=None):
    """Process notebook template with conditional cell visibility and metadata substitution"""

    # Load template notebook
    with open(template_path, 'r') as f:
        notebook = json.load(f)

    # Filter cells based on archive_url presence
    filtered_cells = []

    for cell in notebook['cells']:
        cell_tags = cell.get('metadata', {}).get('tags', [])

        if has_archive_url:
            # Show archive-setup cells, hide manual-setup cells
            if 'manual-setup' in cell_tags:
                continue
            elif 'archive-setup' in cell_tags:
                # Process Jinja2 templating for archive-setup cells
                if metadata and cell['cell_type'] == 'markdown':
                    template_content = ''.join(cell['source'])

                    # Prepare template variables
                    template_vars = {
                        'title': metadata.get('title', 'Unknown Dataset'),
                        'doi_url': f"https://doi.org/{metadata['doi']}" if metadata.get('doi') else 'DOI not available',
                        'mca_entry': metadata.get('mca_entry', 'Unknown'),
                        'archive_filename': metadata.get('archive_filename', 'Unknown'),
                        'aiida_profile': metadata.get('aiida_profile', 'aiida-renku')
                    }

                    # Render template
                    template = Template(template_content)
                    rendered_content = template.render(**template_vars)

                    # Split back into lines for notebook format
                    cell['source'] = rendered_content.split('\n')
                    # Add newlines back except for last line
                    cell['source'] = [line + '\n' for line in cell['source'][:-1]] + [cell['source'][-1]]
        else:
            # Show manual-setup cells, hide archive-setup cells
            if 'archive-setup' in cell_tags:
                continue

        filtered_cells.append(cell)

    # Update notebook with filtered cells
    notebook['cells'] = filtered_cells

    # Save processed notebook
    with open(output_path, 'w') as f:
        json.dump(notebook, f, indent=1)


def main():
    template_path = '/home/jovyan/work/notebooks/explore_template_claude.ipynb'
    output_path = '/home/jovyan/work/notebooks/explore.ipynb'

    # Check if archive_url is set
    archive_url = os.environ.get('archive_url')
    has_archive_url = bool(archive_url and archive_url.strip())

    # Load metadata if available
    metadata = None
    if has_archive_url:
        metadata = load_metadata()
        if not metadata:
            print("Warning: archive_url is set but metadata could not be loaded")

    # Process notebook
    process_notebook(template_path, output_path, has_archive_url, metadata)

    print(f"Processed notebook saved to: {output_path}")
    print(f"Archive URL present: {has_archive_url}")
    if metadata:
        print(f"Loaded metadata for: {metadata.get('title', 'Unknown')}")


if __name__ == '__main__':
    main()
