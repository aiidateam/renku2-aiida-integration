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

temp="${archive_url#*/files/}"
archive_name="${temp%/content*}"
archive_path="${repo_dir}/${archive_name}"

wget -O "$archive_path" "$archive_url"

# With archive_url, generate profile using `core.sqlite_zip` backend
verdi profile show $aiida_profile 2> /dev/null || verdi profile setup core.sqlite_zip \
    --profile-name $aiida_profile \
    --first-name "$first_name" \
    --last-name "$last_name" \
    --email "$email" \
    --institution $institution \
    --set-as-default \
    --non-interactive \
    --no-use-rabbitmq \
    --filepath "$archive_path"

else

# RMQ
rabbitmq-server -detached
verdi profile configure-rabbitmq
verdi config set warnings.rabbitmq_version False

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
