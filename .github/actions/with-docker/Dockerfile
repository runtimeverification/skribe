ARG K_VERSION
FROM runtimeverificationinc/kframework-k:ubuntu-noble-${K_VERSION}

ARG PYTHON_VERSION=3.10

RUN    apt-get -y update             \
    && apt-get -y upgrade            \
    && apt-get -y install            \
         curl wget libssl-dev        \
         libsecp256k1-dev            \  
         software-properties-common  \
    && apt-get -y clean              \
    && add-apt-repository ppa:ethereum/ethereum \
    && apt-get update                \
    && apt-get install solc

ARG USER_ID=9876
ARG GROUP_ID=9876
RUN    groupadd -g ${GROUP_ID} user \
    && useradd -m -u ${USER_ID} -s /bin/bash -g user user

USER user
WORKDIR /home/user

ENV PATH=/home/user/.local/bin:${PATH}

ARG UV_VERSION
RUN    curl -LsSf https://astral.sh/uv/$UV_VERSION/install.sh | sh \
    && uv --version

RUN wget -O rustup.sh https://sh.rustup.rs && \
    chmod +x rustup.sh && \
    ./rustup.sh --verbose --target wasm32-unknown-unknown -y

ENV PATH="/home/user/.cargo/bin:${PATH}"

RUN cargo install --force cargo-stylus
RUN rustup default 1.83.0
RUN rustup target add wasm32-unknown-unknown --toolchain 1.83.0

RUN curl -L https://foundry.paradigm.xyz | bash
ENV PATH="/home/user/.foundry/bin:${PATH}"
RUN foundryup
