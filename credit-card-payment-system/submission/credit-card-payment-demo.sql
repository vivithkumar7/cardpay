-- MySQL schema-only export plus synthetic rows from the isolated showcase database.
-- No rows from the existing local MySQL database are included.
CREATE DATABASE IF NOT EXISTS `credit_card_submission_demo` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `credit_card_submission_demo`;
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_adminlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action` varchar(100) NOT NULL,
  `details` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `admin_user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `audit_adminlog_admin_user_id_af3726f2_fk_auth_user_id` (`admin_user_id`),
  CONSTRAINT `audit_adminlog_admin_user_id_af3726f2_fk_auth_user_id` FOREIGN KEY (`admin_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cards_card` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `card_type` varchar(10) NOT NULL,
  `masked_card_number` varchar(19) NOT NULL,
  `last4` varchar(4) NOT NULL,
  `card_holder_name` varchar(100) NOT NULL,
  `expiry_month` smallint unsigned NOT NULL,
  `expiry_year` smallint unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cards_card_user_id_9c174339_fk_auth_user_id` (`user_id`),
  CONSTRAINT `cards_card_user_id_9c174339_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `cards_card_chk_1` CHECK ((`expiry_month` >= 0)),
  CONSTRAINT `cards_card_chk_2` CHECK ((`expiry_year` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions_transaction` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(12,2) NOT NULL,
  `currency` varchar(3) NOT NULL,
  `status` varchar(10) NOT NULL,
  `reference` varchar(40) NOT NULL,
  `failure_reason` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `card_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reference` (`reference`),
  KEY `transactions_transaction_card_id_b6891695_fk_cards_card_id` (`card_id`),
  KEY `transactions_transaction_user_id_b9ecc248_fk_auth_user_id` (`user_id`),
  CONSTRAINT `transactions_transaction_card_id_b6891695_fk_cards_card_id` FOREIGN KEY (`card_id`) REFERENCES `cards_card` (`id`),
  CONSTRAINT `transactions_transaction_user_id_b9ecc248_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
SET FOREIGN_KEY_CHECKS=0;
START TRANSACTION;
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (1, 1, CONVERT(X'6164645f6c6f67656e747279' USING utf8mb4), CONVERT(X'43616e20616464206c6f6720656e747279' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (2, 1, CONVERT(X'6368616e67655f6c6f67656e747279' USING utf8mb4), CONVERT(X'43616e206368616e6765206c6f6720656e747279' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (3, 1, CONVERT(X'64656c6574655f6c6f67656e747279' USING utf8mb4), CONVERT(X'43616e2064656c657465206c6f6720656e747279' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (4, 1, CONVERT(X'766965775f6c6f67656e747279' USING utf8mb4), CONVERT(X'43616e2076696577206c6f6720656e747279' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (5, 2, CONVERT(X'6164645f7065726d697373696f6e' USING utf8mb4), CONVERT(X'43616e20616464207065726d697373696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (6, 2, CONVERT(X'6368616e67655f7065726d697373696f6e' USING utf8mb4), CONVERT(X'43616e206368616e6765207065726d697373696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (7, 2, CONVERT(X'64656c6574655f7065726d697373696f6e' USING utf8mb4), CONVERT(X'43616e2064656c657465207065726d697373696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (8, 2, CONVERT(X'766965775f7065726d697373696f6e' USING utf8mb4), CONVERT(X'43616e2076696577207065726d697373696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (9, 3, CONVERT(X'6164645f67726f7570' USING utf8mb4), CONVERT(X'43616e206164642067726f7570' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (10, 3, CONVERT(X'6368616e67655f67726f7570' USING utf8mb4), CONVERT(X'43616e206368616e67652067726f7570' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (11, 3, CONVERT(X'64656c6574655f67726f7570' USING utf8mb4), CONVERT(X'43616e2064656c6574652067726f7570' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (12, 3, CONVERT(X'766965775f67726f7570' USING utf8mb4), CONVERT(X'43616e20766965772067726f7570' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (13, 4, CONVERT(X'6164645f75736572' USING utf8mb4), CONVERT(X'43616e206164642075736572' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (14, 4, CONVERT(X'6368616e67655f75736572' USING utf8mb4), CONVERT(X'43616e206368616e67652075736572' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (15, 4, CONVERT(X'64656c6574655f75736572' USING utf8mb4), CONVERT(X'43616e2064656c6574652075736572' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (16, 4, CONVERT(X'766965775f75736572' USING utf8mb4), CONVERT(X'43616e20766965772075736572' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (17, 5, CONVERT(X'6164645f636f6e74656e7474797065' USING utf8mb4), CONVERT(X'43616e2061646420636f6e74656e742074797065' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (18, 5, CONVERT(X'6368616e67655f636f6e74656e7474797065' USING utf8mb4), CONVERT(X'43616e206368616e676520636f6e74656e742074797065' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (19, 5, CONVERT(X'64656c6574655f636f6e74656e7474797065' USING utf8mb4), CONVERT(X'43616e2064656c65746520636f6e74656e742074797065' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (20, 5, CONVERT(X'766965775f636f6e74656e7474797065' USING utf8mb4), CONVERT(X'43616e207669657720636f6e74656e742074797065' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (21, 6, CONVERT(X'6164645f73657373696f6e' USING utf8mb4), CONVERT(X'43616e206164642073657373696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (22, 6, CONVERT(X'6368616e67655f73657373696f6e' USING utf8mb4), CONVERT(X'43616e206368616e67652073657373696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (23, 6, CONVERT(X'64656c6574655f73657373696f6e' USING utf8mb4), CONVERT(X'43616e2064656c6574652073657373696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (24, 6, CONVERT(X'766965775f73657373696f6e' USING utf8mb4), CONVERT(X'43616e20766965772073657373696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (25, 7, CONVERT(X'6164645f626c61636b6c6973746564746f6b656e' USING utf8mb4), CONVERT(X'43616e2061646420426c61636b6c697374656420546f6b656e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (26, 7, CONVERT(X'6368616e67655f626c61636b6c6973746564746f6b656e' USING utf8mb4), CONVERT(X'43616e206368616e676520426c61636b6c697374656420546f6b656e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (27, 7, CONVERT(X'64656c6574655f626c61636b6c6973746564746f6b656e' USING utf8mb4), CONVERT(X'43616e2064656c65746520426c61636b6c697374656420546f6b656e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (28, 7, CONVERT(X'766965775f626c61636b6c6973746564746f6b656e' USING utf8mb4), CONVERT(X'43616e207669657720426c61636b6c697374656420546f6b656e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (29, 8, CONVERT(X'6164645f6f75747374616e64696e67746f6b656e' USING utf8mb4), CONVERT(X'43616e20616464204f75747374616e64696e6720546f6b656e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (30, 8, CONVERT(X'6368616e67655f6f75747374616e64696e67746f6b656e' USING utf8mb4), CONVERT(X'43616e206368616e6765204f75747374616e64696e6720546f6b656e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (31, 8, CONVERT(X'64656c6574655f6f75747374616e64696e67746f6b656e' USING utf8mb4), CONVERT(X'43616e2064656c657465204f75747374616e64696e6720546f6b656e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (32, 8, CONVERT(X'766965775f6f75747374616e64696e67746f6b656e' USING utf8mb4), CONVERT(X'43616e2076696577204f75747374616e64696e6720546f6b656e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (33, 9, CONVERT(X'6164645f63617264' USING utf8mb4), CONVERT(X'43616e206164642063617264' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (34, 9, CONVERT(X'6368616e67655f63617264' USING utf8mb4), CONVERT(X'43616e206368616e67652063617264' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (35, 9, CONVERT(X'64656c6574655f63617264' USING utf8mb4), CONVERT(X'43616e2064656c6574652063617264' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (36, 9, CONVERT(X'766965775f63617264' USING utf8mb4), CONVERT(X'43616e20766965772063617264' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (37, 10, CONVERT(X'6164645f7472616e73616374696f6e' USING utf8mb4), CONVERT(X'43616e20616464207472616e73616374696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (38, 10, CONVERT(X'6368616e67655f7472616e73616374696f6e' USING utf8mb4), CONVERT(X'43616e206368616e6765207472616e73616374696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (39, 10, CONVERT(X'64656c6574655f7472616e73616374696f6e' USING utf8mb4), CONVERT(X'43616e2064656c657465207472616e73616374696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (40, 10, CONVERT(X'766965775f7472616e73616374696f6e' USING utf8mb4), CONVERT(X'43616e2076696577207472616e73616374696f6e' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (41, 11, CONVERT(X'6164645f61646d696e6c6f67' USING utf8mb4), CONVERT(X'43616e206164642061646d696e206c6f67' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (42, 11, CONVERT(X'6368616e67655f61646d696e6c6f67' USING utf8mb4), CONVERT(X'43616e206368616e67652061646d696e206c6f67' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (43, 11, CONVERT(X'64656c6574655f61646d696e6c6f67' USING utf8mb4), CONVERT(X'43616e2064656c6574652061646d696e206c6f67' USING utf8mb4));
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES (44, 11, CONVERT(X'766965775f61646d696e6c6f67' USING utf8mb4), CONVERT(X'43616e20766965772061646d696e206c6f67' USING utf8mb4));
INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`, `first_name`) VALUES (1, CONVERT(X'70626b6466325f73686132353624313030303030302476426d416c626c686350676f3245647a4768534b354c24306b79584f724269487a476a4a4f6f526955755a524b7674304d5871494a353677345a76443267574675553d' USING utf8mb4), NULL, 0, CONVERT(X'64656d6f2d75736572' USING utf8mb4), CONVERT(X'' USING utf8mb4), CONVERT(X'64656d6f406578616d706c652e74657374' USING utf8mb4), 0, 1, CONVERT(X'323032362d31302d30352030343a33343a30302e373536313634' USING utf8mb4), CONVERT(X'' USING utf8mb4));
INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`, `first_name`) VALUES (2, CONVERT(X'70626b6466325f7368613235362431303030303030244d5876726256356545555154765476627279646c794d245553616f5848476f616c7736515632345579697156466b5966783233365953785a465164697952754244453d' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33373a34382e323331333339' USING utf8mb4), 1, CONVERT(X'64656d6f2d61646d696e' USING utf8mb4), CONVERT(X'' USING utf8mb4), CONVERT(X'61646d696e406578616d706c652e74657374' USING utf8mb4), 1, 1, CONVERT(X'323032362d31302d30352030343a33343a30322e363936383431' USING utf8mb4), CONVERT(X'' USING utf8mb4));
INSERT INTO `cards_card` (`id`, `card_type`, `masked_card_number`, `last4`, `card_holder_name`, `expiry_month`, `expiry_year`, `created_at`, `user_id`) VALUES (1, CONVERT(X'435245444954' USING utf8mb4), CONVERT(X'2a2a2a2a2a2a2a2a2a2a2a2a34323432' USING utf8mb4), CONVERT(X'34323432' USING utf8mb4), CONVERT(X'4176657279204d6f7267616e' USING utf8mb4), 12, 2030, CONVERT(X'323032362d31302d30352030343a33343a30342e363038393539' USING utf8mb4), 1);
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (1, CONVERT(X'61646d696e' USING utf8mb4), CONVERT(X'6c6f67656e747279' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (2, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'7065726d697373696f6e' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (3, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'67726f7570' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (4, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'75736572' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (5, CONVERT(X'636f6e74656e747479706573' USING utf8mb4), CONVERT(X'636f6e74656e7474797065' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (6, CONVERT(X'73657373696f6e73' USING utf8mb4), CONVERT(X'73657373696f6e' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (7, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'626c61636b6c6973746564746f6b656e' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (8, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'6f75747374616e64696e67746f6b656e' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (9, CONVERT(X'6361726473' USING utf8mb4), CONVERT(X'63617264' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (10, CONVERT(X'7472616e73616374696f6e73' USING utf8mb4), CONVERT(X'7472616e73616374696f6e' USING utf8mb4));
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (11, CONVERT(X'6175646974' USING utf8mb4), CONVERT(X'61646d696e6c6f67' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (1, CONVERT(X'636f6e74656e747479706573' USING utf8mb4), CONVERT(X'303030315f696e697469616c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e353535393933' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (2, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030315f696e697469616c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e353934393339' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (3, CONVERT(X'61646d696e' USING utf8mb4), CONVERT(X'303030315f696e697469616c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e363230333335' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (4, CONVERT(X'61646d696e' USING utf8mb4), CONVERT(X'303030325f6c6f67656e7472795f72656d6f76655f6175746f5f616464' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e363437393631' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (5, CONVERT(X'61646d696e' USING utf8mb4), CONVERT(X'303030335f6c6f67656e7472795f6164645f616374696f6e5f666c61675f63686f69636573' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e363733373037' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (6, CONVERT(X'6175646974' USING utf8mb4), CONVERT(X'303030315f696e697469616c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e373034303932' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (7, CONVERT(X'636f6e74656e747479706573' USING utf8mb4), CONVERT(X'303030325f72656d6f76655f636f6e74656e745f747970655f6e616d65' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e373631333032' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (8, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030325f616c7465725f7065726d697373696f6e5f6e616d655f6d61785f6c656e677468' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e373937383733' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (9, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030335f616c7465725f757365725f656d61696c5f6d61785f6c656e677468' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e383234333532' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (10, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030345f616c7465725f757365725f757365726e616d655f6f707473' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e383530373636' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (11, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030355f616c7465725f757365725f6c6173745f6c6f67696e5f6e756c6c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e383832363833' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (12, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030365f726571756972655f636f6e74656e7474797065735f30303032' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e383838333636' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (13, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030375f616c7465725f76616c696461746f72735f6164645f6572726f725f6d65737361676573' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e393131313933' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (14, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030385f616c7465725f757365725f757365726e616d655f6d61785f6c656e677468' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e393432383733' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (15, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303030395f616c7465725f757365725f6c6173745f6e616d655f6d61785f6c656e677468' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35362e393732323637' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (16, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303031305f616c7465725f67726f75705f6e616d655f6d61785f6c656e677468' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e303033303733' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (17, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303031315f7570646174655f70726f78795f7065726d697373696f6e73' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e303234363337' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (18, CONVERT(X'61757468' USING utf8mb4), CONVERT(X'303031325f616c7465725f757365725f66697273745f6e616d655f6d61785f6c656e677468' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e303539303833' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (19, CONVERT(X'6361726473' USING utf8mb4), CONVERT(X'303030315f696e697469616c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e303939303535' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (20, CONVERT(X'73657373696f6e73' USING utf8mb4), CONVERT(X'303030315f696e697469616c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e313136303139' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (21, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303030315f696e697469616c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e313933363037' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (22, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303030325f6f75747374616e64696e67746f6b656e5f6a74695f686578' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e323234303633' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (23, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303030335f6175746f5f32303137313031375f32303037' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e323634363238' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (24, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303030345f6175746f5f32303137313031375f32303133' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e333033323038' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (25, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303030355f72656d6f76655f6f75747374616e64696e67746f6b656e5f6a7469' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e333532353738' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (26, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303030365f6175746f5f32303137313031375f32313133' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e333739383830' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (27, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303030375f6175746f5f32303137313031375f32323134' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e343438353535' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (28, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303030385f6d6967726174655f746f5f6269676175746f6669656c64' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e353136303630' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (29, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303031305f6669785f6d6967726174655f746f5f6269676175746f6669656c64' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e353733393234' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (30, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303031315f6c696e656172697a65735f686973746f7279' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e353738373733' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (31, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303031325f616c7465725f6f75747374616e64696e67746f6b656e5f75736572' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e363035383933' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (32, CONVERT(X'746f6b656e5f626c61636b6c697374' USING utf8mb4), CONVERT(X'303031335f616c7465725f626c61636b6c6973746564746f6b656e5f6f7074696f6e735f616e645f6d6f7265' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e363434343236' USING utf8mb4));
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (33, CONVERT(X'7472616e73616374696f6e73' USING utf8mb4), CONVERT(X'303030315f696e697469616c' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33333a35372e363835303639' USING utf8mb4));
INSERT INTO `transactions_transaction` (`id`, `amount`, `currency`, `status`, `reference`, `failure_reason`, `created_at`, `updated_at`, `card_id`, `user_id`) VALUES (1, 1250, CONVERT(X'494e52' USING utf8mb4), CONVERT(X'53554343455353' USING utf8mb4), CONVERT(X'44454d4f2d534554544c45442d303031' USING utf8mb4), CONVERT(X'' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33343a30342e363139393636' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33343a30342e363230303339' USING utf8mb4), 1, 1);
INSERT INTO `transactions_transaction` (`id`, `amount`, `currency`, `status`, `reference`, `failure_reason`, `created_at`, `updated_at`, `card_id`, `user_id`) VALUES (2, 340.13, CONVERT(X'494e52' USING utf8mb4), CONVERT(X'4641494c4544' USING utf8mb4), CONVERT(X'44454d4f2d4641494c45442d303032' USING utf8mb4), CONVERT(X'53696d756c61746564207061796d656e74206661696c7572652e' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33343a30342e363236343334' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33343a30342e363236343639' USING utf8mb4), 1, 1);
INSERT INTO `transactions_transaction` (`id`, `amount`, `currency`, `status`, `reference`, `failure_reason`, `created_at`, `updated_at`, `card_id`, `user_id`) VALUES (3, 780, CONVERT(X'494e52' USING utf8mb4), CONVERT(X'50454e44494e47' USING utf8mb4), CONVERT(X'44454d4f2d50454e44494e472d303033' USING utf8mb4), CONVERT(X'' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33343a30342e363335303035' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33343a30342e363335303635' USING utf8mb4), 1, 1);
INSERT INTO `transactions_transaction` (`id`, `amount`, `currency`, `status`, `reference`, `failure_reason`, `created_at`, `updated_at`, `card_id`, `user_id`) VALUES (4, 825, CONVERT(X'494e52' USING utf8mb4), CONVERT(X'53554343455353' USING utf8mb4), CONVERT(X'5041592d32303236313030353034333634332d3430373746443145' USING utf8mb4), CONVERT(X'' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33363a34352e303038323239' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33363a34362e313031353835' USING utf8mb4), 1, 1);
INSERT INTO `transactions_transaction` (`id`, `amount`, `currency`, `status`, `reference`, `failure_reason`, `created_at`, `updated_at`, `card_id`, `user_id`) VALUES (5, 100.13, CONVERT(X'494e52' USING utf8mb4), CONVERT(X'4641494c4544' USING utf8mb4), CONVERT(X'5041592d32303236313030353034333730322d4232453539313734' USING utf8mb4), CONVERT(X'53696d756c61746564207061796d656e74206661696c7572652e' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33373a30332e353134373532' USING utf8mb4), CONVERT(X'323032362d31302d30352030343a33373a30342e363231383135' USING utf8mb4), 1, 1);
COMMIT;
SET FOREIGN_KEY_CHECKS=1;
