# For finding latest versions of the base image see
# https://github.com/SwissDataScienceCenter/renkulab-docker
FROM renku/renkulab-py:3.11-0.25.0

# Uncomment and adapt if your R or python packages require extra linux (ubuntu) software
# e.g. the following installs apt-utils and vim; each pkg on its own line, all lines
# except for the last end with backslash '\' to continue the RUN line
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata

USER ${NB_USER}

# Install AiiDA without services
RUN pip install --no-cache-dir aiida-core==2.7.1

# RENKU_VERSION determines the version of the renku CLI
# that will be used in this image. To find the latest version,
# visit https://pypi.org/project/renku/#history.

# For local build
ARG RENKU_VERSION="2.9.4"

