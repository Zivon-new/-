/*
 Navicat MySQL Dump SQL

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 80044 (8.0.44)
 Source Host           : localhost:3306
 Source Schema         : price_test_v2

 Target Server Type    : MySQL
 Target Server Version : 80044 (8.0.44)
 File Encoding         : 65001

 Date: 05/01/2026 16:38:31
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for fee_items
-- ----------------------------
DROP TABLE IF EXISTS `fee_items`;
CREATE TABLE `fee_items`  (
  `费用ID` int NOT NULL AUTO_INCREMENT,
  `代理路线ID` int NOT NULL,
  `费用类型` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `单价` decimal(18, 2) NULL DEFAULT 0.00,
  `单位` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `数量` decimal(18, 0) NULL DEFAULT 0,
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'RMB',
  `原币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `人民币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`费用ID`) USING BTREE,
  INDEX `fk_fee_items_route_agents`(`代理路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_fee_items_route_agents` FOREIGN KEY (`代理路线ID`) REFERENCES `route_agents` (`代理路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for fee_total
-- ----------------------------
DROP TABLE IF EXISTS `fee_total`;
CREATE TABLE `fee_total`  (
  `整单费用ID` int NOT NULL AUTO_INCREMENT,
  `代理路线ID` int NOT NULL,
  `费用名称` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `原币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'RMB',
  `人民币金额` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`整单费用ID`) USING BTREE,
  INDEX `fk_fee_total_route_agents`(`代理路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_fee_total_route_agents` FOREIGN KEY (`代理路线ID`) REFERENCES `route_agents` (`代理路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for forex_rate
-- ----------------------------
DROP TABLE IF EXISTS `forex_rate`;
CREATE TABLE `forex_rate`  (
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `汇率` decimal(18, 8) NOT NULL,
  `更新时间` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`币种`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for goods_details
-- ----------------------------
DROP TABLE IF EXISTS `goods_details`;
CREATE TABLE `goods_details`  (
  `货物ID` int NOT NULL AUTO_INCREMENT,
  `路线ID` int NOT NULL,
  `货物名称` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `是否新品` tinyint(1) NULL DEFAULT 0,
  `货物种类` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `数量` decimal(18, 3) NULL DEFAULT 0.000,
  `单价` decimal(18, 4) NULL DEFAULT 0.0000,
  `币种` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'RMB',
  `重量(/kg)` decimal(18, 3) NULL DEFAULT 0.000 COMMENT '单个货物重量,单位:千克',
  `总重量(/kg)` decimal(18, 3) NULL DEFAULT 0.000 COMMENT '数量×单重,单位:千克',
  `总价` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`货物ID`) USING BTREE,
  INDEX `fk_goods_details_routes`(`路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_goods_details_routes` FOREIGN KEY (`路线ID`) REFERENCES `routes` (`路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for goods_total
-- ----------------------------
DROP TABLE IF EXISTS `goods_total`;
CREATE TABLE `goods_total`  (
  `整单货物ID` int NOT NULL AUTO_INCREMENT,
  `路线ID` int NOT NULL,
  `货物名称` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `实际重量(/kg)` decimal(18, 2) NULL DEFAULT 0.00 COMMENT '整单实际重量,单位:千克',
  `货值` decimal(18, 2) NULL DEFAULT 0.00,
  `总体积(/cbm)` decimal(18, 3) NULL DEFAULT 0.000 COMMENT '整单总体积,单位:立方米',
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`整单货物ID`) USING BTREE,
  INDEX `fk_goods_total_routes`(`路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_goods_total_routes` FOREIGN KEY (`路线ID`) REFERENCES `routes` (`路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 12 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for route_agents
-- ----------------------------
DROP TABLE IF EXISTS `route_agents`;
CREATE TABLE `route_agents`  (
  `代理路线ID` int NOT NULL AUTO_INCREMENT,
  `路线ID` int NOT NULL,
  `代理商` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `运输方式` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `贸易类型` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `代理备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `时效` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `时效备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `不含` varchar(511) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `是否赔付` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '0',
  `赔付内容` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`代理路线ID`) USING BTREE,
  INDEX `fk_route_agents_routes`(`路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_route_agents_routes` FOREIGN KEY (`路线ID`) REFERENCES `routes` (`路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for routes
-- ----------------------------
DROP TABLE IF EXISTS `routes`;
CREATE TABLE `routes`  (
  `路线ID` int NOT NULL AUTO_INCREMENT,
  `起始地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `途径地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `目的地` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `交易开始日期` date NULL DEFAULT NULL COMMENT '交易周期开始日期',
  `交易结束日期` date NULL DEFAULT NULL COMMENT '交易周期结束日期',
  `交易年份` year GENERATED ALWAYS AS (year(`交易开始日期`)) STORED COMMENT '虚拟列:交易年份' NULL,
  `交易月份` tinyint GENERATED ALWAYS AS (month(`交易开始日期`)) STORED COMMENT '虚拟列:交易月份' NULL,
  `实际重量(/kg)` decimal(18, 2) NULL DEFAULT 0.00 COMMENT '路线总实际重量,单位:千克',
  `计费重量(/kg)` decimal(18, 2) NULL DEFAULT NULL COMMENT '路线计费重量,单位:千克',
  `总体积(/cbm)` decimal(18, 3) NULL DEFAULT NULL COMMENT '路线总体积,单位:立方米',
  `货值` decimal(18, 2) NULL DEFAULT 0.00,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`路线ID`) USING BTREE,
  INDEX `idx_start_date`(`交易开始日期` ASC) USING BTREE COMMENT '交易开始日期索引',
  INDEX `idx_end_date`(`交易结束日期` ASC) USING BTREE COMMENT '交易结束日期索引',
  INDEX `idx_year_month`(`交易年份` ASC, `交易月份` ASC) USING BTREE COMMENT '年月查询优化索引',
  INDEX `idx_origin`(`起始地` ASC) USING BTREE COMMENT '起始地索引',
  INDEX `idx_destination`(`目的地` ASC) USING BTREE COMMENT '目的地索引'
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for summary
-- ----------------------------
DROP TABLE IF EXISTS `summary`;
CREATE TABLE `summary`  (
  `汇总ID` int NOT NULL AUTO_INCREMENT,
  `代理路线ID` int NOT NULL,
  `小计` decimal(18, 2) NULL DEFAULT 0.00,
  `税率` decimal(10, 4) NULL DEFAULT 0.0000,
  `税金` decimal(18, 2) NULL DEFAULT 0.00,
  `汇损率` decimal(10, 6) NULL DEFAULT 0.000000,
  `汇损` decimal(18, 2) NULL DEFAULT 0.00,
  `总计` decimal(18, 2) NULL DEFAULT 0.00,
  `备注` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `创建时间` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`汇总ID`) USING BTREE,
  UNIQUE INDEX `代理路线ID`(`代理路线ID` ASC) USING BTREE,
  CONSTRAINT `fk_summary_route_agents` FOREIGN KEY (`代理路线ID`) REFERENCES `route_agents` (`代理路线ID`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 58 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Procedure structure for recompute_route
-- ----------------------------
DROP PROCEDURE IF EXISTS `recompute_route`;
delimiter ;;
CREATE PROCEDURE `recompute_route`(IN p_route_id INT)
BEGIN
    DECLARE v_gd_weight DECIMAL(18,3) DEFAULT 0;
    DECLARE v_gt_weight DECIMAL(18,3) DEFAULT 0;
    DECLARE v_gd_value DECIMAL(18,2) DEFAULT 0;
    DECLARE v_gt_value DECIMAL(18,2) DEFAULT 0;
    DECLARE v_gt_volume DECIMAL(18,3) DEFAULT 0;
    DECLARE v_goods_names TEXT DEFAULT '';
    DECLARE v_actual_weight DECIMAL(18,2) DEFAULT 0;
    DECLARE v_billing_weight DECIMAL(18,2) DEFAULT NULL;

    -- ★ 从 goods_details 汇总
    SELECT IFNULL(SUM(`总重量(/kg)`),0), IFNULL(SUM(`总价`),0)
    INTO v_gd_weight, v_gd_value
    FROM goods_details
    WHERE `路线ID` = p_route_id;

    -- ★ 从 goods_total 汇总(包括体积)
    SELECT 
        IFNULL(SUM(`实际重量(/kg)`),0), 
        IFNULL(SUM(`货值`),0),
        IFNULL(SUM(`总体积(/cbm)`),0)
    INTO v_gt_weight, v_gt_value, v_gt_volume
    FROM goods_total
    WHERE `路线ID` = p_route_id;

    -- ★ v3.0: 汇总货物名称
    SELECT GROUP_CONCAT(DISTINCT `货物名称` SEPARATOR ', ')
    INTO v_goods_names
    FROM (
        SELECT `货物名称` FROM goods_details WHERE `路线ID` = p_route_id AND `货物名称` IS NOT NULL
        UNION
        SELECT `货物名称` FROM goods_total WHERE `路线ID` = p_route_id AND `货物名称` IS NOT NULL
    ) combined_goods;

    -- 计算实际重量
    SET v_actual_weight = v_gd_weight + v_gt_weight;
    
    -- ★ v3.0: 获取当前计费重量,如果为null则使用实际重量
    SELECT `计费重量(/kg)` INTO v_billing_weight
    FROM routes
    WHERE `路线ID` = p_route_id;
    
    IF v_billing_weight IS NULL THEN
        SET v_billing_weight = v_actual_weight;
    END IF;

    -- ★ v3.0: 更新 routes 表(包括货物名称、总体积和计费重量)
    UPDATE routes
    SET 
        `实际重量(/kg)` = v_actual_weight,
        `计费重量(/kg)` = v_billing_weight,
        `货值` = v_gd_value + v_gt_value,
        `总体积(/cbm)` = v_gt_volume,
        `货物名称` = v_goods_names
    WHERE `路线ID` = p_route_id;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for recompute_summary
-- ----------------------------
DROP PROCEDURE IF EXISTS `recompute_summary`;
delimiter ;;
CREATE PROCEDURE `recompute_summary`(IN p_agent_route_id INT)
BEGIN
    DECLARE v_route_id INT DEFAULT 0;
    DECLARE v_subtotal DECIMAL(18,2) DEFAULT 0;
    DECLARE v_tax_rate DECIMAL(10,4) DEFAULT 0;
    DECLARE v_tax DECIMAL(18,2) DEFAULT 0;
    DECLARE v_loss_rate DECIMAL(10,6) DEFAULT 0;
    DECLARE v_loss DECIMAL(18,2) DEFAULT 0;
    DECLARE v_total DECIMAL(18,2) DEFAULT 0;
    DECLARE v_route_value DECIMAL(18,2) DEFAULT 0;

    SELECT `路线ID` INTO v_route_id
    FROM route_agents
    WHERE `代理路线ID` = p_agent_route_id
    LIMIT 1;

    IF v_route_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '找不到对应的route_agents记录';
    END IF;

    SELECT IFNULL(`货值`,0) INTO v_route_value
    FROM routes
    WHERE `路线ID` = v_route_id
    LIMIT 1;

    SELECT 
        IFNULL(SUM(`人民币金额`),0)
    INTO v_subtotal
    FROM (
        SELECT `人民币金额` FROM fee_items WHERE `代理路线ID` = p_agent_route_id
        UNION ALL
        SELECT `人民币金额` FROM fee_total WHERE `代理路线ID` = p_agent_route_id
    ) combined_fees;

    SELECT 
        IFNULL(`税率`,0), 
        IFNULL(`汇损率`,0)
    INTO v_tax_rate, v_loss_rate
    FROM summary
    WHERE `代理路线ID` = p_agent_route_id
    LIMIT 1;

    SET v_tax = (v_subtotal + v_route_value) * (v_tax_rate / 100);
    SET v_loss = (v_subtotal + v_route_value) * (v_loss_rate / 100);
    SET v_total = v_subtotal + v_route_value + v_tax + v_loss;

    IF EXISTS(SELECT 1 FROM summary WHERE `代理路线ID` = p_agent_route_id) THEN
        UPDATE summary
        SET 
            `小计` = v_subtotal,
            `税金` = v_tax,
            `汇损` = v_loss,
            `总计` = v_total
        WHERE `代理路线ID` = p_agent_route_id;
    ELSE
        INSERT INTO summary(`代理路线ID`, `小计`, `税率`, `税金`, `汇损率`, `汇损`, `总计`)
        VALUES (p_agent_route_id, v_subtotal, v_tax_rate, v_tax, v_loss_rate, v_loss, v_total);
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for recompute_summary_for_route
-- ----------------------------
DROP PROCEDURE IF EXISTS `recompute_summary_for_route`;
delimiter ;;
CREATE PROCEDURE `recompute_summary_for_route`(IN p_route_id INT)
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE v_agent_route_id INT;
    DECLARE cur_agents CURSOR FOR 
        SELECT `代理路线ID` FROM route_agents WHERE `路线ID` = p_route_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur_agents;
    read_loop: LOOP
        FETCH cur_agents INTO v_agent_route_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        CALL recompute_summary(v_agent_route_id);
    END LOOP;
    CLOSE cur_agents;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_bi`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_bi` BEFORE INSERT ON `fee_items` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`原币金额` = IFNULL(NEW.`单价`,0) * IFNULL(NEW.`数量`,0);
    SET NEW.`人民币金额` = NEW.`原币金额` * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_ai`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_ai` AFTER INSERT ON `fee_items` FOR EACH ROW BEGIN
    CALL recompute_summary(NEW.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_bu`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_bu` BEFORE UPDATE ON `fee_items` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`原币金额` = IFNULL(NEW.`单价`,0) * IFNULL(NEW.`数量`,0);
    SET NEW.`人民币金额` = NEW.`原币金额` * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_au`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_au` AFTER UPDATE ON `fee_items` FOR EACH ROW BEGIN
    CALL recompute_summary(NEW.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_items_ad`;
delimiter ;;
CREATE TRIGGER `trg_fee_items_ad` AFTER DELETE ON `fee_items` FOR EACH ROW BEGIN
    CALL recompute_summary(OLD.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_bi`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_bi` BEFORE INSERT ON `fee_total` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`人民币金额` = IFNULL(NEW.`原币金额`,0) * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_ai`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_ai` AFTER INSERT ON `fee_total` FOR EACH ROW BEGIN
    CALL recompute_summary(NEW.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_bu`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_bu` BEFORE UPDATE ON `fee_total` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`人民币金额` = IFNULL(NEW.`原币金额`,0) * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_au`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_au` AFTER UPDATE ON `fee_total` FOR EACH ROW BEGIN
    CALL recompute_summary(NEW.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table fee_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_fee_total_ad`;
delimiter ;;
CREATE TRIGGER `trg_fee_total_ad` AFTER DELETE ON `fee_total` FOR EACH ROW BEGIN
    CALL recompute_summary(OLD.`代理路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_bi`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_bi` BEFORE INSERT ON `goods_details` FOR EACH ROW BEGIN
    DECLARE v_rate DECIMAL(18,8) DEFAULT 1;
    
    IF NEW.`币种` IS NULL OR NEW.`币种` = '' OR UPPER(NEW.`币种`) IN ('RMB','CNY') THEN
        SET v_rate = 1;
    ELSE
        SELECT IFNULL(`汇率`,1) INTO v_rate FROM forex_rate WHERE `币种` = NEW.`币种` LIMIT 1;
    END IF;

    SET NEW.`总重量(/kg)` = IFNULL(NEW.`数量`,0) * IFNULL(NEW.`重量(/kg)`,0);
    SET NEW.`总价` = IFNULL(NEW.`数量`,0) * IFNULL(NEW.`单价`,0) * v_rate;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_au`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_au` AFTER UPDATE ON `goods_details` FOR EACH ROW BEGIN
    CALL recompute_route(NEW.`路线ID`);
    CALL recompute_summary_for_route(NEW.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_details
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_details_ad`;
delimiter ;;
CREATE TRIGGER `trg_goods_details_ad` AFTER DELETE ON `goods_details` FOR EACH ROW BEGIN
    CALL recompute_route(OLD.`路线ID`);
    CALL recompute_summary_for_route(OLD.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_bi`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_bi` BEFORE INSERT ON `goods_total` FOR EACH ROW BEGIN
    IF NEW.`货值` IS NULL THEN
        SET NEW.`货值` = 0;
    END IF;
    IF NEW.`实际重量(/kg)` IS NULL THEN
        SET NEW.`实际重量(/kg)` = 0;
    END IF;
    IF NEW.`总体积(/cbm)` IS NULL THEN
        SET NEW.`总体积(/cbm)` = 0;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_ai`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_ai` AFTER INSERT ON `goods_total` FOR EACH ROW BEGIN
    CALL recompute_route(NEW.`路线ID`);
    CALL recompute_summary_for_route(NEW.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_bu`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_bu` BEFORE UPDATE ON `goods_total` FOR EACH ROW BEGIN
    IF NEW.`货值` IS NULL THEN
        SET NEW.`货值` = 0;
    END IF;
    IF NEW.`实际重量(/kg)` IS NULL THEN
        SET NEW.`实际重量(/kg)` = 0;
    END IF;
    IF NEW.`总体积(/cbm)` IS NULL THEN
        SET NEW.`总体积(/cbm)` = 0;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_au`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_au` AFTER UPDATE ON `goods_total` FOR EACH ROW BEGIN
    CALL recompute_route(NEW.`路线ID`);
    CALL recompute_summary_for_route(NEW.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table goods_total
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_goods_total_ad`;
delimiter ;;
CREATE TRIGGER `trg_goods_total_ad` AFTER DELETE ON `goods_total` FOR EACH ROW BEGIN
    CALL recompute_route(OLD.`路线ID`);
    CALL recompute_summary_for_route(OLD.`路线ID`);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table routes
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_routes_bi`;
delimiter ;;
CREATE TRIGGER `trg_routes_bi` BEFORE INSERT ON `routes` FOR EACH ROW BEGIN
    -- ★ v3.0: 如果计费重量为null,自动设置为实际重量
    IF NEW.`计费重量(/kg)` IS NULL AND NEW.`实际重量(/kg)` IS NOT NULL THEN
        SET NEW.`计费重量(/kg)` = NEW.`实际重量(/kg)`;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table routes
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_routes_bu`;
delimiter ;;
CREATE TRIGGER `trg_routes_bu` BEFORE UPDATE ON `routes` FOR EACH ROW BEGIN
    -- ★ v3.0: 如果计费重量被设置为null,自动使用实际重量
    IF NEW.`计费重量(/kg)` IS NULL AND NEW.`实际重量(/kg)` IS NOT NULL THEN
        SET NEW.`计费重量(/kg)` = NEW.`实际重量(/kg)`;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table routes
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_routes_au`;
delimiter ;;
CREATE TRIGGER `trg_routes_au` AFTER UPDATE ON `routes` FOR EACH ROW BEGIN
    -- 如果货值发生变化,则触发该路线下所有代理的 summary 重新计算
    IF NEW.`货值` <> OLD.`货值` THEN
        CALL recompute_summary_for_route(NEW.`路线ID`);
    END IF;
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
