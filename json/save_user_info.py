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
f = open('../config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 1
base_path = "/home/qiubing/github/sponsor/user"
url = "https://api.github.com/graphql"

# read all the tokens
f = open('../github_tokens.txt', 'r')
github_tokens = f.read().strip().split("\n")

use_time_count = {} # record the times of each token
sleep_time_tokens = {} # record the sleep time of each token
sleep_gap_token = 1.8 # the sleep time of each token
for token in github_tokens:
    use_time_count.setdefault(token, 0)
    sleep_time_tokens.setdefault(token, -1)

max_commit_time_pr = {} # record the max created_at time for each pr


# get a suitable token
def get_token():
    while(True):
        # get the minimum count times for token
        # token = min(use_time_count, key=use_time_count.get)
        for token in github_tokens:
            cur_time = time.time()
            if cur_time - sleep_time_tokens[token] > sleep_gap_token:
                # remain_times = get_remain_times(token)
                # print token + " remain: " + str(remain_times)
                # if remain_times >= 100:
                #     use_time_count[token] += 1
                sleep_time_tokens[token] = cur_time
                return token
        time.sleep(50)

def connectMysqlDB(config, autocommit = True):

    db = MySQLdb.connect(host=config['mysql']['host'],
                         user=config['mysql']['user'],
                         passwd=config['mysql']['passwd'],
                         db=config['mysql']['db'],

                         local_infile=1,
                         use_unicode=True,
                         charset='utf8mb4',

                         sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION',

                         autocommit=autocommit)
    return db

# the thread for processing each pr
class crawlThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        login = work["login"]
        # get a suitable token and combine header
        github_token = get_token()
        headers = {
            'Authorization': 'Bearer ' + github_token,
            'Content-Type': 'application/json'
        }
        # print "headers is: " + str(headers)
        query = """query {
                user(login:"dlemstra") {
                    name
                    email
                    login
                    bio
                    company
                    createdAt
                    updatedAt
                    databaseId
                    isBountyHunter
                    isCampusExpert
                    isDeveloperProgramMember
                    isEmployee
                    isHireable
                    isSiteAdmin
                    location
                    projectsResourcePath
                    projectsUrl
                    url
                    websiteUrl
                    resourcePath
                    twitterUsername
                }
            }
        """
        values = {"query": query, "variables": {}}
        try:
            response = requests.post(url=url, headers=headers, json=values)
            response_json = response.json()
            print("response.status_code: " + str(response.status_code))
            if response.status_code != 200:
                print("request error at: ")
            # 写入文件
            filename = base_path + "/" + login + ".json"
            flag = base.generate_file(filename, json.dumps(response_json))
            if flag is True:
                print "create file successfully: " + filename
            elif flag is False:
                print "file is already existed: " + filename
            else:
                print "create file failed: " + flag + " filename: " + filename
            self.q.task_done()
        except Exception as e:
            print(e)
            # print("other exception at: " + topic)
            # logger.error("other exception at: " + topic)



if __name__ == "__main__":

    workQueue = Queue.Queue()

    # create database connection
    db = connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute("select login "
                "from init_user ")
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"login": item[0]})
    print "finish reading database"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        crawlThread(workQueue).start()
    workQueue.join()

    print "finish"
