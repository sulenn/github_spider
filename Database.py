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