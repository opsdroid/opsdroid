FROM python:3.9.6-alpine3.14 as builder
LABEL maintainer="Jacob Tomlinson <jacob@tomlinson.email>"

WORKDIR /usr/src/app

ARG EXTRAS=[all,connector_matrix_e2e]
ENV DEPS_DIR=/usr/src/app/deps

# Copy source
COPY . .

# Install build tools and libraries to build OpsDroid and its dependencies.
RUN apk update \
    && apk add \
    build-base \
    cargo \
    gcc \
    git \
    g++ \
    libffi-dev \
    linux-headers \
    musl-dev \
    olm-dev \
    openssh-client \
    openssl-dev \
    python3-dev \
    zeromq-dev \
    && pip install --upgrade \
    build \
    pip \
    setuptools \
    setuptools-scm \
    wheel \
    && mkdir -p "${DEPS_DIR}" \
    && pip download --prefer-binary -d ${DEPS_DIR} .${EXTRAS} \
    && pip wheel -w ${DEPS_DIR} ${DEPS_DIR}/*.tar.gz \
    && count=$(ls -1 ${DEPS_DIR}/*.zip 2>/dev/null | wc -l) && if [ $count != 0 ]; then pip wheel -w ${DEPS_DIR} ${DEPS_DIR}/*.zip ; fi \
    && python -m build --wheel --outdir ${DEPS_DIR}

FROM python:3.9.6-alpine3.14 as runtime
LABEL maintainer="Jacob Tomlinson <jacob@tomlinson.email>"
LABEL maintainer="Rémy Greinhofer <remy.greinhofer@gmail.com>"

WORKDIR /usr/src/app

ARG EXTRAS=[all,connector_matrix_e2e]
ENV DEPS_DIR=/usr/src/app/deps

# Copy the pre-built dependencies.
COPY --from=builder ${DEPS_DIR}/*.whl ${DEPS_DIR}/

# Install Opsdroid using only pre-built dependencies.
RUN apk add --no-cache \
    git \
    olm \
    libzmq \
    && pip install --no-cache-dir --no-index -f ${DEPS_DIR} \
    $(find ${DEPS_DIR} -type f -name opsdroid-*-any.whl)${EXTRAS} \
    && rm -rf /tmp/* /var/tmp/* ${DEPS_DIR}/* \
    && adduser -u 1001 -D opsdroid

EXPOSE 8080

# Ensure the service runs as an unprivileged user.
USER opsdroid
ENTRYPOINT ["opsdroid"]
CMD ["start"]
