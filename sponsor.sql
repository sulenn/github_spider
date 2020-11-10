-- create table: init_user
CREATE TABLE
IF
	NOT EXISTS `init_user` (
	    `login` VARCHAR(100) NOT NULL,
	    PRIMARY KEY ( `login` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_user
CREATE TABLE
IF
	NOT EXISTS `github_user` (
		`database_id` INT,
		`login` VARCHAR(100) NOT NULL,
		`name` VARCHAR(100) NOT NULL,
	    `email` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
	    `updated_at` datetime,
	    PRIMARY KEY ( `database_id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;