CREATE DATABASE enwiktionary;
USE enwiktionary;
CREATE USER 'beland'@'localhost';
GRANT ALL PRIVILEGES ON enwiktionary TO 'beland'@'localhost' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON enwiktionary.* TO 'beland'@'localhost' WITH GRANT OPTION;
CREATE DATABASE enwiki;
USE enwiki;
GRANT ALL PRIVILEGES ON enwiki TO 'beland'@'localhost' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON enwiki.* TO 'beland'@'localhost' WITH GRANT OPTION;

