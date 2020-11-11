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
		`login` VARCHAR(100) NOT NULL,
		`database_id` INT,
		`name` VARCHAR(100) NOT NULL,
	    `email` VARCHAR(100) NOT NULL,
		`spon_maintainer_count` INT,
		`spon_sponsor_count` INT,
	    `created_at` datetime,
	    `updated_at` datetime,
	    PRIMARY KEY ( `login` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_sponsor_listing
CREATE TABLE
IF
	NOT EXISTS `github_sponsor_listing` (
		`login` VARCHAR(100) NOT NULL,
		`slug` VARCHAR(100) NOT NULL,
		`name` VARCHAR(100) NOT NULL,
		`tiers_total_count` INT,
	    `created_at` datetime,
		`short_description` TEXT,
	    PRIMARY KEY ( `login` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_sponsor_listing_tiers
CREATE TABLE
IF
	NOT EXISTS `github_sponsor_listing_tiers` (
		`login` VARCHAR(100) NOT NULL,
		`slug` VARCHAR(100) NOT NULL,
		`monthly_price_in_cents` INT,
		`monthly_price_in_dollars` INT,
		`name` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
		`updated_at` datetime,
		`description` TEXT,
		PRIMARY KEY ( `login`,`name` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_sponsorships_as_maintainer
CREATE TABLE
IF
	NOT EXISTS `github_sponsorships_as_maintainer` (
		`login` VARCHAR(100) NOT NULL,
		`sponsor_login` VARCHAR(100) NOT NULL,
		`flag` INT,     -- 0 is user, 1 is organization
	    `created_at` datetime,
		PRIMARY KEY ( `login`,`sponsor_login` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_sponsorships_as_sponsor
CREATE TABLE
IF
	NOT EXISTS `github_sponsorships_as_sponsor` (
		`login` VARCHAR(100) NOT NULL,
		`sponsor_login` VARCHAR(100) NOT NULL,
		`flag` INT,     -- 0 is user, 1 is organization
	    `created_at` datetime,
		PRIMARY KEY ( `login`,`sponsor_login` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;