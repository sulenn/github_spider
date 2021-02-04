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
		`name` VARCHAR(100),
	    `email` VARCHAR(100),
		`spon_maintainer_count` INT,
		`spon_sponsor_count` INT,
	    `created_at` datetime,
	    `updated_at` datetime,
	    `flag` INT,              -- 0 is exist, 1 is not found or organization
	    `has_sponsors_listing TINYINT`    -- 1 has sponsors listing, 0 hasn't sponsors listing
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
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- create table: github_sponsorships_as_maintainer
CREATE TABLE
IF
	NOT EXISTS `github_sponsorships_as_maintainer` (
		`login` VARCHAR(100) NOT NULL,
		`sponsor_login` VARCHAR(100),
		`flag` INT,     -- 0 is user, 1 is organization, 2 is private
	    `created_at` datetime
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_sponsorships_as_sponsor
-- if login == sponsor_login, sponsor_login doesn't sponsor others
CREATE TABLE
IF
	NOT EXISTS `github_sponsorships_as_sponsor` (
	    `login` VARCHAR(100),
		`slug` VARCHAR(100),
		`sponsor_login` VARCHAR(100),
		`flag` INT,     -- 0 is user, 1 is organization, 2 is private, 3 is unknown, 4: sponsor_login didn't have sponsor others
	    `created_at` datetime,
	    PRIMARY KEY ( `login`,`sponsor_login` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_user_commits_per_day
CREATE TABLE
IF
	NOT EXISTS `github_user_commits_per_day` (
		`login` VARCHAR(100) NOT NULL,
		`date` VARCHAR(100) NOT NULL,
		`weekday` INT,
	    `contribution_count` INT,
		PRIMARY KEY ( `login`,`date` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_user_issue
CREATE TABLE
IF
	NOT EXISTS `github_user_issue` (
		`issue_database_id` INT,
		`login` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
		`title` TEXT,
		PRIMARY KEY ( `issue_database_id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- create table: github_user_pr
CREATE TABLE
IF
	NOT EXISTS `github_user_pr` (
		`pr_database_id` INT,
		`login` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
		`title` TEXT,
		PRIMARY KEY ( `pr_database_id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- create table: github_user_pr_review
CREATE TABLE
IF
	NOT EXISTS `github_user_pr_review` (
		`pr_database_id` INT,
		`login` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
		`title` TEXT,
		PRIMARY KEY ( `pr_database_id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- create table: github_repository
CREATE TABLE
IF
	NOT EXISTS `github_repository` (
		`repo_database_id` INT,
		`login` VARCHAR(100) NOT NULL,
		`name` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
		PRIMARY KEY ( `repo_database_id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_commit_comment
CREATE TABLE
IF
	NOT EXISTS `github_commit_comment` (
		`comm_database_id` INT,
		`login` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
		`updated_at` datetime,
		`body` TEXT,
		`commit_oid` VARCHAR(100),
		PRIMARY KEY ( `comm_database_id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- create table: github_issue_comment
CREATE TABLE
IF
	NOT EXISTS `github_issue_comment` (
		`comm_database_id` INT,
		`login` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
		`updated_at` datetime,
		`issue_login` VARCHAR(100),
		`issue_database_id` INT,
		PRIMARY KEY ( `comm_database_id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;