#!/bin/bash

# Set some variables
first_name=aiida
last_name=renku
email="aiida@renku2"
aiida_profile="aiida-renku"
institution="AiiDA-RenkuLab"

project_dir="$(pwd)"
repo_dir="${project_dir}/aiida_data"
mkdir "$repo_dir"

# Export AIIDA_PATH environment variable
export AIIDA_PATH=$HOME

if [ -n "$archive_url" ]; then

archive_name="${archive_url#*filename=}"
archive_path="${repo_dir}/${archive_name}"

echo "WGET -O $archive_path $archive_url"
wget -O "$archive_path" "$archive_url"

rabbitmq-server -detached

# With archive_url, generate profile using `core.sqlite_zip` backend
verdi profile show $aiida_profile 2> /dev/null || verdi profile setup core.sqlite_zip \
    --profile-name $aiida_profile \
    --first-name "$first_name" \
    --last-name "$last_name" \
    --email "$email" \
    --institution $institution \
    --set-as-default \
    --non-interactive \
    --filepath "$archive_path"

else

# Without archive_url, generate profile using `core.sqlite_dos` backend
verdi profile show $aiida_profile 2> /dev/null || verdi profile setup core.sqlite_dos \
    --profile-name $aiida_profile \
    --first-name "$first_name" \
    --last-name "$last_name" \
    --email "$email" \
    --institution $institution \
    --set-as-default \
    --non-interactive

fi

verdi config set warnings.rabbitmq_version False
verdi profile configure-rabbitmq

# Process README.md to replace placeholders
# if [ -f "README.md" ]; then
#     # Replace archive section placeholder
#     if [ -n "$archive_url" ]; then
#         sed -i "s|<!-- ARCHIVE_SECTION -->|This project comes with a Jupyter notebook for importing and exploring an [AiiDA archive]($archive_url).|g" README.md
#     else
#         # Remove the placeholder line if no archive_url
#         sed -i '/<!-- ARCHIVE_SECTION -->/d' README.md
#     fi

#     # Replace other simple placeholders
#     if [ -n "$PROJECT_NAME" ]; then
#         sed -i "s|PROJECT_NAME_PLACEHOLDER|$PROJECT_NAME|g" README.md
#     fi

#     if [ -n "$PROJECT_DESCRIPTION" ]; then
#         sed -i "s|PROJECT_DESCRIPTION_PLACEHOLDER|$PROJECT_DESCRIPTION|g" README.md
#     fi
# fi