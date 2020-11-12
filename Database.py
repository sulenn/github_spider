# encoding=utf8
# crawl missed issue comments in mongodb

import time
import threading
import Queue
import urllib

import MySQLdb
import yaml as yaml
import urllib2
import json
import datetime
from utils import base
from datetime import datetime, timedelta
import requests
import os


# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 1
base_path = ""

# read all the tokens
f = open('github_tokens.txt', 'r')
github_tokens = f.read().strip().split("\n")

sleep_time_tokens = {} # record the sleep time of each token
sleep_gap_token = 1.8 # the sleep time of each token
for token in github_tokens:
    sleep_time_tokens.setdefault(token, -1)

# write github user info
def writeGithubUser(path):
    global base_path
    base_path = path
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute("select login "
                "from init_user "
                "WHERE login NOT IN (SELECT login from github_user)")
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        print "finish"
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubUserThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeGithubUserThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get db connection
        db = base.connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        # read data from file
        file = base_path + "/" + login + ".json"
        text = base.get_info_from_file(file)
        if text is False:
            print "file not existed: " + file
        else:
            obj = json.loads(text)
            cur.execute("insert into github_user "
                        "(database_id, login, name, email,spon_maintainer_count, spon_sponsor_count, created_at, updated_at) "
                        "values (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (obj["data"]["user"]["databaseId"], obj["data"]["user"]["login"], obj["data"]["user"]["name"], obj["data"]["user"]["email"],
                         obj["data"]["user"]["sponsorshipsAsMaintainer"]["totalCount"], obj["data"]["user"]["sponsorshipsAsSponsor"]["totalCount"],
                         base.time_handler(obj["data"]["user"]["createdAt"]), base.time_handler(obj["data"]["user"]["createdAt"])))
            db.commit()
            print login + " ~~~~~~~~~ data commit into dababase success!!"
        self.q.task_done()
        cur.close()
        db.close()

# write github user sponsor listing info
def writeGithubSponsorListing(path, sql):
    global base_path
    base_path = path
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        print "finish"
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubSponsorListingThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeGithubSponsorListingThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get db connection
        db = base.connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        # read data from file
        try:
            file = base_path + "/" + login + ".json"
            text = base.get_info_from_file(file)
            if text is False:
                print "file not existed: " + file
            else:
                obj = json.loads(text)
                cur.execute("insert into github_sponsor_listing "
                            "(login, slug, name, tiers_total_count, created_at, short_description) "
                            "values (%s, %s, %s, %s, %s, %s)",
                            (obj["data"]["user"]["login"], obj["data"]["user"]["sponsorsListing"]["slug"], obj["data"]["user"]["sponsorsListing"]["name"],
                             obj["data"]["user"]["sponsorsListing"]["tiers"]["totalCount"], base.time_handler(obj["data"]["user"]["sponsorsListing"]["createdAt"]),
                             obj["data"]["user"]["sponsorsListing"]["shortDescription"]))
                db.commit()
                print login + " ~~~~~~~~~ data commit into dababase success!!"
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)

# write github user sponsor listing tiers info
def writeGithubSponsorListingTiers(path, sql):
    global base_path
    base_path = path
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        print "finish"
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubSponsorListingTiersThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeGithubSponsorListingTiersThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get db connection
        db = base.connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        # read data from file
        try:
            file = base_path + "/" + login + ".json"
            text = base.get_info_from_file(file)
            if text is False:
                print "file not existed: " + file
            else:
                obj = json.loads(text)
                print login + " ~~~~~~~~~ has " + str(obj["data"]["user"]["sponsorsListing"]["tiers"]["totalCount"]) + " tiers"
                count = 1
                for edge in obj["data"]["user"]["sponsorsListing"]["tiers"]["edges"]:
                    cur.execute("insert into github_sponsor_listing_tiers "
                                "(login, slug, monthly_price_in_cents, monthly_price_in_dollars, name, created_at, updated_at, description) "
                                "values (%s, %s, %s, %s, %s, %s, %s, %s)",
                                (obj["data"]["user"]["login"], obj["data"]["user"]["sponsorsListing"]["slug"], edge["node"]["monthlyPriceInCents"],
                                 edge["node"]["monthlyPriceInDollars"], edge["node"]["name"], base.time_handler(edge["node"]["createdAt"]),
                                 base.time_handler(edge["node"]["updatedAt"]), edge["node"]["description"]))
                    db.commit()
                    print "the " + str(count) + "th tier data commit into dababase success!!"
                    count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)

# write github user sponsorships as maintainer
def writeGithubSponsorshipsAsMaintainer(path, sql):
    global base_path
    base_path = path
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        print "finish"
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubSponsorshipsAsMaintainerThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeGithubSponsorshipsAsMaintainerThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get db connection
        db = base.connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        # read data from file
        try:
            directory = base_path + "/" + login
            files = os.listdir(directory)
            for file in files:
                file_path = directory + "/" + file
                text = base.get_info_from_file(file_path)
                if text is False:
                    print "file not existed: " + file_path
                else:
                    obj = json.loads(text)
                    print "read file: " + file_path
                    count = 1
                    for edge in obj["data"]["user"]["sponsorshipsAsMaintainer"]["edges"]:
                        if edge["node"]["privacyLevel"] == "PRIVATE":
                            cur.execute("insert into github_sponsorships_as_maintainer "
                                        "(login, flag, created_at) "
                                        "values (%s, %s, %s)",
                                        (obj["data"]["user"]["login"], str(2), base.time_handler(edge["node"]["createdAt"])))
                        else:
                            if "company" in edge["node"]["sponsorEntity"]:
                                flag = 0
                            else:
                                flag = 1
                            cur.execute("insert into github_sponsorships_as_maintainer "
                                        "(login, sponsor_login, flag, created_at) "
                                        "values (%s, %s, %s, %s)",
                                        (obj["data"]["user"]["login"], edge["node"]["sponsorEntity"]["login"], flag,
                                         base.time_handler(edge["node"]["createdAt"])))
                        db.commit()
                        print "the " + str(count) + "th record in file: " + file_path
                        count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)

# write github user sponsorships as sponsor
def writeGithubSponsorshipsAsSponsor(path, sql):
    global base_path
    base_path = path
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        print "finish"
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubSponsorshipsAsSponsorThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeGithubSponsorshipsAsSponsorThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get db connection
        db = base.connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        # read data from file
        try:
            directory = base_path + "/" + login
            files = os.listdir(directory)
            for file in files:
                file_path = directory + "/" + file
                text = base.get_info_from_file(file_path)
                if text is False:
                    print "file not existed: " + file_path
                else:
                    obj = json.loads(text)
                    print "read file: " + file_path
                    count = 1
                    for edge in obj["data"]["user"]["sponsorshipsAsSponsor"]["edges"]:
                        if edge["node"]["privacyLevel"] == "PRIVATE":
                            cur.execute("insert into github_sponsorships_as_sponsor "
                                        "(sponsor_login, flag, created_at) "
                                        "values (%s, %s, %s)",
                                        (obj["data"]["user"]["login"], str(2), base.time_handler(edge["node"]["createdAt"])))
                        else:
                            cur.execute("insert into github_sponsorships_as_sponsor "
                                        "(slug, sponsor_login, flag, created_at) "
                                        "values (%s, %s, %s, %s)",
                                        (edge["node"]["sponsorable"]["sponsorsListing"]["slug"], obj["data"]["user"]["login"], str(3),
                                         base.time_handler(edge["node"]["createdAt"])))
                        db.commit()
                        print "the " + str(count) + "th record in file: " + file_path
                        count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)

# write the recently all of commit contribution
def writeUserCommits(path, sql):
    global base_path
    base_path = path
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        print "finish"
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeUserCommitsThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeUserCommitsThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get db connection
        db = base.connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        # read data from file
        try:
            directory = base_path + "/" + login
            files = os.listdir(directory)
            for file in files:
                file_path = directory + "/" + file
                text = base.get_info_from_file(file_path)
                if text is False:
                    print "file not existed: " + file_path
                else:
                    obj = json.loads(text)
                    print "read file: " + file_path + "\n\n"
                    count = 1
                    for week in obj["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
                        for day in week["contributionDays"]:
                            cur.execute("insert into github_user_commits_per_day "
                                        "(login, date, weekday, contribution_count) "
                                        "values (%s, %s, %s, %s)",
                                        (obj["data"]["user"]["login"], day["date"], day["weekday"], day["contributionCount"]))
                            db.commit()
                            print "the " + str(count) + "th record in file: " + file_path
                            count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)

# write the recently all of issue contribution
def writeUserIssues(path, sql):
    global base_path
    base_path = path
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        print "finish"
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeUserIssuesThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeUserIssuesThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get db connection
        db = base.connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        # read data from file
        try:
            directory = base_path + "/" + login
            files = base.read_all_filename_in_directory(directory)
            for file in files:
                text = base.get_info_from_file(file)
                if text is False:
                    print "file not existed: " + file
                else:
                    obj = json.loads(text)
                    print "\n\nread file: " + file
                    count = 1
                    for node in obj["data"]["user"]["contributionsCollection"]["issueContributions"]["edges"]:
                        cur.execute("insert into github_user_issue "
                                    "(issue_database_id, login, created_at, title) "
                                    "values (%s, %s, %s, %s)",
                                    (node["node"]["issue"]["databaseId"], obj["data"]["user"]["login"], base.time_handler(node["node"]["issue"]["createdAt"]),
                                     node["node"]["issue"]["title"]))
                        db.commit()
                        print "the " + str(count) + "th record in file: " + file
                        count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)

# write the recently all of pull request contribution
def writeUserPullRequests(path, sql):
    global base_path
    base_path = path
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        print "finish"
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeUserPullRequestThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeUserPullRequestThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get db connection
        db = base.connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        # read data from file
        try:
            directory = base_path + "/" + login
            files = base.read_all_filename_in_directory(directory)
            for file in files:
                text = base.get_info_from_file(file)
                if text is False:
                    print "file not existed: " + file
                else:
                    obj = json.loads(text)
                    print "\n\nread file: " + file
                    count = 1
                    for node in obj["data"]["user"]["contributionsCollection"]["pullRequestContributions"]["edges"]:
                        cur.execute("insert into github_user_pr "
                                    "(pr_database_id, login, created_at, title) "
                                    "values (%s, %s, %s, %s)",
                                    (node["node"]["pullRequest"]["databaseId"], obj["data"]["user"]["login"], base.time_handler(node["node"]["pullRequest"]["createdAt"]),
                                     node["node"]["pullRequest"]["title"]))
                        db.commit()
                        print "the " + str(count) + "th record in file: " + file
                        count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)