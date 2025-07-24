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
    """
    Normalize archive URL to handle various Materials Cloud Archive URL formats.
    Converts all formats to: https://archive.materialscloud.org/records/{record_id}/files/{filename.aiida}
    """
    if not archive_url or not archive_url.strip():
        return archive_url

    archive_url = archive_url.strip()

    # Remove common suffixes
    suffixes_to_remove = ['/content', '/download', '?download=1', '?dl=1']
    for suffix in suffixes_to_remove:
        if archive_url.endswith(suffix):
            archive_url = archive_url.rstrip(suffix)

    # Remove trailing slashes
    archive_url = archive_url.rstrip('/')

    # Parse URL components
    parsed = urlparse(archive_url)

    # Ensure we're dealing with a Materials Cloud Archive URL
    if 'materialscloud.org' not in parsed.netloc:
        print(f"Warning: URL doesn't appear to be from Materials Cloud Archive: {archive_url}")
        return archive_url

    # Handle different URL patterns
    path = parsed.path

    # CRITICAL FIX: Handle API URLs that return metadata instead of file content
    # Convert: /api/records/{record_id}/files/{filename.aiida}
    # To:      /records/{record_id}/files/{filename.aiida}
    api_match = re.match(r'/api/records/([^/]+)/files/([^/?]+)', path)
    if api_match:
        record_id = api_match.group(1)
        filename = unquote(api_match.group(2))  # URL decode

        # Ensure filename ends with .aiida
        if not filename.endswith('.aiida'):
            print(f"Warning: File doesn't appear to be an AiiDA archive: {filename}")
            return archive_url

        # Reconstruct as download URL (remove /api/)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        clean_url = f"{base_url}/records/{record_id}/files/{filename}"

        print(f"Converted API URL to download URL: {archive_url} -> {clean_url}")
        return clean_url

    # Pattern 1: Already in correct format
    # https://archive.materialscloud.org/records/{record_id}/files/{filename.aiida}
    if re.match(r'/records/[^/]+/files/[^/]+\.aiida


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

    # Normalize the URL to handle various formats
    print(f"Original URL: {archive_url}")
    normalized_url = normalize_archive_url(archive_url)

    if normalized_url != archive_url:
        print(f"Normalized URL: {normalized_url}")

    # Validate that we have a .aiida file URL
    if not normalized_url.endswith(".aiida"):
        print(f"Error: URL does not point to an .aiida file: {normalized_url}")
        print("Please provide a direct link to an AiiDA archive file (.aiida)")

        # Try to extract record ID anyway to give helpful feedback
        record_id = extract_record_id_from_url(normalized_url)
        if record_id:
            print(f"Browse files at: https://archive.materialscloud.org/records/{record_id}")
        sys.exit(1)

    # Extract record ID from normalized URL
    record_id = extract_record_id_from_url(normalized_url)
    if not record_id:
        print(f"Error: Could not extract record ID from URL: {normalized_url}")
        print("Expected format: https://archive.materialscloud.org/records/{record_id}/files/{filename.aiida}")
        sys.exit(1)

    print(f"Processing record: {record_id}")

    # Fetch metadata
    metadata = fetch_mca_metadata(record_id)
    if not metadata:
        print("Failed to fetch metadata from Materials Cloud Archive API")
        sys.exit(1)

    # Add archive-specific information
    archive_filename = get_archive_filename_from_url(normalized_url)
    if archive_filename:
        metadata["archive_filename"] = archive_filename
        metadata["aiida_profile"] = os.path.splitext(archive_filename)[0]  # Remove .aiida extension
    else:
        print("Warning: Could not extract filename from URL")

    # Save the normalized URL (this is the key fix!)
    metadata["archive_url"] = normalized_url

    # Save metadata to JSON file
    output_file = "/tmp/mca_metadata.json"
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Metadata saved to: {output_file}")
    print(f"📊 Title: {metadata['title']}")
    print(f"🔗 DOI: {metadata.get('doi', 'Not available')}")
    print(f"📋 MCA Entry: {metadata['mca_entry']}")
    print(f"📁 Archive file: {metadata.get('archive_filename', 'Unknown')}")
    print(f"🌐 Archive URL: {metadata['archive_url']}")

    # Display available files info
    aiida_files = [f for f in metadata.get('files', []) if f.get('type') == 'aiida_archive']
    if len(aiida_files) > 1:
        print(f"\n📚 Note: This record contains {len(aiida_files)} AiiDA archive files:")
        for f in aiida_files[:5]:  # Show first 5
            size_mb = f.get('size', 0) / (1024 * 1024) if f.get('size') else 0
            print(f"   • {f['filename']} ({size_mb:.1f} MB)")
        if len(aiida_files) > 5:
            print(f"   ... and {len(aiida_files) - 5} more files")


if __name__ == "__main__":
    main()
, path):
        return archive_url

    # Pattern 2: Old format with /record/ (singular)
    # https://archive.materialscloud.org/record/{record_id}
    old_record_match = re.match(r'/record/([^/?]+)', path)
    if old_record_match:
        record_id = old_record_match.group(1)
        print(f"Converting old record URL format for record: {record_id}")
        # We can't determine the specific file from just a record URL
        # Return the record URL and let the user specify the file
        print(f"Warning: Record URL provided instead of direct file URL.")
        print(f"Please provide the direct file URL from: https://archive.materialscloud.org/records/{record_id}")
        return archive_url

    # Pattern 3: Modern format but missing file specification
    # https://archive.materialscloud.org/records/{record_id}
    records_only_match = re.match(r'/records/([^/?]+)/?


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

    # Normalize the URL to handle various formats
    print(f"Original URL: {archive_url}")
    normalized_url = normalize_archive_url(archive_url)

    if normalized_url != archive_url:
        print(f"Normalized URL: {normalized_url}")

    # Validate that we have a .aiida file URL
    if not normalized_url.endswith(".aiida"):
        print(f"Error: URL does not point to an .aiida file: {normalized_url}")
        print("Please provide a direct link to an AiiDA archive file (.aiida)")

        # Try to extract record ID anyway to give helpful feedback
        record_id = extract_record_id_from_url(normalized_url)
        if record_id:
            print(f"Browse files at: https://archive.materialscloud.org/records/{record_id}")
        sys.exit(1)

    # Extract record ID from normalized URL
    record_id = extract_record_id_from_url(normalized_url)
    if not record_id:
        print(f"Error: Could not extract record ID from URL: {normalized_url}")
        print("Expected format: https://archive.materialscloud.org/records/{record_id}/files/{filename.aiida}")
        sys.exit(1)

    print(f"Processing record: {record_id}")

    # Fetch metadata
    metadata = fetch_mca_metadata(record_id)
    if not metadata:
        print("Failed to fetch metadata from Materials Cloud Archive API")
        sys.exit(1)

    # Add archive-specific information
    archive_filename = get_archive_filename_from_url(normalized_url)
    if archive_filename:
        metadata["archive_filename"] = archive_filename
        metadata["aiida_profile"] = os.path.splitext(archive_filename)[0]  # Remove .aiida extension
    else:
        print("Warning: Could not extract filename from URL")

    # Save the normalized URL (this is the key fix!)
    metadata["archive_url"] = normalized_url

    # Save metadata to JSON file
    output_file = "/tmp/mca_metadata.json"
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Metadata saved to: {output_file}")
    print(f"📊 Title: {metadata['title']}")
    print(f"🔗 DOI: {metadata.get('doi', 'Not available')}")
    print(f"📋 MCA Entry: {metadata['mca_entry']}")
    print(f"📁 Archive file: {metadata.get('archive_filename', 'Unknown')}")
    print(f"🌐 Archive URL: {metadata['archive_url']}")

    # Display available files info
    aiida_files = [f for f in metadata.get('files', []) if f.get('type') == 'aiida_archive']
    if len(aiida_files) > 1:
        print(f"\n📚 Note: This record contains {len(aiida_files)} AiiDA archive files:")
        for f in aiida_files[:5]:  # Show first 5
            size_mb = f.get('size', 0) / (1024 * 1024) if f.get('size') else 0
            print(f"   • {f['filename']} ({size_mb:.1f} MB)")
        if len(aiida_files) > 5:
            print(f"   ... and {len(aiida_files) - 5} more files")


if __name__ == "__main__":
    main()
, path)
    if records_only_match:
        record_id = records_only_match.group(1)
        print(f"Warning: Records URL provided without specific file.")
        print(f"Please specify the exact .aiida file from: https://archive.materialscloud.org/records/{record_id}")
        return archive_url

    # Pattern 4: Direct file URL with extra path components or parameters
    # Extract record_id and filename if possible
    records_files_match = re.match(r'/records/([^/]+)/files/([^/?]+)', path)
    if records_files_match:
        record_id = records_files_match.group(1)
        filename = unquote(records_files_match.group(2))  # URL decode

        # Ensure filename ends with .aiida
        if not filename.endswith('.aiida'):
            print(f"Warning: File doesn't appear to be an AiiDA archive: {filename}")
            return archive_url

        # Reconstruct clean URL
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        clean_url = f"{base_url}/records/{record_id}/files/{filename}"

        if clean_url != archive_url:
            print(f"Normalized URL: {archive_url} -> {clean_url}")

        return clean_url

    # Pattern 5: Handle URLs with additional query parameters
    if '?' in archive_url:
        clean_url = archive_url.split('?')[0]
        if clean_url != archive_url:
            print(f"Removed query parameters: {archive_url} -> {clean_url}")
            return normalize_archive_url(clean_url)  # Recursive call to handle the cleaned URL

    # If we can't parse it, return as-is with a warning
    print(f"Warning: Unable to normalize URL format: {archive_url}")
    print("Expected format: https://archive.materialscloud.org/records/{record_id}/files/{filename.aiida}")

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

    # Normalize the URL to handle various formats
    print(f"Original URL: {archive_url}")
    normalized_url = normalize_archive_url(archive_url)

    if normalized_url != archive_url:
        print(f"Normalized URL: {normalized_url}")

    # Validate that we have a .aiida file URL
    if not normalized_url.endswith(".aiida"):
        print(f"Error: URL does not point to an .aiida file: {normalized_url}")
        print("Please provide a direct link to an AiiDA archive file (.aiida)")

        # Try to extract record ID anyway to give helpful feedback
        record_id = extract_record_id_from_url(normalized_url)
        if record_id:
            print(f"Browse files at: https://archive.materialscloud.org/records/{record_id}")
        sys.exit(1)

    # Extract record ID from normalized URL
    record_id = extract_record_id_from_url(normalized_url)
    if not record_id:
        print(f"Error: Could not extract record ID from URL: {normalized_url}")
        print("Expected format: https://archive.materialscloud.org/records/{record_id}/files/{filename.aiida}")
        sys.exit(1)

    print(f"Processing record: {record_id}")

    # Fetch metadata
    metadata = fetch_mca_metadata(record_id)
    if not metadata:
        print("Failed to fetch metadata from Materials Cloud Archive API")
        sys.exit(1)

    # Add archive-specific information
    archive_filename = get_archive_filename_from_url(normalized_url)
    if archive_filename:
        metadata["archive_filename"] = archive_filename
        metadata["aiida_profile"] = os.path.splitext(archive_filename)[0]  # Remove .aiida extension
    else:
        print("Warning: Could not extract filename from URL")

    # Save the normalized URL (this is the key fix!)
    metadata["archive_url"] = normalized_url

    # Save metadata to JSON file
    output_file = "/tmp/mca_metadata.json"
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Metadata saved to: {output_file}")
    print(f"📊 Title: {metadata['title']}")
    print(f"🔗 DOI: {metadata.get('doi', 'Not available')}")
    print(f"📋 MCA Entry: {metadata['mca_entry']}")
    print(f"📁 Archive file: {metadata.get('archive_filename', 'Unknown')}")
    print(f"🌐 Archive URL: {metadata['archive_url']}")

    # Display available files info
    aiida_files = [f for f in metadata.get('files', []) if f.get('type') == 'aiida_archive']
    if len(aiida_files) > 1:
        print(f"\n📚 Note: This record contains {len(aiida_files)} AiiDA archive files:")
        for f in aiida_files[:5]:  # Show first 5
            size_mb = f.get('size', 0) / (1024 * 1024) if f.get('size') else 0
            print(f"   • {f['filename']} ({size_mb:.1f} MB)")
        if len(aiida_files) > 5:
            print(f"   ... and {len(aiida_files) - 5} more files")


if __name__ == "__main__":
    main()