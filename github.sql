-- create database
CREATE DATABASE GITHUB;

-- create table: github_repo
CREATE TABLE
IF
	NOT EXISTS `github_repo` (
		`id` INT,
		`owner` VARCHAR(100) NOT NULL,
	    `name` VARCHAR(100) NOT NULL,
	    `issues` INT,
	    `pull_requests` INT,
	    `created_at` datetime,
	    `updated_at` datetime,
	    PRIMARY KEY ( `id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_repo_test
-- CREATE TABLE
-- IF
-- 	NOT EXISTS `github_repo_test` (
--         `id` INT,
-- 		`owner` VARCHAR(100) NOT NULL,
-- 	    `name` VARCHAR(100) NOT NULL,
-- 	    `issues` INT,
-- 	    `pull_requests` INT,
-- 	    `created_at` datetime,
-- 	    `updated_at` datetime,
-- 	    PRIMARY KEY ( `id` )
-- 	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_issue
-- 0 represent issue and 1 pull request in flag
CREATE TABLE
IF
	NOT EXISTS `github_issue` (
		`id` INT,
		`number` INT,
		`user_login` VARCHAR(100) NOT NULL,
		`owner_login` VARCHAR(100) NOT NULL,
	    `repo` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
	    `updated_at` datetime,
	    `flag` INT,
	    `comments` INT,
	    `total_count` INT,
	    `up` INT,
	    `down` INT,
	    `laugh` INT,
	    `confused` INT,
	    `heart` INT,
	    `hooray` INT,
	    `rocket` INT,
	    `eyes` INT,
	    PRIMARY KEY ( `id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_issue_test
-- CREATE TABLE
-- IF
-- 	NOT EXISTS `github_issue_test` (
-- 		`id` INT,
-- 		`number` INT,
-- 		`user_login` VARCHAR(100) NOT NULL,
-- 		`owner_login` VARCHAR(100) NOT NULL,
-- 	    `repo` VARCHAR(100) NOT NULL,
-- 	    `created_at` datetime,
-- 	    `updated_at` datetime,
-- 	    `flag` INT,
-- 	    `comments` INT,
-- 	    `total_count` INT,
-- 	    `up` INT,
-- 	    `down` INT,
-- 	    `laugh` INT,
-- 	    `confused` INT,
-- 	    `heart` INT,
-- 	    `hooray` INT,
-- 	    `rocket` INT,
-- 	    `eyes` INT,
-- 	    PRIMARY KEY ( `id` )
-- 	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_comment
CREATE TABLE
IF
	NOT EXISTS `github_comment` (
		`id` INT,
		`issue_number` INT,
		`user_login` VARCHAR(100) NOT NULL,
		`owner_login` VARCHAR(100) NOT NULL,
	    `repo` VARCHAR(100) NOT NULL,
	    `created_at` datetime,
	    `updated_at` datetime,
	    `total_count` INT,
	    `up` INT,
	    `down` INT,
	    `laugh` INT,
	    `confused` INT,
	    `heart` INT,
	    `hooray` INT,
	    `rocket` INT,
	    `eyes` INT,
	    PRIMARY KEY ( `id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_comment_test
-- CREATE TABLE
-- IF
-- 	NOT EXISTS `github_comment_test` (
-- 		`id` INT,
-- 		`issue_number` INT,
-- 		`user_login` VARCHAR(100) NOT NULL,
-- 		`owner_login` VARCHAR(100) NOT NULL,
-- 	    `repo` VARCHAR(100) NOT NULL,
-- 	    `created_at` datetime,
-- 	    `updated_at` datetime,
-- 	    `total_count` INT,
-- 	    `up` INT,
-- 	    `down` INT,
-- 	    `laugh` INT,
-- 	    `confused` INT,
-- 	    `heart` INT,
-- 	    `hooray` INT,
-- 	    `rocket` INT,
-- 	    `eyes` INT,
-- 	    PRIMARY KEY ( `id` )
-- 	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_contributor
CREATE TABLE
IF
	NOT EXISTS `github_contributor` (
		`id` INT,
		`login` VARCHAR(100) NOT NULL,
		`owner_login` VARCHAR(100) NOT NULL,
		`repo_id` INT NOT NULL,
	    `repo` VARCHAR(100) NOT NULL,
	    `type` VARCHAR(50) NOT NULL,
	    `contributions` INT,
	    PRIMARY KEY ( `id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- select the sum of github_issue and github_pull_request
select issue.num as issue_num, pull_request.num as pull_request_num
from (select count(*) as num from github_issue) as issue, (select count(*) as num from github_pull_request) as pull_request;
