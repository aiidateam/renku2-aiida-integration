#!/bin/bash

# Set some variables
read -ra name_array <<< "$(git config user.name | tr -d "'")"
first_name="${name_array[0]}"
last_name="${name_array[@]:1}"
last_name="${last_name// / }"
email="$(git config user.email)"
aiida_profile="aiida_renku"
institution="AiiDA-RenkuLab"

project_dir="$(pwd)"
repo_dir="${project_dir}/aiida_data"
mkdir "$repo_dir"

# Export AIIDA_PATH environment variable
export AIIDA_PATH=$repo_dir

if [ -n "$ARCHIVE_URL" ]; then

archive_name="${ARCHIVE_URL#*filename=}"
archive_path="${repo_dir}/${archive_name}"

wget -O "$archive_path" "$ARCHIVE_URL"

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
rabbitmq-server -detached

# Process README.md to replace placeholders
# if [ -f "README.md" ]; then
#     # Replace archive section placeholder
#     if [ -n "$ARCHIVE_URL" ]; then
#         sed -i "s|<!-- ARCHIVE_SECTION -->|This project comes with a Jupyter notebook for importing and exploring an [AiiDA archive]($ARCHIVE_URL).|g" README.md
#     else
#         # Remove the placeholder line if no ARCHIVE_URL
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