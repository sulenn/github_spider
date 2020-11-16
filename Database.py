# encoding=utf8
# crawl missed issue comments in mongodb

import threading
import Queue

import yaml as yaml
import json
from utils import base
import os
import logging

# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 10
base_path = ""

# read all the tokens
f = open('github_tokens.txt', 'r')
github_tokens = f.read().strip().split("\n")

sleep_time_tokens = {} # record the sleep time of each token
sleep_gap_token = 1.8 # the sleep time of each token
for token in github_tokens:
    sleep_time_tokens.setdefault(token, -1)

# write github user info
def writeGithubUser(path, sql):
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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubUserThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeGithubUserThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get()
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            # get db connection
            db = base.connectMysqlDB(config, autocommit=False)
            cur = db.cursor()

            # read data from file
            file = base_path + "/" + login + ".json"
            text = base.get_info_from_file(file)
            if text is False:
                logging.warn("file not existed: " + file)
            else:
                obj = json.loads(text)
                logging.info("writing login data: " + login)
                cur.execute("insert into github_user "
                            "(database_id, login, name, email,spon_maintainer_count, spon_sponsor_count, created_at, updated_at) "
                            "values (%s, %s, %s, %s, %s, %s, %s, %s)",
                            (obj["data"]["user"]["databaseId"], obj["data"]["user"]["login"], obj["data"]["user"]["name"], obj["data"]["user"]["email"],
                             obj["data"]["user"]["sponsorshipsAsMaintainer"]["totalCount"], obj["data"]["user"]["sponsorshipsAsSponsor"]["totalCount"],
                             base.time_handler(obj["data"]["user"]["createdAt"]), base.time_handler(obj["data"]["user"]["updatedAt"])))
                db.commit()
                logging.info(login + " ~~~~~~~~~ data commit into dababase success!!")
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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubSponsorListingThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeGithubSponsorListingThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            # get db connection
            db = base.connectMysqlDB(config, autocommit=False)
            cur = db.cursor()

            # read data from file
            try:
                file = base_path + "/" + login + ".json"
                text = base.get_info_from_file(file)
                if text is False:
                    logging.warn("file not existed: " + file)
                else:
                    obj = json.loads(text)
                    cur.execute("insert into github_sponsor_listing "
                                "(login, slug, name, tiers_total_count, created_at, short_description) "
                                "values (%s, %s, %s, %s, %s, %s)",
                                (obj["data"]["user"]["login"], obj["data"]["user"]["sponsorsListing"]["slug"], obj["data"]["user"]["sponsorsListing"]["name"],
                                 obj["data"]["user"]["sponsorsListing"]["tiers"]["totalCount"], base.time_handler(obj["data"]["user"]["sponsorsListing"]["createdAt"]),
                                 obj["data"]["user"]["sponsorsListing"]["shortDescription"]))
                    db.commit()
                    logging.info(login + " ~~~~~~~~~ data commit into dababase success!!")
                self.q.task_done()
                cur.close()
                db.close()
            except Exception as e:
                logging.error(e)
                return

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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubSponsorListingTiersThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeGithubSponsorListingTiersThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            # get db connection
            db = base.connectMysqlDB(config, autocommit=False)
            cur = db.cursor()

            # read data from file
            try:
                file = base_path + "/" + login + ".json"
                text = base.get_info_from_file(file)
                if text is False:
                    logging.warn("file not existed: " + file)
                else:
                    obj = json.loads(text)
                    logging.info(login + " ~~~~~~~~~ has " + str(obj["data"]["user"]["sponsorsListing"]["tiers"]["totalCount"]) + " tiers")
                    count = 1
                    for edge in obj["data"]["user"]["sponsorsListing"]["tiers"]["edges"]:
                        cur.execute("insert into github_sponsor_listing_tiers "
                                    "(login, slug, monthly_price_in_cents, monthly_price_in_dollars, name, created_at, updated_at, description) "
                                    "values (%s, %s, %s, %s, %s, %s, %s, %s)",
                                    (obj["data"]["user"]["login"], obj["data"]["user"]["sponsorsListing"]["slug"], edge["node"]["monthlyPriceInCents"],
                                     edge["node"]["monthlyPriceInDollars"], edge["node"]["name"], base.time_handler(edge["node"]["createdAt"]),
                                     base.time_handler(edge["node"]["updatedAt"]), edge["node"]["description"]))
                        db.commit()
                        logging.info("the " + str(count) + "th tier data commit into dababase success!!")
                        count += 1
                self.q.task_done()
                cur.close()
                db.close()
            except Exception as e:
                logging.error(e)
                return

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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubSponsorshipsAsMaintainerThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeGithubSponsorshipsAsMaintainerThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

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
                        logging.warn("file not existed: " + file_path)
                    else:
                        obj = json.loads(text)
                        logging.info("read file: " + file_path)
                        count = 1
                        for edge in obj["data"]["user"]["sponsorshipsAsMaintainer"]["edges"]:
                            if edge["node"]["privacyLevel"] == "PRIVATE":
                                cur.execute("insert into github_sponsorships_as_maintainer "
                                            "(login, flag, created_at) "
                                            "values (%s, %s, %s)",
                                            (obj["data"]["user"]["login"], base.flag2, base.time_handler(edge["node"]["createdAt"])))
                            else:
                                if "company" in edge["node"]["sponsorEntity"]:
                                    flag = base.flag0
                                else:
                                    flag = base.flag1
                                cur.execute("insert into github_sponsorships_as_maintainer "
                                            "(login, sponsor_login, flag, created_at) "
                                            "values (%s, %s, %s, %s)",
                                            (obj["data"]["user"]["login"], edge["node"]["sponsorEntity"]["login"], flag,
                                             base.time_handler(edge["node"]["createdAt"])))
                            db.commit()
                            logging.info("the " + str(count) + "th record in file: " + file_path)
                            count += 1
                self.q.task_done()
                cur.close()
                db.close()
            except Exception as e:
                logging.error(e)

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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeGithubSponsorshipsAsSponsorThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeGithubSponsorshipsAsSponsorThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

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
                        logging.warn("file not existed: " + file_path)
                        continue
                    obj = json.loads(text)
                    print "read file: " + file_path
                    count = 1
                    # github user 接受了打赏，但是没有打赏过别人。
                    # 之所以将这部分数据写入 github_sponsorships_as_sponsor 表中，是为了做筛选
                    if len(obj["data"]["user"]["sponsorshipsAsSponsor"]["edges"]) == 0:
                        logging.warn("the user " + login + " doesn't sponsor others")
                        cur.execute("insert into github_sponsorships_as_sponsor "
                                    "(login, sponsor_login, flag) "
                                    "values (%s, %s, %s)",
                                    (login, login, str(base.flag4)))
                        db.commit()
                        continue
                    for edge in obj["data"]["user"]["sponsorshipsAsSponsor"]["edges"]:
                        if edge["node"]["privacyLevel"] == "PRIVATE":
                            logging.info("the " + str(count) + "th record is private in file: " + file_path)
                            count += 1
                            continue
                        else:
                            slug = edge["node"]["sponsorable"]["sponsorsListing"]["slug"].split("-")[1]
                            cur.execute("insert into github_sponsorships_as_sponsor "
                                        "(login, slug, sponsor_login, flag, created_at) "
                                        "values (%s, %s, %s, %s, %s)",
                                        (slug, edge["node"]["sponsorable"]["sponsorsListing"]["slug"], obj["data"]["user"]["login"], str(3),
                                         base.time_handler(edge["node"]["createdAt"])))
                        db.commit()
                        logging.info("the " + str(count) + "th record in file: " + file_path)
                        count += 1
                self.q.task_done()
                cur.close()
                db.close()
            except Exception as e:
                logging.error(e)

def updateGithubSponsorshipsAsSponsor(login, flag):
    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    cur.execute("update github_sponsorships_as_sponsor "
                "set flag= " + flag + " "
                "where login='" + login + "'")
    items = cur.fetchall()
    logging.info("finish reading database")

    # close this database connection
    cur.close()
    db.close()

def updateGithubSponsorshipsAsMaintainer(login, flag):
    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    cur.execute("update github_sponsorships_as_maintainer "
                "set flag= " + flag + " "
                "where sponsor_login='" + login + "'")
    items = cur.fetchall()
    logging.info("finish reading database")

    # close this database connection
    cur.close()
    db.close()

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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeUserCommitsThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeUserCommitsThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

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
                        logging.warn("file not existed: " + file_path)
                    else:
                        obj = json.loads(text)
                        logging.info("read file: " + file_path)
                        count = 1
                        for week in obj["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
                            for day in week["contributionDays"]:
                                cur.execute("insert into github_user_commits_per_day "
                                            "(login, date, weekday, contribution_count) "
                                            "values (%s, %s, %s, %s)",
                                            (obj["data"]["user"]["login"], day["date"], day["weekday"], day["contributionCount"]))
                                db.commit()
                                logging.info("the " + str(count) + "th record in file: " + file_path)
                                count += 1
                self.q.task_done()
                cur.close()
                db.close()
            except Exception as e:
                logging.error(e)
                return

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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeUserIssuesThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeUserIssuesThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

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
                        logging.warn("file not existed: " + file)
                    else:
                        obj = json.loads(text)
                        logging.info("read file: " + file)
                        count = 1
                        for node in obj["data"]["user"]["contributionsCollection"]["issueContributions"]["edges"]:
                            cur.execute("insert into github_user_issue "
                                        "(issue_database_id, login, created_at, title) "
                                        "values (%s, %s, %s, %s)",
                                        (node["node"]["issue"]["databaseId"], obj["data"]["user"]["login"], base.time_handler(node["node"]["issue"]["createdAt"]),
                                         node["node"]["issue"]["title"]))
                            db.commit()
                            logging.info("the " + str(count) + "th record in file: " + file)
                            count += 1
                self.q.task_done()
                cur.close()
                db.close()
            except Exception as e:
                logging.error(e)
                return

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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeUserPullRequestThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeUserPullRequestThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

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
                        logging.warn("file not existed: " + file)
                    else:
                        obj = json.loads(text)
                        logging.info("read file: " + file)
                        count = 1
                        for node in obj["data"]["user"]["contributionsCollection"]["pullRequestContributions"]["edges"]:
                            cur.execute("insert into github_user_pr "
                                        "(pr_database_id, login, created_at, title) "
                                        "values (%s, %s, %s, %s)",
                                        (node["node"]["pullRequest"]["databaseId"], obj["data"]["user"]["login"], base.time_handler(node["node"]["pullRequest"]["createdAt"]),
                                         node["node"]["pullRequest"]["title"]))
                            db.commit()
                            logging.info("the " + str(count) + "th record in file: " + file)
                            count += 1
                self.q.task_done()
                cur.close()
                db.close()
            except Exception as e:
                logging.error(e)
                return

# write the recently all of pull request review contribution
def writeUserPullRequestReview(path, sql):
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
    logging.info("finish reading database")
    logging.info("%d tasks left for handling" % (len(unhandled_tasks)))

    # close this database connection
    cur.close()
    db.close()

    if len(unhandled_tasks) == 0:
        logging.warn("finish")
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        writeUserPullRequestReviewThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class writeUserPullRequestReviewThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

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
                        logging.warn("file not existed: " + file)
                    else:
                        obj = json.loads(text)
                        logging.info("read file: " + file)
                        count = 1
                        for node in obj["data"]["user"]["contributionsCollection"]["pullRequestReviewContributions"]["edges"]:
                            cur.execute("insert into github_user_pr_review "
                                        "(pr_database_id, login, created_at, title) "
                                        "values (%s, %s, %s, %s)",
                                        (node["node"]["pullRequest"]["databaseId"], obj["data"]["user"]["login"], base.time_handler(node["node"]["pullRequest"]["createdAt"]),
                                         node["node"]["pullRequest"]["title"]))
                            db.commit()
                            logging.info("the " + str(count) + "th record in file: " + file)
                            count += 1
                self.q.task_done()
                cur.close()
                db.close()
            except Exception as e:
                logging.error(e)
                return

# write the recently all of repository contribution
def writeUserRepository(path, sql):
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
        writeUserRepositoryThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeUserRepositoryThread(threading.Thread):
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
                    for node in obj["data"]["user"]["contributionsCollection"]["repositoryContributions"]["edges"]:
                        cur.execute("insert into github_repository "
                                    "(repo_database_id, login, name, created_at) "
                                    "values (%s, %s, %s, %s)",
                                    (node["node"]["repository"]["databaseId"], obj["data"]["user"]["login"], node["node"]["repository"]["name"],
                                     base.time_handler(node["node"]["repository"]["createdAt"])))
                        db.commit()
                        print "the " + str(count) + "th record in file: " + file
                        count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)

# write user commit comment
def writeUserCommitComment(path, sql):
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
        writeUserCommitCommentThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeUserCommitCommentThread(threading.Thread):
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
                    for node in obj["data"]["user"]["commitComments"]["edges"]:
                        cur.execute("insert into github_commit_comment "
                                    "(comm_database_id, login, created_at, updated_at, body, commit_oid) "
                                    "values (%s, %s, %s, %s, %s, %s)",
                                    (node["node"]["databaseId"], obj["data"]["user"]["login"], base.time_handler(node["node"]["createdAt"]),
                                     base.time_handler(node["node"]["updatedAt"]), node["node"]["body"], node["node"]["commit"]["oid"]))
                        db.commit()
                        print "the " + str(count) + "th record in file: " + file
                        count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)

# write user issue comment
def writeUserIssueComment(path, sql):
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
        writeUserIssueCommentThread(workQueue).start()
    workQueue.join()

    print "finish"

class writeUserIssueCommentThread(threading.Thread):
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
                    for node in obj["data"]["user"]["issueComments"]["edges"]:
                        try:
                            cur.execute("insert into github_issue_comment "
                                        "(comm_database_id, login, created_at, updated_at, issue_login, issue_database_id) "
                                        "values (%s, %s, %s, %s, %s, %s)",
                                        (node["node"]["databaseId"], obj["data"]["user"]["login"], base.time_handler(node["node"]["createdAt"]),
                                         base.time_handler(node["node"]["updatedAt"]), node["node"]["issue"]["author"]["login"],
                                         node["node"]["issue"]["databaseId"]))
                            db.commit()
                        except Exception as e:
                            print e
                            print "\n\ninsert failed!! the " + str(count) + "th record in file: " + file + "\n\n"
                            cur.execute("insert into github_issue_comment "
                                        "(comm_database_id, login, created_at, updated_at, issue_database_id) "
                                        "values (%s, %s, %s, %s, %s)",
                                        (node["node"]["databaseId"], obj["data"]["user"]["login"],
                                         base.time_handler(node["node"]["createdAt"]),
                                         base.time_handler(node["node"]["updatedAt"]),
                                         node["node"]["issue"]["databaseId"]))
                            db.commit()
                        print "the " + str(count) + "th record in file: " + file
                        count += 1
            self.q.task_done()
            cur.close()
            db.close()
        except Exception as e:
            print(e)