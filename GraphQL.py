# encoding=utf8
# crawl missed issue comments in mongodb

import threading
import Queue

import yaml as yaml
import json
from utils import base
import requests
import Database
import logging
from requests.exceptions import ConnectionError, ReadTimeout

# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 10
base_path = ""
query = ""
start_time = ""
end_time = ""
url = "https://api.github.com/graphql"

# read all the tokens
f = open('github_tokens.txt', 'r')
github_tokens = f.read().strip().split("\n")

sleep_time_tokens = {} # record the sleep time of each token
sleep_gap_token = 1.8 # the sleep time of each token
for token in github_tokens:
    sleep_time_tokens.setdefault(token, -1)

# common crawl
def crawlCommon(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
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
        crawlCommonThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlCommonThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get()
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if base.judge_http_response(response) is False:
                        continue
                    response_json = response.json()
                    # 写入文件
                    filename = base_path + "/" + login + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    self.q.task_done()
                    break
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                except Exception as e:
                    logging.error(e)
                    return

# crawl github user data
def crawlUser(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
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
        print
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        crawlUserThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlUserThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get()
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if response.status_code != 200:
                        logging.error("response.status_code: " + str(response.status_code))
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        if response_json["errors"][0]["type"] == "NOT_FOUND":
                            Database.updateGithubSponsorshipsAsSponsor(login, str(base.flag1))
                            self.q.task_done()
                            break
                        continue
                    # 写入文件
                    filename = base_path + "/" + login + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    self.q.task_done()
                    break
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                except Exception as e:
                    logging.error(e)
                    return

# crawl github user data for sponsorships as maintainer
def crawlUserForSponsorshipsAsMaintainer(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
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
        print
        return

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        crawlUserForSponsorshipsAsMaintainerThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlUserForSponsorshipsAsMaintainerThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get()
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if response.status_code != 200:
                        logging.error("response.status_code: " + str(response.status_code))
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        if response_json["errors"][0]["type"] == "NOT_FOUND":
                            Database.updateGithubSponsorshipsAsMaintainer(login, str(base.flag1))
                            self.q.task_done()
                            break
                        continue
                    # 写入文件
                    filename = base_path + "/" + login + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    self.q.task_done()
                    break
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                except Exception as e:
                    logging.error(e)
                    return

# crawl sponsorships as maintainer
def crawlSponsorshipsAsMaintainer(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
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
        crawlSponsorshipsAsMaintainerThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlSponsorshipsAsMaintainerThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            after_cursor = ""
            count = 1
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login, after_cursor), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if base.judge_http_response(response) is False:
                        continue
                    response_json = response.json()
                    # 写入文件
                    filename = base_path + "/" + login + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.info("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["sponsorshipsAsMaintainer"]["pageInfo"]["hasNextPage"] is False:
                        break
                    after_cursor = response_json["data"]["user"]["sponsorshipsAsMaintainer"]["pageInfo"]["endCursor"]
                    count += 1
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                except Exception as e:
                    logging.error(e)
                    return
            self.q.task_done()

# crawl sponsorships as sponsor
def crawlSponsorshipsAsSponsor(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
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
        crawlSponsorshipsAsSponsorThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlSponsorshipsAsSponsorThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            after_cursor = ""
            count = 1
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login, after_cursor), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if base.judge_http_response(response) is False:
                        continue
                    response_json = response.json()
                    # 写入文件
                    filename = base_path + "/" + login + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["sponsorshipsAsSponsor"]["pageInfo"]["hasNextPage"] is False:
                        break
                    after_cursor = response_json["data"]["user"]["sponsorshipsAsSponsor"]["pageInfo"]["endCursor"]
                    count += 1
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                except Exception as e:
                    logging.error(e)
                    return
            self.q.task_done()

# crawl the recently all of commit contribution
def crawlUserCommits(p, q, sql, time1, time2):
    global base_path
    global query
    global start_time
    global end_time
    base_path = p
    query = q
    start_time = time1
    end_time = time2
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
        crawlUserCommitsThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlUserCommitsThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                # print github_token
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login, start_time, end_time), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if base.judge_http_response(response) is False:
                        continue
                    response_json = response.json()
                    # 写入文件
                    filename = base_path + "/" + login + "/" + start_time + "_" + end_time + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                    continue
                except Exception as e:
                    logging.error(e)
                    return
                self.q.task_done()
                break

# crawl the recently all of issue contribution
def crawlUserIssues(p, q, sql, time1, time2):
    global base_path
    global query
    global start_time
    global end_time
    base_path = p
    query = q
    start_time = time1
    end_time = time2
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
        crawlUserIssuesThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlUserIssuesThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            count = 1
            after_cursor = ""
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                # print github_token
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login, start_time, end_time, after_cursor), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if base.judge_http_response(response) is False:
                        continue
                    response_json = response.json()
                    # 写入文件
                    filename = base_path + "/" + login + "/" + start_time + "_" + end_time + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.info("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["contributionsCollection"]["issueContributions"]["pageInfo"]["hasNextPage"] is True:
                        after_cursor = response_json["data"]["user"]["contributionsCollection"]["issueContributions"]["pageInfo"]["endCursor"]
                        count += 1
                        continue
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                    continue
                except Exception as e:
                    logging.error(e)
                    return
                break
            self.q.task_done()

# crawl the recently all of pull request contribution
def crawlUserPullRequests(p, q, sql, time1, time2):
    global base_path
    global query
    global start_time
    global end_time
    base_path = p
    query = q
    start_time = time1
    end_time = time2
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
        crawlUserPullRequestsThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlUserPullRequestsThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            count = 1
            after_cursor = ""
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                # print github_token
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login, start_time, end_time, after_cursor), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if base.judge_http_response(response) is False:
                        continue
                    response_json = response.json()
                    # 写入文件
                    filename = base_path + "/" + login + "/" + start_time + "_" + end_time + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["contributionsCollection"]["pullRequestContributions"]["pageInfo"]["hasNextPage"] is True:
                        after_cursor = response_json["data"]["user"]["contributionsCollection"]["pullRequestContributions"]["pageInfo"]["endCursor"]
                        count += 1
                        continue
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                    continue
                except Exception as e:
                    logging.error(e)
                    return
                break
            self.q.task_done()

# crawl the recently all of pull request review contribution
def crawlUserPullRequestReview(p, q, sql, time1, time2):
    global base_path
    global query
    global start_time
    global end_time
    base_path = p
    query = q
    start_time = time1
    end_time = time2
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
        crawlUserPullRequestReviewThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlUserPullRequestReviewThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            count = 1
            after_cursor = ""
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                # print github_token
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                values = {"query": query % (login, start_time, end_time, after_cursor), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values)
                    if base.judge_http_response(response) is False:
                        continue
                    response_json = response.json()
                    # 写入文件
                    filename = base_path + "/" + login + "/" + start_time + "_" + end_time + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["contributionsCollection"]["pullRequestReviewContributions"]["pageInfo"]["hasNextPage"] is True:
                        after_cursor = response_json["data"]["user"]["contributionsCollection"]["pullRequestReviewContributions"]["pageInfo"]["endCursor"]
                        count += 1
                        continue
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                    continue
                except Exception as e:
                    logging.error(e)
                    return
                break
            self.q.task_done()

# crawl the recently all of repository contribution
def crawlUserRepository(p, q, sql, time1, time2):
    global base_path
    global query
    global start_time
    global end_time
    base_path = p
    query = q
    start_time = time1
    end_time = time2
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
        crawlUserRepositoryThread(workQueue).start()
    workQueue.join()

    print "finish"

class crawlUserRepositoryThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        count = 1
        after_cursor = ""
        while True:
            # get a suitable token and combine header
            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
            # print github_token
            headers = {
                'Authorization': 'Bearer ' + github_token,
                'Content-Type': 'application/json'
            }
            # print "headers is: " + str(headers)
            values = {"query": query % (login, start_time, end_time, after_cursor), "variables": {}}
            try:
                response = requests.post(url=url, headers=headers, json=values)
                if base.judge_http_response(response) is False:
                    continue
                response_json = response.json()
                # 写入文件
                filename = base_path + "/" + login + "/" + start_time + "_" + end_time + "/" + str(count) + ".json"
                flag = base.generate_file(filename, json.dumps(response_json))
                if flag is True:
                    print "create file successfully: " + filename
                elif flag is False:
                    print "file is already existed: " + filename
                else:
                    print "create file failed: " + flag + " filename: " + filename
                if response_json["data"]["user"]["contributionsCollection"]["repositoryContributions"]["pageInfo"]["hasNextPage"] is True:
                    after_cursor = response_json["data"]["user"]["contributionsCollection"]["repositoryContributions"]["pageInfo"]["endCursor"]
                    count += 1
                    continue
            except Exception as e:
                print(e)
                continue
            break
        self.q.task_done()

# crawl user commit comment
def crawlUserCommitComment(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
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
        crawlUserCommitCommentThread(workQueue).start()
    workQueue.join()

    print "finish"

class crawlUserCommitCommentThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        count = 1
        after_cursor = ""
        while True:
            # get a suitable token and combine header
            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
            # print github_token
            headers = {
                'Authorization': 'Bearer ' + github_token,
                'Content-Type': 'application/json'
            }
            # print "headers is: " + str(headers)
            values = {"query": query % (login, after_cursor), "variables": {}}
            try:
                response = requests.post(url=url, headers=headers, json=values)
                if base.judge_http_response(response) is False:
                    continue
                response_json = response.json()
                # 写入文件
                filename = base_path + "/" + login + "/" + str(count) + ".json"
                flag = base.generate_file(filename, json.dumps(response_json))
                if flag is True:
                    print "create file successfully: " + filename
                elif flag is False:
                    print "file is already existed: " + filename
                else:
                    print "create file failed: " + flag + " filename: " + filename
                if response_json["data"]["user"]["commitComments"]["pageInfo"]["hasNextPage"] is True:
                    after_cursor = ", after:" + "\"" + response_json["data"]["user"]["commitComments"]["pageInfo"]["endCursor"] + "\""
                    count += 1
                    continue
            except Exception as e:
                print(e)
                continue
            break
        self.q.task_done()

# crawl user issue comment
def crawlUserIssueComment(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
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
        crawlUserIssueCommentThread(workQueue).start()
    workQueue.join()

    print "finish"

class crawlUserIssueCommentThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        count = 1
        after_cursor = ""
        while True:
            # get a suitable token and combine header
            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
            # print github_token
            headers = {
                'Authorization': 'Bearer ' + github_token,
                'Content-Type': 'application/json'
            }
            # print "headers is: " + str(headers)
            values = {"query": query % (login, after_cursor), "variables": {}}
            try:
                response = requests.post(url=url, headers=headers, json=values)
                if base.judge_http_response(response) is False:
                    continue
                response_json = response.json()
                # 写入文件
                filename = base_path + "/" + login + "/" + str(count) + ".json"
                flag = base.generate_file(filename, json.dumps(response_json))
                if flag is True:
                    print "create file successfully: " + filename
                elif flag is False:
                    print "file is already existed: " + filename
                else:
                    print "create file failed: " + flag + " filename: " + filename
                if response_json["data"]["user"]["issueComments"]["pageInfo"]["hasNextPage"] is True:
                    after_cursor = ", after:" + "\"" + response_json["data"]["user"]["issueComments"]["pageInfo"]["endCursor"] + "\""
                    count += 1
                    continue
            except Exception as e:
                print(e)
                continue
            break
        self.q.task_done()