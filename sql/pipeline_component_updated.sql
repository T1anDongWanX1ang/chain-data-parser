-- 更新后的 pipeline_component 表结构
-- 字段名从 next_component_id 改为 pre_component_id

CREATE TABLE `pipeline_component` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `pipeline_id` bigint NOT NULL,
  `pre_component_id` bigint DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `type` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `i_pipeline_id` (`pipeline_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 如果需要从旧表迁移数据，可以使用以下语句：
-- ALTER TABLE `pipeline_component` CHANGE `next_component_id` `pre_component_id` bigint DEFAULT NULL;
