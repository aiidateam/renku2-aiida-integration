# For finding latest versions of the base image see
# https://github.com/SwissDataScienceCenter/renkulab-docker
FROM renku/renkulab-py:3.11-0.25.0

# Effectively disable RabbitMQ `consumer_timeout`
ENV RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS="-rabbit consumer_timeout undefined"

# Uncomment and adapt if code is to be included in the image
# COPY src /code/src

# Uncomment and adapt if your R or python packages require extra linux (ubuntu) software
# e.g. the following installs apt-utils and vim; each pkg on its own line, all lines
# except for the last end with backslash '\' to continue the RUN line
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata

USER ${NB_USER}

# # Install AiiDA and the services
# RUN conda install -c conda-forge aiida-core=2.7.1 aiida-core.services=2.7.1 -y

# Install AiiDA with architecture-specific handling
RUN ARCH=$(uname -m) && \
    echo "Building for architecture: $ARCH" && \
    if [ "$ARCH" = "aarch64" ]; then \
        echo "ARM64: Installing AiiDA core (services may have limited availability)" && \
        conda install -c conda-forge aiida-core=2.7.1 -y && \
        (conda install -c conda-forge aiida-core.services=2.7.1 -y || \
         echo "Note: aiida-core.services not fully available for ARM64"); \
    else \
        echo "AMD64: Installing AiiDA with full services" && \
        conda install -c conda-forge aiida-core=2.7.1 aiida-core.services=2.7.1 -y; \
    fi

RUN conda clean -y --all && \
    conda env export -n "root"

RUN pip install --upgrade typing_extensions

# RENKU_VERSION determines the version of the renku CLI
# that will be used in this image. To find the latest version,
# visit https://pypi.org/project/renku/#history.

# For local build
ARG RENKU_VERSION="2.9.4"

