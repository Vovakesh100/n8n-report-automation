# n8n plus python3, needed by the Execute Command node (see docs/DECISIONS.md, T7 decision).
FROM docker.n8n.io/n8nio/n8n:latest

USER root
RUN apk add --no-cache python3
USER node
