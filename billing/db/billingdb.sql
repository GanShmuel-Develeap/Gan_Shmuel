--
-- Database: `billdb`
--

CREATE DATABASE IF NOT EXISTS `billdb`;
USE `billdb`;

-- --------------------------------------------------------

--
-- Table structure
--

CREATE TABLE IF NOT EXISTS `Provider` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  AUTO_INCREMENT=10001 ;

CREATE TABLE IF NOT EXISTS `Rates` (
  `product_name` varchar(50) NOT NULL,
  `rate` int(11) DEFAULT 0,
  `scope` int(11) DEFAULT NULL, /*changed here*/
  FOREIGN KEY (scope) REFERENCES `Provider`(`id`)
) ENGINE=InnoDB ;

CREATE TABLE IF NOT EXISTS `Trucks` (
  `id` varchar(10) NOT NULL,
  `provider_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`provider_id`) REFERENCES `Provider`(`id`)
) ENGINE=InnoDB ;
/*
INSERT INTO Provider (`name`) VALUES ('pro1'), ('pro2');

INSERT INTO Rates (`product_name`, `rate`, `scope`) VALUES ('apple', 2, NULL), ('orange', 3, NULL), ('orange', 5, 10001);

INSERT INTO Trucks (`id`, `provider_id`) VALUES ('134-33-443', 10002);
*/