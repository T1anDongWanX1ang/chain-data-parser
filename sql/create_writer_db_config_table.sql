-- 创建writer_db_config表
CREATE TABLE IF NOT EXISTS `writer_db_config` (
  `component_id` bigint NOT NULL,
  `module_content` JSON DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`component_id`),
  KEY `i_component_id` (`component_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci; 