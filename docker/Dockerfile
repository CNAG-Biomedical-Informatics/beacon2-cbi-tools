FROM ubuntu:24.04 AS core

ARG BFF_TOOLS_VERSION=development
ARG VCS_REF=unknown

LABEL org.opencontainers.image.authors="Manuel Rueda <manuel.rueda@cnag.eu>" \
      org.opencontainers.image.source="https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools" \
      org.opencontainers.image.title="Beacon v2 CBI Tools" \
      org.opencontainers.image.version="${BFF_TOOLS_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="GPL-3.0-or-later"

ENV DEBIAN_FRONTEND=noninteractive \
    BFF_TOOLS_DATA=/beacon2-cbi-tools-data \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/beacon2-cbi-tools
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python3 -m pip install --break-system-packages --no-cache-dir .

WORKDIR /work
ENTRYPOINT ["bff-tools"]
CMD ["--help"]


FROM core AS annotation

RUN apt-get update && apt-get install -y --no-install-recommends \
    bcftools \
    default-jre-headless \
    libsnpsift-java \
    snpeff \
    && rm -rf /var/lib/apt/lists/*


FROM annotation AS runtime
