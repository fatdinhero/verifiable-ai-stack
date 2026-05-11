# Multi-stage build for agentsprotocol-validator
#
# Stage 1: build the Rust binary
# Stage 2: minimal runtime image

FROM rust:1.78-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    clang \
    libclang-dev \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Cache dependencies separately from source
COPY Cargo.toml Cargo.lock* ./
RUN mkdir src && echo 'fn main(){}' > src/main.rs && cargo build --release && rm -rf src

# Build the real binary
COPY src ./src
RUN touch src/main.rs && cargo build --release

# ── Runtime ──────────────────────────────────────────────────────────────────
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/agentsprotocol-validator /usr/local/bin/validator

# Default data directory
RUN mkdir -p /data

ENV AP_DATA_DIR=/data
ENV AP_LISTEN_ADDR=/ip4/0.0.0.0/tcp/9000
ENV AP_RPC_ADDR=0.0.0.0:8545

EXPOSE 9000 8545

ENTRYPOINT ["/usr/local/bin/validator"]
