"""
Script to fetch metadata from Materials Cloud Archive (MCA)
"""

import json
import re
import requests
import sys
import os
import argparse
from urllib.parse import urlparse, unquote


def extract_record_id_from_url(archive_url):
    """Extract MCA record ID from archive file URL"""
    try:
        # Parse URL pattern: https://archive.materialscloud.org/records/{record_id}/files/filename.aiida
        parsed = urlparse(archive_url)

        # Extract from modern path pattern (e.g., /records/yf0rj-w3r97/files/...)
        records_match = re.search(r"/records/([^/]+)/", parsed.path)
        if records_match:
            record_id = records_match.group(1)
            print(f"Extracted record ID: {record_id}")
            return record_id

        print(f"Could not extract record ID from URL: {archive_url}")
        return None
    except Exception as e:
        print(f"Error extracting record ID: {e}")
        return None


def fetch_mca_metadata(record_id):
    """Fetch metadata from MCA using InvenioRDM API"""
    try:
        base_url = "https://archive.materialscloud.org"
        api_url = f"{base_url}/api/records/{record_id}"

        print(f"Fetching metadata from: {api_url}")
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract relevant metadata
        metadata = {
            "doi": None,
            "title": data.get("metadata", {}).get("title", ""),
            "mca_entry": record_id,  # Use the actual record ID
            "created": data.get("created", ""),
            "files": [],
        }

        # Extract DOI from multiple possible locations
        identifiers = data.get("metadata", {}).get("identifiers", [])
        for identifier in identifiers:
            if identifier.get("scheme") == "doi":
                metadata["doi"] = identifier.get("identifier")
                break

        # Alternative DOI location in pids
        if not metadata["doi"]:
            pids = data.get("pids", {})
            if "doi" in pids:
                metadata["doi"] = pids["doi"]["identifier"]

        # Extract file information
        files_data = data.get("files", {}).get("entries", {})
        for filename, file_info in files_data.items():
            file_entry = {
                "filename": filename,
                "size": file_info.get("size"),
                "checksum": file_info.get("checksum"),
                "key": file_info.get("key", filename),
            }

            if filename.endswith(".aiida"):
                file_entry["type"] = "aiida_archive"
            else:
                file_entry["type"] = "other"

            metadata["files"].append(file_entry)

        return metadata

    except requests.exceptions.RequestException as e:
        print(f"Error fetching metadata from MCA API: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response content: {e.response.text[:500]}")
        return None
    except Exception as e:
        print(f"Error processing MCA metadata: {e}")
        return None


def get_archive_filename_from_url(archive_url):
    """Extract archive filename from URL"""
    try:
        parsed = urlparse(archive_url)

        # Extract filename from /files/ path: /records/{record_id}/files/{filename.aiida}
        files_match = re.search(r"/files/([^/?]+)", parsed.path)
        if files_match:
            filename = unquote(files_match.group(1))  # URL decode the filename
            print(f"Extracted filename: {filename}")
            return filename

        print(f"Could not extract filename from URL: {archive_url}")
        return None
    except Exception as e:
        print(f"Error extracting filename: {e}")
        return None


def normalize_archive_url(archive_url):
    """Normalize archive URL by removing /content suffix and handling different URL formats"""
    # Remove trailing /content if present
    if archive_url.endswith("/content"):
        archive_url = archive_url.rstrip("/content")

    return archive_url


def get_archive_url():
    """Get archive URL from command line arguments or environment variable"""
    parser = argparse.ArgumentParser(description="Fetch metadata from Materials Cloud Archive (MCA)")
    parser.add_argument("--archive-url", help="URL to the archive file (.aiida)")

    args = parser.parse_args()

    # Priority: command line argument, then environment variable
    archive_url = args.archive_url or os.environ.get("archive_url")

    if not archive_url:
        print("Error: No archive URL provided.")
        print("Usage:")
        print("  python script.py --archive-url <archive_url>")
        print("  export archive_url=<archive_url> && python script.py")
        sys.exit(1)

    return archive_url


def main():
    archive_url = get_archive_url()

    # Normalize the URL (remove /content suffix)
    archive_url = normalize_archive_url(archive_url)

    if not archive_url.endswith(".aiida"):
        print("archive_url does not point to an .aiida file")
        sys.exit(1)

    # Extract record ID from URL
    record_id = extract_record_id_from_url(archive_url)
    if not record_id:
        print(f"Could not extract record ID from URL: {archive_url}")
        sys.exit(1)

    print(f"Fetching metadata for record: {record_id}")

    # Fetch metadata
    metadata = fetch_mca_metadata(record_id)
    if not metadata:
        print("Failed to fetch metadata")
        sys.exit(1)

    # Add archive-specific information
    archive_filename = get_archive_filename_from_url(archive_url)
    if archive_filename:
        metadata["archive_filename"] = archive_filename
        metadata["aiida_profile"] = os.path.splitext(archive_filename)[0]  # Remove .aiida extension

    # Save metadata to JSON file
    output_file = "/tmp/mca_metadata.json"
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata saved to: {output_file}")
    print(f"Title: {metadata['title']}")
    print(f"DOI: {metadata['doi']}")
    print(f"MCA Entry: {metadata['mca_entry']}")
    print(f"Archive file: {metadata.get('archive_filename', 'Unknown')}")


if __name__ == "__main__":
    main()
