DROP TABLE IF EXISTS `pagelinks`;
SET character_set_client = utf8;
CREATE TABLE `pagelinks` (
  `pl_from` int(8) unsigned NOT NULL DEFAULT 0,
  `pl_namespace` int(11) NOT NULL DEFAULT 0,
  `pl_title` varbinary(255) NOT NULL DEFAULT '',
  `pl_from_namespace` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=binary ROW_FORMAT=COMPRESSED;
