#!/usr/bin/env bash
set -e
/opt/ravenor/venv/bin/python3 /opt/ravenor/collector.py
rclone copy /opt/ravenor/corpus gdrive:ravenor-corpus
