# Use Ubuntu 24.04 as the base image
FROM ubuntu:24.04

# Maintainer Information
LABEL maintainer="Manuel Rueda <manuel.rueda@cnag.eu>"

# Set non-interactive environment for apt operations
ENV DEBIAN_FRONTEND=noninteractive

# Install system packages required by bff-tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget git gnupg cpanminus gcc make libperl-dev \
    libbz2-dev zlib1g-dev libncurses5-dev libncursesw5-dev \
    liblzma-dev libcurl4-openssl-dev pkg-config libssl-dev \
    default-jre perl jq vim python3 python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install mongosh (MongoDB Shell)
RUN apt-get update && apt-get install -y --no-install-recommends gnupg && \
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - && \
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" \
        | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && apt-get install -y --no-install-recommends mongodb-mongosh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /usr/share/

# Clone the repository
RUN git clone https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools.git

# Remove Git metadata and CI configs to shrink image and avoid shipping them
RUN rm -rf beacon2-cbi-tools/.git beacon2-cbi-tools/.github beacon2-cbi-tools/.gitattributes beacon2-cbi-tools/.gitignore

# Remove docs
RUN rm -rf beacon2-cbi-tools/docs/ beacon2-cbi-tools/mkdocs.yml

# Install Python runtime dependencies and Perl dependencies from cpanfile
WORKDIR /usr/share/beacon2-cbi-tools
RUN python3 -m pip install --break-system-packages --no-cache-dir -r requirements.txt && \
    cpanm --notest --installdeps . && \
    rm -rf /root/.cpanm/work/*

# Add a non-root user
ARG GID=1000

RUN set -eux; \
    if getent group "${GID}" >/dev/null; then \
        GROUP_NAME="$(getent group "${GID}" | cut -d: -f1)"; \
    else \
        GROUP_NAME="dockeruser"; \
        groupadd -g "${GID}" "${GROUP_NAME}"; \
    fi; \
    useradd --create-home --no-log-init -u "${UID}" -g "${GROUP_NAME}" dockeruser

# Uncomment the following line to run the container as dockeruser
# USER dockeruser
