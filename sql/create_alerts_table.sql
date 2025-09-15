-- 告警模块数据库表创建脚本
-- 创建时间: 2025-09-15
-- 作者: 产品经理 John

-- 创建告警表
CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '告警ID',
    message VARCHAR(255) NOT NULL COMMENT '告警消息',
    alert_type VARCHAR(50) DEFAULT 'system' COMMENT '告警类型：system/api/performance',
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium' COMMENT '严重程度',
    source VARCHAR(100) DEFAULT 'chain-parser' COMMENT '告警来源',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    is_cleared BOOLEAN DEFAULT FALSE COMMENT '是否已清除',
    cleared_at TIMESTAMP NULL COMMENT '清除时间',
    cleared_by VARCHAR(100) NULL COMMENT '清除人',
    
    -- 索引优化
    INDEX idx_is_cleared (is_cleared),
    INDEX idx_created_at (created_at),
    INDEX idx_severity (severity),
    INDEX idx_alert_type (alert_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统告警表';

-- 插入测试数据
INSERT INTO alerts (message, alert_type, severity, source) VALUES
('API响应时间超过3秒阈值', 'performance', 'high', 'monitoring'),
('Base链API调用失败', 'api', 'critical', 'blockchain-service'),
('缓存命中率低于70%', 'performance', 'medium', 'redis'),
('数据库连接池使用率过高', 'system', 'high', 'database'),
('磁盘空间使用率超过80%', 'system', 'medium', 'server'),
('内存使用率超过90%', 'system', 'critical', 'server'),
('Ethereum链调用超时', 'api', 'high', 'blockchain-service'),
('代理合约检测失败', 'api', 'medium', 'blockchain-service');