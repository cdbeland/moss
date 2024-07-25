#!/usr/bin/bash

# RUN TIME

# About 6 hours (as of July 2024)

# FIRST TIME SETUP

# Change "beland" to the Unix user you want to set up for

# sudo su
# apt-get install mariadb-server
#  (Fedora: dnf install mariadb-server)
# service mariadb restart
# mysql
#  CREATE DATABASE enwiktionary;
#  USE enwiktionary;
#  CREATE USER 'beland'@'localhost';
#  GRANT ALL PRIVILEGES ON enwiktionary TO 'beland'@'localhost' WITH GRANT OPTION;
#  GRANT ALL PRIVILEGES ON enwiktionary.* TO 'beland'@'localhost' WITH GRANT OPTION;
#  CREATE DATABASE enwiki;
#  USE enwiki;
#  GRANT ALL PRIVILEGES ON enwiki TO 'beland'@'localhost' WITH GRANT OPTION;
#  GRANT ALL PRIVILEGES ON enwiki.* TO 'beland'@'localhost' WITH GRANT OPTION;

# Optimization suggestions for my.cnf:
#
# [mysqld]
#
# # OPTIMIZE FOR LOADING LARGE DUMPS
# max_allowed_packet=1GB
#
# # THESE SACRIFICE DATA INTEGRITY FOR PERFORMANCE WHEN LOADING LARGE DUMPS
# innodb_buffer_pool_size = 4G
# innodb_log_buffer_size = 256M
# innodb_log_file_size = 1G
# innodb_flush_log_at_trx_commit = 0
# innodb_doublewrite = 0
#
# # Optimize for SSD
# # https://dev.mysql.com/doc/refman/5.6/en/optimizing-innodb-diskio.html
# innodb_checksum_algorithm = crc32
# innodb_flush_neighbors = 0
# innodb_io_capacity = 1000
# innodb_log_compressed_pages = OFF
# binlog_row_image = minimal
# # innodb_flush_method parameter = O_DSYNC  # Tries to open too many files

# sudo mkdir -p /var/local/moss/bulk-wikipedia
# sudo chown -R $USER /var/local/moss

set -e

echo `date`
echo "Dropping walled garden data..."
# Both can't fit in storage at the same time

echo "DROP TABLE IF EXISTS page;" | mysql -D enwiki
echo "DROP TABLE IF EXISTS pagelinks;" | mysql -D enwiki
echo "DROP TABLE IF EXISTS named_page_links;" | mysql -D enwiki

echo `date`
echo "Dropping tables to be regenerated..."
# Breathing room while regenerating

echo "DROP TABLE IF EXISTS page_categories;" | mysql -D enwiktionary
echo "DROP TABLE IF EXISTS categorylinks;" | mysql -D enwiktionary
echo "DROP TABLE IF EXISTS page;" | mysql -D enwiktionary
echo "DROP TABLE IF EXISTS page_categories;" | mysql -D enwiki

echo `date`

./update_downloads_parallel1.sh >& /var/local/moss/bulk-wikipedia/download-parallel1.log &
./update_downloads_parallel2.sh >& /var/local/moss/bulk-wikipedia/download-parallel2.log &
# 4 and 5 are kicked off from 2

# ./update_downloads_parallel3.sh >& /bulk-wikipedia/download-parallel3.log &
# Only used by chemical formula report, takes more than 24 hours,
# disabled until performance can be improved or the report is manually
# run.

echo `date`
echo "Parallel scripts launched."
