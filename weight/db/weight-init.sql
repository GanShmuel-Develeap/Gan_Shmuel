CREATE TABLE IF NOT EXISTS `containers_registered` (
  `container_id` varchar(15) NOT NULL,
  `weight` int(12) DEFAULT NULL,
  `unit` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`container_id`)
) ENGINE=MyISAM AUTO_INCREMENT=10001 ;

CREATE TABLE IF NOT EXISTS `transactions` (
  `id` int(12) NOT NULL AUTO_INCREMENT,
  `datetime` datetime DEFAULT NULL,
  `direction` varchar(10) DEFAULT NULL,
  `truck` varchar(50) DEFAULT NULL,
  `containers` varchar(10000) DEFAULT NULL,
  `bruto` int(12) DEFAULT NULL,
  `unit` varchar(10) DEFAULT NULL,
  `truckTara` int(12) DEFAULT NULL,
  `neto` int(12) DEFAULT NULL,
  `produce` varchar(50) DEFAULT NULL,
  `session_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=10001 ;