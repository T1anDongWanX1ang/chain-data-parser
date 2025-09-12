-- 添加逻辑删除字段到 pipeline 表
ALTER TABLE `pipeline` 
ADD COLUMN `disabled` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否禁用(逻辑删除)';

-- 添加逻辑删除字段到 pipelin_classification 表
ALTER TABLE `pipelin_classification` 
ADD COLUMN `disabled` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否禁用(逻辑删除)';

-- 创建索引以提高查询性能
CREATE INDEX idx_pipeline_disabled ON `pipeline` (`disabled`);
CREATE INDEX idx_pipelin_classification_disabled ON `pipelin_classification` (`disabled`);

-- 为现有记录设置默认值（确保现有数据不被意外删除）
UPDATE `pipeline` SET `disabled` = 0 WHERE `disabled` IS NULL;
UPDATE `pipelin_classification` SET `disabled` = 0 WHERE `disabled` IS NULL;
