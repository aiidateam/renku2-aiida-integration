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

# install the python dependencies
COPY environment.yml /tmp/
RUN mamba env update -q -f /tmp/environment.yml

RUN /opt/conda/bin/pip install --upgrade pip && \
    conda clean -y --all && \
    conda env export -n "root"

RUN pip install --upgrade pip

RUN pip install aiida-core~=2.7.0

# RENKU_VERSION determines the version of the renku CLI
# that will be used in this image. To find the latest version,
# visit https://pypi.org/project/renku/#history.

# For local build
ARG RENKU_VERSION="2.9.4"

