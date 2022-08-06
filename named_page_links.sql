DROP TABLE IF EXISTS `named_page_links`;
CREATE TABLE `named_page_links` (
  `pl_from` varbinary(255),
  `pl_to` varbinary(255)
) ENGINE=Aria DEFAULT CHARSET=binary ROW_FORMAT=COMPRESSED;
