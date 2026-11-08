# n8n plus python3, needed by the Execute Command node (see docs/DECISIONS.md, T7 decision).
# The n8n image is a hardened Alpine image: no apk usage, no python3. So python3 is copied
# from the official Alpine (musl) Python image. The helper uses only the stdlib.
FROM python:3.12-alpine AS python

FROM n8nio/n8n:2.46.6
COPY --from=python /usr/local /usr/local
USER node
