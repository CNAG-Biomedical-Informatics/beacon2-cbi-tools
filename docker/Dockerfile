FROM ubuntu:24.04 AS core

LABEL maintainer="Manuel Rueda <manuel.rueda@cnag.eu>"

ENV DEBIAN_FRONTEND=noninteractive \
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
