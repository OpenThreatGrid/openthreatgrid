# go-mmproxy — restores the real client IP behind a PROXY-protocol load balancer.
# Used as a sidecar in front of Cowrie (which has no native PROXY support).
# Also ships iproute2 so the same image can run the init container that sets up
# the loopback routing table required for transparent proxying.
FROM golang:1.23-bookworm AS build
RUN go install github.com/path-network/go-mmproxy@latest

FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /go/bin/go-mmproxy /usr/local/bin/go-mmproxy
ENTRYPOINT ["/usr/local/bin/go-mmproxy"]
