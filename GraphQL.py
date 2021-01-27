# encoding=utf8
# crawl missed issue comments in mongodb

import threading
import Queue
import yaml as yaml
import json
from utils import base
import requests
import Database
import time
from utils import queries
import logging
from requests.exceptions import ConnectionError, ReadTimeout

# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 20
base_path = ""
query = ""
start_time = ""
end_time = ""
url = "https://api.github.com/graphql"

# read all the tokens
f = open('github_tokens.txt', 'r')
github_tokens = f.read().strip().split("\n")

sleep_time_tokens = {} # record the sleep time of each token
sleep_gap_token = 60 # the sleep time of each token
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
        login = item[0]
        # judge the file is existed
        filename = base_path + "/" + login + ".json"
        if base.judge_file_exist(filename):
            continue
        # unhandled tasks
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
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if base.judge_http_response(response) is False:
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
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
                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                    logging.error(e)
                except Exception as e:
                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                    logging.fatal(e)
                    continue

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
        login = item[0]
        # judge the file is existed
        filename = base_path + "/" + login + ".json"
        if base.judge_file_exist(filename):
            continue
        # unhandled tasks
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
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if response.status_code != 200:
                        logging.error("response.status_code: " + str(response.status_code))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
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
                    logging.fatal(e)
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
        login = item[0]
        # judge the file is existed
        filename = base_path + "/" + login + ".json"
        if base.judge_file_exist(filename):
            continue
        # unhandled tasks
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
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if response.status_code != 200:
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        logging.error("response.status_code: " + str(response.status_code))
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
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
                    logging.fatal(e)
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
    unhandled_logins = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_logins.append(item[0])
    logging.info("finish reading database")

    # read handled task from directory
    handled_logins = base.read_all_filename_none_path(base_path)

    # judge handled logins is whether was handled, if true, handle unhandled task
    for login in handled_logins:
        workQueue.put_nowait({"login": login})
    for _ in range(THREAD_NUM):
        judgeSponsorshipsAsMaintainerThread(workQueue).start()
    workQueue.join()

    # unhandled logins
    unhandled_logins = list(set(unhandled_logins) - set(handled_logins))

    # unhandled tasks
    unhandled_tasks = []
    for login in unhandled_logins:
        unhandled_tasks.append({"login": login})
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

class judgeSponsorshipsAsMaintainerThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]

            # get the max index in handled login directory
            directory_path = base_path + "/" + login
            filenames = base.read_all_filename_none_path(directory_path)
            indexes = []
            for filename in filenames:
                indexes.append(int(filename[:len(filename) - 5]))
            count = int(max(indexes))
            num_per_query = 100

            # judge task is whether was handled
            file_path = directory_path + "/" + str(count) + ".json"
            text = base.get_info_from_file(file_path)
            if text is False:
                logging.fatal("file not existed: " + file_path)
            else:
                obj = json.loads(text)
                logging.info("read file: " + file_path)
                if "hasNextPage" in obj["data"]["user"]["sponsorshipsAsMaintainer"]["pageInfo"]:
                    hasNextPage = obj["data"]["user"]["sponsorshipsAsMaintainer"]["pageInfo"]["hasNextPage"]
                    if hasNextPage is True:
                        cursor = obj["data"]["user"]["sponsorshipsAsMaintainer"]["pageInfo"]["endCursor"]
                        count += 1
                        while True:
                            # get a suitable token and combine header
                            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                            # print github_token
                            headers = {
                                'Authorization': 'Bearer ' + github_token,
                                'Content-Type': 'application/json'
                            }
                            # print "headers is: " + str(headers)
                            condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                        + cursor + "\""
                            values = {"query": query % (login, condition), "variables": {}}
                            try:
                                response = requests.post(url=url, headers=headers, json=values, timeout=40)
                                if response.status_code == 403:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    continue
                                if response.status_code != 200:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    continue
                                response_json = response.json()
                                if "errors" in response_json:
                                    logging.error(json.dumps(response_json))
                                    if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                                        logging.info("login: " + login + ", count: " + str(count))
                                        if num_per_query > 1:
                                            num_per_query /= 2
                                            logging.warn(
                                                "num of per query minus half, after minus half, num_per_query: " + str(
                                                    num_per_query))
                                        else:    # when data doesn't existed, replace query sentence
                                            global query
                                            query = queries.query_github_user_commit_comments_empty
                                            logging.warn("replace query sentence to handle losed data")
                                        continue
                                    if "type" not in response_json["errors"][0]:
                                        logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                        logging.info("login: " + login + ", count: " + str(count))
                                        continue
                                    if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                    continue
                                # handle the situation, when data doesn't existed, recover num_per_query and query
                                if "edges" not in response_json["data"]["user"]["sponsorshipsAsMaintainer"]:
                                    num_per_query = 100
                                    global query
                                    query = queries.query_github_user_commit_comments
                                    logging.warn("losed data is successful handled!!!!")
                                # 写入文件
                                filename = base_path + "/" + login + "/" + str(count) + ".json"
                                flag = base.generate_file(filename, json.dumps(response_json))
                                if flag is True:
                                    logging.info("create file successfully: " + filename)
                                elif flag is False:
                                    logging.warn("file is already existed: " + filename)
                                else:
                                    logging.warn("create file failed: " + flag + " filename: " + filename)
                                if response_json["data"]["user"]["sponsorshipsAsMaintainer"]["pageInfo"]["hasNextPage"] is True:
                                    cursor = response_json["data"]["user"]["sponsorshipsAsMaintainer"]["pageInfo"]["endCursor"]
                                    count += 1
                                    continue
                            except (ConnectionError, ReadTimeout) as e:
                                logging.error(e)
                                continue
                            except Exception as e:
                                logging.fatal(e)
                                continue
                                # return
                            break
                    else:
                        logging.info("data of user: " + login + " was handled!")
            self.q.task_done()

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
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if base.judge_http_response(response) is False:
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
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
                    logging.fatal(e)
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
    unhandled_logins = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_logins.append(item[0])
    logging.info("finish reading database")

    # read handled task from directory
    handled_logins = base.read_all_filename_none_path(base_path)

    # judge handled logins is whether was handled, if true, handle unhandled task
    for login in handled_logins:
        workQueue.put_nowait({"login": login})
    for _ in range(THREAD_NUM):
        judgeSponsorshipsAsSponsorThread(workQueue).start()
    workQueue.join()

    # unhandled logins
    unhandled_logins = list(set(unhandled_logins) - set(handled_logins))

    # unhandled tasks
    unhandled_tasks = []
    for login in unhandled_logins:
        unhandled_tasks.append({"login": login})
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

class judgeSponsorshipsAsSponsorThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]

            # get the max index in handled login directory
            directory_path = base_path + "/" + login
            filenames = base.read_all_filename_none_path(directory_path)
            indexes = []
            for filename in filenames:
                indexes.append(int(filename[:len(filename) - 5]))
            count = int(max(indexes))
            num_per_query = 100

            # judge task is whether was handled
            file_path = directory_path + "/" + str(count) + ".json"
            text = base.get_info_from_file(file_path)
            if text is False:
                logging.fatal("file not existed: " + file_path)
            else:
                obj = json.loads(text)
                logging.info("read file: " + file_path)
                if "hasNextPage" in obj["data"]["user"]["sponsorshipsAsSponsor"]["pageInfo"]:
                    hasNextPage = obj["data"]["user"]["sponsorshipsAsSponsor"]["pageInfo"]["hasNextPage"]
                    if hasNextPage is True:
                        cursor = obj["data"]["user"]["sponsorshipsAsSponsor"]["pageInfo"]["endCursor"]
                        count += 1
                        while True:
                            # get a suitable token and combine header
                            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                            # print github_token
                            headers = {
                                'Authorization': 'Bearer ' + github_token,
                                'Content-Type': 'application/json'
                            }
                            # print "headers is: " + str(headers)
                            condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                        + cursor + "\""
                            values = {"query": query % (login, condition), "variables": {}}
                            try:
                                response = requests.post(url=url, headers=headers, json=values, timeout=40)
                                if response.status_code == 403:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    continue
                                if response.status_code != 200:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    continue
                                response_json = response.json()
                                if "errors" in response_json:
                                    logging.error(json.dumps(response_json))
                                    if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                                        logging.info("login: " + login + ", count: " + str(count))
                                        if num_per_query > 1:
                                            num_per_query /= 2
                                            logging.warn(
                                                "num of per query minus half, after minus half, num_per_query: " + str(
                                                    num_per_query))
                                        else:    # when data doesn't existed, replace query sentence
                                            global query
                                            query = queries.query_github_user_commit_comments_empty
                                            logging.warn("replace query sentence to handle losed data")
                                        continue
                                    if "type" not in response_json["errors"][0]:
                                        logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                        logging.info("login: " + login + ", count: " + str(count))
                                        continue
                                    if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                    continue
                                # handle the situation, when data doesn't existed, recover num_per_query and query
                                if "edges" not in response_json["data"]["user"]["sponsorshipsAsSponsor"]:
                                    num_per_query = 100
                                    global query
                                    query = queries.query_github_user_commit_comments
                                    logging.warn("losed data is successful handled!!!!")
                                # 写入文件
                                filename = base_path + "/" + login + "/" + str(count) + ".json"
                                flag = base.generate_file(filename, json.dumps(response_json))
                                if flag is True:
                                    logging.info("create file successfully: " + filename)
                                elif flag is False:
                                    logging.warn("file is already existed: " + filename)
                                else:
                                    logging.warn("create file failed: " + flag + " filename: " + filename)
                                if response_json["data"]["user"]["sponsorshipsAsSponsor"]["pageInfo"]["hasNextPage"] is True:
                                    cursor = response_json["data"]["user"]["sponsorshipsAsSponsor"]["pageInfo"]["endCursor"]
                                    count += 1
                                    continue
                            except (ConnectionError, ReadTimeout) as e:
                                logging.error(e)
                                continue
                            except Exception as e:
                                logging.fatal(e)
                                continue
                                # return
                            break
                    else:
                        logging.info("data of user: " + login + " was handled!")
            self.q.task_done()

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
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if base.judge_http_response(response) is False:
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
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
                    logging.fatal(e)
                    return
            self.q.task_done()

# crawl the recently all of commit contribution
def crawlUserCommits(p, q, sql):
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
        login = item[0]
        # judge the file is existed
        filename = base_path + "/" + login + "/"
        if base.judge_file_exist(filename):
            continue
        # unhandled tasks
        unhandled_tasks.append({"login": item[0], "created_at": item[1]})
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
            start_time = work["created_at"]
            final_time = "2020-12-12 00:00:00"
            while base.datetime_to_timestamp(start_time) < base.time_string_to_timestamp(final_time):
                end_time = base.add_one_year(start_time)
                while True:
                    # get a suitable token and combine header
                    github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                    # print github_token
                    headers = {
                        'Authorization': 'Bearer ' + github_token,
                        'Content-Type': 'application/json'
                    }
                    # print "headers is: " + str(headers)
                    values = {"query": query % (login, base.datetime_to_github_time(start_time),
                                                base.datetime_to_github_time(end_time)), "variables": {}}
                    try:
                        response = requests.post(url=url, headers=headers, json=values, timeout=40)
                        if response.status_code == 403:
                            logging.error("response.status_code: " + str(response.status_code))
                            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                            continue
                        if response.status_code != 200:
                            logging.error("response.status_code: " + str(response.status_code))
                            continue
                        response_json = response.json()
                        if "errors" in response_json:
                            logging.error(json.dumps(response_json))
                            if "type" not in response_json["errors"][0]:
                                logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                logging.info("login: " + login)
                                continue
                            if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                logging.info("RATE_LIMITED!!!!!!!!!!!!!!!!!!!!!")
                            logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            continue
                        # 写入文件
                        filename = base_path + "/" + login + "/" + base.datetime_to_github_time(start_time) + "_" \
                                   + base.datetime_to_github_time(end_time) + ".json"
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
                        logging.fatal(e)
                        continue
                    break
                start_time = base.add_one_day(end_time)
            self.q.task_done()

# crawl the recently all of issue contribution
def crawlUserIssues(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_logins = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_logins.append(item[0])
    logging.info("finish reading database")

    # read handled task from directory
    handled_logins = base.read_all_filename_none_path(base_path)

    # judge handled logins is whether was handled, if true, handle unhandled task
    for login in handled_logins:
        workQueue.put_nowait({"login": login})
    for _ in range(THREAD_NUM):
        judgeUserIssueThread(workQueue).start()
    workQueue.join()

    # unhandled logins
    unhandled_logins = list(set(unhandled_logins) - set(handled_logins))

    # unhandled tasks
    unhandled_tasks = []
    for login in unhandled_logins:
        unhandled_tasks.append({"login": login})
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

class judgeUserIssueThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]

            # get the max index in handled login directory
            directory_path = base_path + "/" + login
            filenames = base.read_all_filename_none_path(directory_path)
            indexes = []
            for filename in filenames:
                indexes.append(int(filename[:len(filename) - 5]))
            count = int(max(indexes))
            num_per_query = 100

            # judge task is whether was handled
            file_path = directory_path + "/" + str(count) + ".json"
            text = base.get_info_from_file(file_path)
            if text is False:
                logging.fatal("file not existed: " + file_path)
            else:
                obj = json.loads(text)
                logging.info("read file: " + file_path)
                if "hasNextPage" in obj["data"]["user"]["issues"]["pageInfo"]:
                    hasNextPage = obj["data"]["user"]["issues"]["pageInfo"]["hasNextPage"]
                    if hasNextPage is True:
                        cursor = obj["data"]["user"]["issues"]["pageInfo"]["endCursor"]
                        count += 1
                        while True:
                            # get a suitable token and combine header
                            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                            # print github_token
                            headers = {
                                'Authorization': 'Bearer ' + github_token,
                                'Content-Type': 'application/json'
                            }
                            # print "headers is: " + str(headers)
                            condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                        + cursor + "\""
                            values = {"query": query % (login, condition), "variables": {}}
                            try:
                                response = requests.post(url=url, headers=headers, json=values, timeout=40)
                                if response.status_code == 403:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    continue
                                if response.status_code != 200:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    continue
                                response_json = response.json()
                                if "errors" in response_json:
                                    logging.error(json.dumps(response_json))
                                    if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                                        logging.info("login: " + login + ", count: " + str(count))
                                        if num_per_query > 1:
                                            num_per_query /= 2
                                            logging.warn(
                                                "num of per query minus half, after minus half, num_per_query: " + str(
                                                    num_per_query))
                                        else:    # when data doesn't existed, replace query sentence
                                            global query
                                            query = queries.query_github_user_issues_empty
                                            logging.warn("replace query sentence to handle losed data")
                                        continue
                                    if "type" not in response_json["errors"][0]:
                                        logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                        logging.info("login: " + login + ", count: " + str(count))
                                        continue
                                    if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                    continue
                                # handle the situation, when data doesn't existed, recover num_per_query and query
                                if "edges" not in response_json["data"]["user"]["issues"]:
                                    num_per_query = 100
                                    global query
                                    query = queries.query_github_user_issues
                                    logging.warn("losed data is successful handled!!!!")
                                # 写入文件
                                filename = base_path + "/" + login + "/" + str(count) + ".json"
                                flag = base.generate_file(filename, json.dumps(response_json))
                                if flag is True:
                                    logging.info("create file successfully: " + filename)
                                elif flag is False:
                                    logging.warn("file is already existed: " + filename)
                                else:
                                    logging.warn("create file failed: " + flag + " filename: " + filename)
                                if response_json["data"]["user"]["issues"]["pageInfo"]["hasNextPage"] is True:
                                    cursor = response_json["data"]["user"]["issues"]["pageInfo"]["endCursor"]
                                    count += 1
                                    continue
                            except (ConnectionError, ReadTimeout) as e:
                                logging.error(e)
                                continue
                            except Exception as e:
                                logging.fatal(e)
                                continue
                                # return
                            break
                    else:
                        logging.info("data of user: " + login + " was handled!")
            self.q.task_done()

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
            cursor = ""
            num_per_query = 100
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                # print github_token
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                if cursor == "":
                    condition = "first:" + str(num_per_query)
                else:
                    condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                + cursor + "\""
                values = {"query": query % (login, condition), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if response.status_code == 403:
                        logging.error("response.status_code: " + str(response.status_code))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        continue
                    if response.status_code != 200:
                        logging.error("response.status_code: " + str(response.status_code))
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                            logging.info("login: " + login + ", count: " + str(count))
                            if num_per_query > 1:
                                num_per_query /= 2
                                logging.warn(
                                    "num of per query minus half, after minus half, num_per_query: " + str(
                                        num_per_query))
                            else:  # when data doesn't existed, replace query sentence
                                global query
                                query = queries.query_github_user_issues_empty
                                logging.warn("replace query sentence to handle losed data")
                            continue
                        if "type" not in response_json["errors"][0]:
                            logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            logging.info("login: " + login + ", count: " + str(count))
                            continue
                        if response_json["errors"][0]["type"] == "RATE_LIMITED":
                            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        continue
                    # handle the situation, when data doesn't existed, recover num_per_query and query
                    if "edges" not in response_json["data"]["user"]["issues"]:
                        num_per_query = 100
                        global query
                        query = queries.query_github_user_issues
                        logging.warn("losed data is successful handled!!!!")
                    # 写入文件
                    filename = base_path + "/" + login + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["issues"]["pageInfo"]["hasNextPage"] is True:
                        cursor = response_json["data"]["user"]["issues"]["pageInfo"]["endCursor"]
                        count += 1
                        continue
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                    continue
                except Exception as e:
                    logging.error(e)
                    continue
                break
            self.q.task_done()

# crawl the recently all of pull request contribution
def  crawlUserPullRequests(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_logins = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_logins.append(item[0])
    logging.info("finish reading database")

    # read handled task from directory
    handled_logins = base.read_all_filename_none_path(base_path)

    # judge handled logins is whether was handled, if true, handle unhandled task
    for login in handled_logins:
        workQueue.put_nowait({"login": login})
    for _ in range(THREAD_NUM):
        judgeUserPullRequestThread(workQueue).start()
    workQueue.join()

    # unhandled logins
    unhandled_logins = list(set(unhandled_logins) - set(handled_logins))

    # unhandled tasks
    unhandled_tasks = []
    for login in unhandled_logins:
        unhandled_tasks.append({"login": login})
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

class judgeUserPullRequestThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]

            # get the max index in handled login directory
            directory_path = base_path + "/" + login
            filenames = base.read_all_filename_none_path(directory_path)
            indexes = []
            for filename in filenames:
                indexes.append(int(filename[:len(filename) - 5]))
            count = int(max(indexes))
            num_per_query = 100

            # judge task is whether was handled
            file_path = directory_path + "/" + str(count) + ".json"
            text = base.get_info_from_file(file_path)
            if text is False:
                logging.fatal("file not existed: " + file_path)
            else:
                obj = json.loads(text)
                logging.info("read file: " + file_path)
                if "hasNextPage" in obj["data"]["user"]["pullRequests"]["pageInfo"]:
                    hasNextPage = obj["data"]["user"]["pullRequests"]["pageInfo"]["hasNextPage"]
                    if hasNextPage is True:
                        cursor = obj["data"]["user"]["pullRequests"]["pageInfo"]["endCursor"]
                        count += 1
                        while True:
                            # get a suitable token and combine header
                            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                            # print github_token
                            headers = {
                                'Authorization': 'Bearer ' + github_token,
                                'Content-Type': 'application/json'
                            }
                            # print "headers is: " + str(headers)
                            condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                        + cursor + "\""
                            values = {"query": query % (login, condition), "variables": {}}
                            try:
                                response = requests.post(url=url, headers=headers, json=values, timeout=40)
                                if response.status_code == 403:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    continue
                                if response.status_code != 200:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    continue
                                response_json = response.json()
                                if "errors" in response_json:
                                    logging.error(json.dumps(response_json))
                                    if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                                        logging.info("login: " + login + ", count: " + str(count))
                                        if num_per_query > 1:
                                            num_per_query /= 2
                                            logging.warn(
                                                "num of per query minus half, after minus half, num_per_query: " + str(
                                                    num_per_query))
                                        else:    # when data doesn't existed, replace query sentence
                                            global query
                                            query = queries.query_github_user_pull_requests_empty
                                            logging.warn("replace query sentence to handle losed data")
                                        continue
                                    if "type" not in response_json["errors"][0]:
                                        logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                        logging.info("login: " + login + ", count: " + str(count))
                                        continue
                                    if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                    continue
                                # handle the situation, when data doesn't existed, recover num_per_query and query
                                if "edges" not in response_json["data"]["user"]["pullRequests"]:
                                    num_per_query = 100
                                    global query
                                    query = queries.query_github_user_pull_requests
                                    logging.warn("losed data is successful handled!!!!")
                                # 写入文件
                                filename = base_path + "/" + login + "/" + str(count) + ".json"
                                flag = base.generate_file(filename, json.dumps(response_json))
                                if flag is True:
                                    logging.info("create file successfully: " + filename)
                                elif flag is False:
                                    logging.warn("file is already existed: " + filename)
                                else:
                                    logging.warn("create file failed: " + flag + " filename: " + filename)
                                if response_json["data"]["user"]["pullRequests"]["pageInfo"]["hasNextPage"] is True:
                                    cursor = response_json["data"]["user"]["pullRequests"]["pageInfo"]["endCursor"]
                                    count += 1
                                    continue
                            except (ConnectionError, ReadTimeout) as e:
                                logging.error(e)
                                continue
                            except Exception as e:
                                logging.fatal(e)
                                continue
                                # return
                            break
                    else:
                        logging.info("data of user: " + login + " was handled!")
            self.q.task_done()

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
            cursor = ""
            num_per_query = 100
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                # print github_token
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                if cursor == "":
                    condition = "first:" + str(num_per_query)
                else:
                    condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                + cursor + "\""
                values = {"query": query % (login, condition), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if response.status_code == 403:
                        logging.error("response.status_code: " + str(response.status_code))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        continue
                    if response.status_code != 200:
                        logging.error("response.status_code: " + str(response.status_code))
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                            logging.info("login: " + login + ", count: " + str(count))
                            if num_per_query > 1:
                                num_per_query /= 2
                                logging.warn(
                                    "num of per query minus half, after minus half, num_per_query: " + str(
                                        num_per_query))
                            else:  # when data doesn't existed, replace query sentence
                                global query
                                query = queries.query_github_user_pull_requests_empty
                                logging.warn("replace query sentence to handle losed data")
                            continue
                        if "type" not in response_json["errors"][0]:
                            logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            logging.info("login: " + login + ", count: " + str(count))
                            continue
                        if response_json["errors"][0]["type"] == "RATE_LIMITED":
                            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        continue
                    # handle the situation, when data doesn't existed, recover num_per_query and query
                    if "edges" not in response_json["data"]["user"]["pullRequests"]:
                        num_per_query = 100
                        global query
                        query = queries.query_github_user_pull_requests
                        logging.warn("losed data is successful handled!!!!")
                    # 写入文件
                    filename = base_path + "/" + login + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["pullRequests"]["pageInfo"]["hasNextPage"] is True:
                        cursor = response_json["data"]["user"]["pullRequests"]["pageInfo"]["endCursor"]
                        count += 1
                        continue
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                    continue
                except Exception as e:
                    logging.error(e)
                    continue
                break
            self.q.task_done()

# crawl the recently all of pull request review contribution
def crawlUserPullRequestReview(p, q, sql):
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
        login = item[0]
        # judge the file is existed
        filename = base_path + "/" + login
        if base.judge_file_exist(filename):
            continue
        # unhandled tasks
        unhandled_tasks.append({"login": item[0], "created_at": item[1]})
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
            start_time = work["created_at"]
            final_time = "2020-12-12 00:00:00"
            while base.datetime_to_timestamp(start_time) < base.time_string_to_timestamp(final_time):
                end_time = base.add_one_year(start_time)
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
                    values = {"query": query % (login, base.datetime_to_github_time(start_time), base.datetime_to_github_time(end_time), after_cursor), "variables": {}}
                    try:
                        response = requests.post(url=url, headers=headers, json=values, timeout=40)
                        if response.status_code == 403:
                            logging.error("response.status_code: " + str(response.status_code))
                            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                            continue
                        if response.status_code != 200:
                            logging.error("response.status_code: " + str(response.status_code))
                            continue
                        response_json = response.json()
                        if "errors" in response_json:
                            logging.error(json.dumps(response_json))
                            if "type" not in response_json["errors"][0]:
                                logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                logging.info("login: " + login)
                                continue
                            if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                logging.info("RATE_LIMITED!!!!!!!!!!!!!!!!!!!!!")
                            logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            continue
                        # 写入文件
                        filename = base_path + "/" + login + "/" + base.datetime_to_github_time(start_time) + "_" + \
                                   base.datetime_to_github_time(end_time) + "/" + str(count) + ".json"
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
                        logging.fatal(e)
                        continue
                    break
                start_time = base.add_one_day(end_time)
            self.q.task_done()

# crawl the recently all of repository contribution
def crawlUserRepository(p, q, sql):
    global base_path
    global query
    global start_time
    global end_time
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
        login = item[0]
        # judge the file is existed
        filename = base_path + "/" + login
        if base.judge_file_exist(filename):
            continue
        # unhandled tasks
        unhandled_tasks.append({"login": item[0], "created_at": item[1]})
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
        crawlUserRepositoryThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlUserRepositoryThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            start_time = work["created_at"]
            final_time = "2020-12-12 00:00:00"
            while base.datetime_to_timestamp(start_time) < base.time_string_to_timestamp(final_time):
                end_time = base.add_one_year(start_time)
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
                    values = {"query": query % (login, base.datetime_to_github_time(start_time), base.datetime_to_github_time(end_time), after_cursor), "variables": {}}
                    try:
                        response = requests.post(url=url, headers=headers, json=values, timeout=40)
                        if response.status_code == 403:
                            logging.error("response.status_code: " + str(response.status_code))
                            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                            continue
                        if response.status_code != 200:
                            logging.error("response.status_code: " + str(response.status_code))
                            continue
                        response_json = response.json()
                        if "errors" in response_json:
                            logging.error(json.dumps(response_json))
                            if "type" not in response_json["errors"][0]:
                                logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                logging.info("login: " + login)
                                continue
                            if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                logging.info("RATE_LIMITED!!!!!!!!!!!!!!!!!!!!!")
                            logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            continue
                        # 写入文件
                        filename = base_path + "/" + login + "/" + base.datetime_to_github_time(start_time) + "_" + \
                                   base.datetime_to_github_time(end_time) + "/" + str(count) + ".json"
                        flag = base.generate_file(filename, json.dumps(response_json))
                        if flag is True:
                            logging.info("create file successfully: " + filename)
                        elif flag is False:
                            logging.warn("file is already existed: " + filename)
                        else:
                            logging.warn("create file failed: " + flag + " filename: " + filename)
                        if response_json["data"]["user"]["contributionsCollection"]["repositoryContributions"]["pageInfo"]["hasNextPage"] is True:
                            after_cursor = response_json["data"]["user"]["contributionsCollection"]["repositoryContributions"]["pageInfo"]["endCursor"]
                            count += 1
                            continue
                    except (ConnectionError, ReadTimeout) as e:
                        logging.error(e)
                        continue
                    except Exception as e:
                        logging.fatal(e)
                        continue
                    break
                start_time = base.add_one_day(end_time)
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
    unhandled_logins = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_logins.append(item[0])
    logging.info("finish reading database")

    # read handled task from directory
    handled_logins = base.read_all_filename_none_path(base_path)

    # judge handled logins is whether was handled, if true, handle unhandled task
    for login in handled_logins:
        workQueue.put_nowait({"login": login})
    for _ in range(THREAD_NUM):
        judgeUserCommitCommentHandledThread(workQueue).start()
    workQueue.join()

    # unhandled logins
    unhandled_logins = list(set(unhandled_logins) - set(handled_logins))

    # unhandled tasks
    unhandled_tasks = []
    for login in unhandled_logins:
        unhandled_tasks.append({"login": login})
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
        crawlUserCommitCommentThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class judgeUserCommitCommentHandledThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]

            # get the max index in handled login directory
            directory_path = base_path + "/" + login
            filenames = base.read_all_filename_none_path(directory_path)
            indexes = []
            for filename in filenames:
                indexes.append(int(filename[:len(filename) - 5]))
            count = int(max(indexes))
            num_per_query = 100

            # judge task is whether was handled
            file_path = directory_path + "/" + str(count) + ".json"
            text = base.get_info_from_file(file_path)
            if text is False:
                logging.fatal("file not existed: " + file_path)
            else:
                obj = json.loads(text)
                logging.info("read file: " + file_path)
                if "hasNextPage" in obj["data"]["user"]["commitComments"]["pageInfo"]:
                    hasNextPage = obj["data"]["user"]["commitComments"]["pageInfo"]["hasNextPage"]
                    if hasNextPage is True:
                        cursor = obj["data"]["user"]["commitComments"]["pageInfo"]["endCursor"]
                        count += 1
                        while True:
                            # get a suitable token and combine header
                            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                            # print github_token
                            headers = {
                                'Authorization': 'Bearer ' + github_token,
                                'Content-Type': 'application/json'
                            }
                            # print "headers is: " + str(headers)
                            condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                        + cursor + "\""
                            values = {"query": query % (login, condition), "variables": {}}
                            try:
                                response = requests.post(url=url, headers=headers, json=values, timeout=40)
                                if response.status_code == 403:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    continue
                                if response.status_code != 200:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    continue
                                response_json = response.json()
                                if "errors" in response_json:
                                    logging.error(json.dumps(response_json))
                                    if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                                        logging.info("login: " + login + ", count: " + str(count))
                                        if num_per_query > 1:
                                            num_per_query /= 2
                                            logging.warn(
                                                "num of per query minus half, after minus half, num_per_query: " + str(
                                                    num_per_query))
                                        else:    # when data doesn't existed, replace query sentence
                                            global query
                                            query = queries.query_github_user_commit_comments_empty
                                            logging.warn("replace query sentence to handle losed data")
                                        continue
                                    if "type" not in response_json["errors"][0]:
                                        logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                        logging.info("login: " + login + ", count: " + str(count))
                                        continue
                                    if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                    continue
                                # handle the situation, when data doesn't existed, recover num_per_query and query
                                if "edges" not in response_json["data"]["user"]["commitComments"]:
                                    num_per_query = 100
                                    global query
                                    query = queries.query_github_user_commit_comments
                                    logging.warn("losed data is successful handled!!!!")
                                # 写入文件
                                filename = base_path + "/" + login + "/" + str(count) + ".json"
                                flag = base.generate_file(filename, json.dumps(response_json))
                                if flag is True:
                                    logging.info("create file successfully: " + filename)
                                elif flag is False:
                                    logging.warn("file is already existed: " + filename)
                                else:
                                    logging.warn("create file failed: " + flag + " filename: " + filename)
                                if response_json["data"]["user"]["commitComments"]["pageInfo"]["hasNextPage"] is True:
                                    cursor = response_json["data"]["user"]["commitComments"]["pageInfo"]["endCursor"]
                                    count += 1
                                    continue
                            except (ConnectionError, ReadTimeout) as e:
                                logging.error(e)
                                continue
                            except Exception as e:
                                logging.fatal(e)
                                continue
                                # return
                            break
                    else:
                        logging.info("data of user: " + login + " was handled!")
            self.q.task_done()

class crawlUserCommitCommentThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            count = 1
            cursor = ""
            num_per_query = 100
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                # print github_token
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                if cursor == "":
                    condition = "first:" + str(num_per_query)
                else:
                    condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                + cursor + "\""
                values = {"query": query % (login, condition), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if response.status_code == 403:
                        logging.error("response.status_code: " + str(response.status_code))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        continue
                    if response.status_code != 200:
                        logging.error("response.status_code: " + str(response.status_code))
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                            logging.info("login: " + login + ", count: " + str(count))
                            if num_per_query > 1:
                                num_per_query /= 2
                                logging.warn(
                                    "num of per query minus half, after minus half, num_per_query: " + str(
                                        num_per_query))
                            else:  # when data doesn't existed, replace query sentence
                                global query
                                query = queries.query_github_user_commit_comments_empty
                                logging.warn("replace query sentence to handle losed data")
                            continue
                        if "type" not in response_json["errors"][0]:
                            logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            logging.info("login: " + login + ", count: " + str(count))
                            continue
                        if response_json["errors"][0]["type"] == "RATE_LIMITED":
                            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        continue
                    # handle the situation, when data doesn't existed, recover num_per_query and query
                    if "edges" not in response_json["data"]["user"]["commitComments"]:
                        num_per_query = 100
                        global query
                        query = queries.query_github_user_commit_comments
                        logging.warn("losed data is successful handled!!!!")
                    # 写入文件
                    filename = base_path + "/" + login + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["commitComments"]["pageInfo"]["hasNextPage"] is True:
                        cursor = response_json["data"]["user"]["commitComments"]["pageInfo"]["endCursor"]
                        count += 1
                        continue
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                    continue
                except Exception as e:
                    logging.error(e)
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
    unhandled_logins = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_logins.append(item[0])
    logging.info("finish reading database")

    # read handled task from directory
    handled_logins = base.read_all_filename_none_path(base_path)

    # judge handled logins is whether was handled, if true, handle unhandled task
    for login in handled_logins:
        workQueue.put_nowait({"login": login})
    for _ in range(THREAD_NUM):
        judgeUserIssueCommentHandledThread(workQueue).start()
    workQueue.join()

    # unhandled logins
    unhandled_logins = list(set(unhandled_logins) - set(handled_logins))

    # unhandled tasks
    unhandled_tasks = []
    for login in unhandled_logins:
        unhandled_tasks.append({"login": login})

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
        crawlUserIssueCommentThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class judgeUserIssueCommentHandledThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]

            # get the max index in handled login directory
            directory_path = base_path + "/" + login
            filenames = base.read_all_filename_none_path(directory_path)
            indexes = []
            for filename in filenames:
                indexes.append(int(filename[:len(filename) - 5]))
            count = int(max(indexes))
            num_per_query = 100

            # judge task is whether was handled
            file_path = directory_path + "/" + str(count) + ".json"
            text = base.get_info_from_file(file_path)
            if text is False:
                logging.fatal("file not existed: " + file_path)
            else:
                obj = json.loads(text)
                logging.info("read file: " + file_path)
                if "hasNextPage" in obj["data"]["user"]["issueComments"]["pageInfo"]:
                    hasNextPage = obj["data"]["user"]["issueComments"]["pageInfo"]["hasNextPage"]
                    if hasNextPage is True:
                        cursor = obj["data"]["user"]["issueComments"]["pageInfo"]["endCursor"]
                        count += 1
                        while True:
                            # get a suitable token and combine header
                            github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                            # print github_token
                            headers = {
                                'Authorization': 'Bearer ' + github_token,
                                'Content-Type': 'application/json'
                            }
                            # print "headers is: " + str(headers)
                            condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                        + cursor + "\""
                            values = {"query": query % (login, condition), "variables": {}}
                            try:
                                response = requests.post(url=url, headers=headers, json=values, timeout=40)
                                if response.status_code == 403:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    continue
                                if response.status_code != 200:
                                    logging.error("response.status_code: " + str(response.status_code))
                                    continue
                                response_json = response.json()
                                if "errors" in response_json:
                                    logging.error(json.dumps(response_json))
                                    if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                                        logging.info("login: " + login + ", count: " + str(count))
                                        if num_per_query > 1:
                                            num_per_query /= 2
                                            logging.warn(
                                                "num of per query minus half, after minus half, num_per_query: " + str(
                                                    num_per_query))
                                        else:    # when data doesn't existed, replace query sentence
                                            global query
                                            query = queries.query_github_user_issue_comments_empty
                                            logging.warn("replace query sentence to handle losed data")
                                        continue
                                    if "type" not in response_json["errors"][0]:
                                        logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                        logging.info("login: " + login + ", count: " + str(count))
                                        continue
                                    if response_json["errors"][0]["type"] == "RATE_LIMITED":
                                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                    logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                    continue
                                # handle the situation, when data doesn't existed, recover num_per_query and query
                                if "edges" not in response_json["data"]["user"]["issueComments"]:
                                    num_per_query = 100
                                    global query
                                    query = queries.query_github_user_issue_comments
                                    logging.warn("losed data is successful handled!!!!")
                                # 写入文件
                                filename = base_path + "/" + login + "/" + str(count) + ".json"
                                flag = base.generate_file(filename, json.dumps(response_json))
                                if flag is True:
                                    logging.info("create file successfully: " + filename)
                                elif flag is False:
                                    logging.warn("file is already existed: " + filename)
                                else:
                                    logging.warn("create file failed: " + flag + " filename: " + filename)
                                if response_json["data"]["user"]["issueComments"]["pageInfo"]["hasNextPage"] is True:
                                    cursor = response_json["data"]["user"]["issueComments"]["pageInfo"]["endCursor"]
                                    count += 1
                                    continue
                            except (ConnectionError, ReadTimeout) as e:
                                logging.error(e)
                                sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                continue
                            except Exception as e:
                                logging.fatal(e)
                                sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                                continue
                                # return
                            break
                    else:
                        logging.info("data of user: " + login + " was handled!")
            self.q.task_done()

class crawlUserIssueCommentThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while not self.q.empty():
            work = self.q.get(timeout=0)
            logging.info("the number of work in queue: " + str(self.q.qsize()))

            login = work["login"]
            count = 1
            cursor = ""
            num_per_query = 100
            while True:
                # get a suitable token and combine header
                github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
                # print github_token
                headers = {
                    'Authorization': 'Bearer ' + github_token,
                    'Content-Type': 'application/json'
                }
                # print "headers is: " + str(headers)
                if cursor == "":
                    condition = "first:" + str(num_per_query)
                else:
                    condition = "first:" + str(num_per_query) + ", after:" + "\"" \
                                + cursor + "\""
                values = {"query": query % (login, condition), "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if response.status_code == 403:
                        logging.error("response.status_code: " + str(response.status_code))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        continue
                    if response.status_code != 200:
                        logging.error("response.status_code: " + str(response.status_code))
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        if "Something went wrong while executing your query" in response_json["errors"][0]["message"]:
                            logging.info("login: " + login + ", count: " + str(count))
                            if num_per_query > 1:
                                num_per_query /= 2
                                logging.warn(
                                    "num of per query minus half, after minus half, num_per_query: " + str(
                                        num_per_query))
                            else:  # when data doesn't existed, replace query sentence
                                global query
                                query = queries.query_github_user_issue_comments_empty
                                logging.warn("replace query sentence to handle losed data")
                            continue
                        if "type" not in response_json["errors"][0]:
                            logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            logging.info("login: " + login + ", count: " + str(count))
                            continue
                        if response_json["errors"][0]["type"] == "RATE_LIMITED":
                            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        continue
                    # handle the situation, when data doesn't existed, recover num_per_query and query
                    if "edges" not in response_json["data"]["user"]["issueComments"]:
                        num_per_query = 100
                        global query
                        query = queries.query_github_user_issue_comments
                        logging.warn("losed data is successful handled!!!!")
                    # 写入文件
                    filename = base_path + "/" + login + "/" + str(count) + ".json"
                    flag = base.generate_file(filename, json.dumps(response_json))
                    if flag is True:
                        logging.info("create file successfully: " + filename)
                    elif flag is False:
                        logging.warn("file is already existed: " + filename)
                    else:
                        logging.warn("create file failed: " + flag + " filename: " + filename)
                    if response_json["data"]["user"]["issueComments"]["pageInfo"]["hasNextPage"] is True:
                        cursor = response_json["data"]["user"]["issueComments"]["pageInfo"]["endCursor"]
                        count += 1
                        continue
                except (ConnectionError, ReadTimeout) as e:
                    logging.error(e)
                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                    continue
                except Exception as e:
                    logging.fatal(e)
                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                    continue
                    # return
                break
            self.q.task_done()

# crawl all user sponsor listing data
def crawlAllUserSponsorListing(p, q, sql):
    global base_path
    global query
    base_path = p
    query = q
    workQueue = Queue.Queue()

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_logins = []
    cur.execute(sql)
    items = cur.fetchall()
    for item in items:
        unhandled_logins.append(item[0])
    logging.info("finish reading database")

    # read handled task from directory
    filenames = base.read_all_filename_none_path(base_path)
    handled_logins = []
    for filename in filenames:
        handled_logins.append(filename[:len(filename)-5])
    unhandled_logins = list(set(unhandled_logins)-set(handled_logins))

    # unhandled tasks
    unhandled_tasks = []
    for login in unhandled_logins:
        unhandled_tasks.append({"login": login})

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
        crawlAllUserSponsorListingThread(workQueue).start()
    workQueue.join()

    logging.info("finish")

class crawlAllUserSponsorListingThread(threading.Thread):
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
                values = {"query": query % login, "variables": {}}
                try:
                    response = requests.post(url=url, headers=headers, json=values, timeout=40)
                    if response.status_code != 200:
                        logging.error("response.status_code: " + str(response.status_code))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        continue
                    response_json = response.json()
                    if "errors" in response_json:
                        logging.error(json.dumps(response_json))
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        if "type" not in response_json["errors"][0]:
                            logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            logging.info("login: " + login)
                            continue
                        if response_json["errors"][0]["type"] == "NOT_FOUND":
                            Database.updateGithubUserFlag(login, str(base.flag1))
                            break
                        logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
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
                except (ConnectionError, ReadTimeout) as e:
                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                    logging.error(e)
                    continue
                except Exception as e:
                    sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                    logging.fatal(e)
                    continue
                break
            self.q.task_done()

def get_contributionYears(login):
    while True:
        # get a suitable token and combine header
        github_token = base.get_token(github_tokens, sleep_time_tokens, sleep_gap_token)
        # print github_token
        headers = {
            'Authorization': 'Bearer ' + github_token,
            'Content-Type': 'application/json'
        }
        # print "headers is: " + str(headers)
        values = {"query": queries.query_github_user_contributionYears % login, "variables": {}}
        try:
            response = requests.post(url=url, headers=headers, json=values, timeout=40)
            if response.status_code != 200:
                logging.error("response.status_code: " + str(response.status_code))
                sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                continue
            response_json = response.json()
            if "errors" in response_json:
                logging.error(json.dumps(response_json))
                sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                if "type" not in response_json["errors"][0]:
                    logging.fatal("unknown error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    logging.info("login: " + login)
                    continue
                logging.error("normal error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                continue
            return response_json["data"]["user"]["contributionsCollection"]["contributionYears"]
        except (ConnectionError, ReadTimeout) as e:
            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
            logging.error(e)
            continue
        except Exception as e:
            sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
            logging.fatal(e)
            continue