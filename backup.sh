#!/bin/bash
BACKUP_DIR=/opt/poisv/backups
mkdir -p $BACKUP_DIR
sqlite3 /opt/poisv/data/incidents.db ".backup $BACKUP_DIR/incidents-$(date +%Y%m%d).db"
find $BACKUP_DIR -name "incidents-*.db" -mtime +7 -delete