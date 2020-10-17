-- create database
CREATE DATABASE GITHUB;

-- create table: github_repo
CREATE TABLE
IF
	NOT EXISTS `github_repo` (
		`id` INT,
		`owner` VARCHAR(100) NOT NULL,
	    `reponame` VARCHAR(100) NOT NULL,
	    `issues` INT,
	    `pull_requests` INT,
	    PRIMARY KEY ( `id` )
	)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- create table: github_issue
CREATE TABLE
IF
	NOT EXISTS `github_issue` (
		`id` INT,
		`number` INT,
		`user_login` VARCHAR(100) NOT NULL,
		`owner_login` VARCHAR(100) NOT NULL,
	    `repo` VARCHAR(100) NOT NULL,
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

-- create table: github_pull_request
CREATE TABLE
IF
	NOT EXISTS `github_pull_request` (
		`id` INT,
		`number` INT,
		`user_login` VARCHAR(100) NOT NULL,
		`owner_login` VARCHAR(100) NOT NULL,
	    `repo` VARCHAR(100) NOT NULL,
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

-- create table: github_comment
CREATE TABLE
IF
	NOT EXISTS `github_comment` (
		`id` INT,
		`issue_number` INT,
		`user_login` VARCHAR(100) NOT NULL,
		`owner_login` VARCHAR(100) NOT NULL,
	    `repo` VARCHAR(100) NOT NULL,
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

-- select the sum of github_issue and github_pull_request
select issue.num as issue_num, pull_request.num as pull_request_num
from (select count(*) as num from github_issue) as issue, (select count(*) as num from github_pull_request) as pull_request;
