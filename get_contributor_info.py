# encoding=utf8
# crawl missed issue comments in mongodb

import time
import threading
import Queue

import MySQLdb
import yaml as yaml
import urllib2
import json
import datetime
from utils import base
from datetime import datetime, timedelta


# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 1
base_path = "/home/qiubing/github/contributors/"

# read all the tokens
f = open('github_tokens.txt', 'r')
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

def time_handler(target_time):
    _date = datetime.strptime(target_time, "%Y-%m-%dT%H:%M:%SZ")
    local_time = _date + timedelta(hours=8)
    end_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return end_time

# the thread for processing each pr
class crawlThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        work = self.q.get(timeout=0)
        print "the number of work in queue: " + str(self.q.qsize())

        id = work["repo_id"]
        owner = work["owner"]
        repo = work["repo"]
        page = 1
        sum = 0       # sum of inserted db

        # get db connection
        db = connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        while True:
            print ""
            try:
                # get a suitable token and combine header
                github_token = get_token()
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Authorization': 'token ' + github_token,
                    'Content-Type': 'application/json',
                    'method': 'GET',
                    'Accept': 'application/vnd.github.squirrel-girl-preview+json'

                }
                # print "headers is: " + str(headers)

                # combine url, notice: per page is 30
                url = "https://api.github.com/repos/" + owner + "/" + repo + "/contributors"
                url = url + "?anon=true" + "&page=" + str(page)
                print "url is: " + url

                insert_dict = {}
                try:
                    # request data and parse response
                    req = urllib2.Request(
                        url=url,
                        headers=headers
                    )
                    response = urllib2.urlopen(req)
                    result = json.loads(response.read().decode("utf-8"))
                    # print result

                    # judge response info empty
                    length = len(result)
                    sum += length
                    if length == 0:
                        # close the db connection
                        cur.close()
                        db.close()
                        print "finish & the sum of issue of pull request is: " + str(sum)
                        self.q.task_done()
                        return

                    # write file
                    json_str = json.dumps(result)
                    # print "json format data: " + json_str
                    filename = base_path + "/" + owner + "&" + repo + "&" + str(id) + "/" + str(page) + ".json"
                    flag = base.generate_file(filename, json_str)
                    if flag is True:
                        print "create file successfully: " + filename
                    elif flag is False:
                        print "file is already existed: " + filename
                    else:
                        print "create file failed: " + flag + " filename: " + filename
                        continue

                    page += 1  # page++

                    # handle response json data
                    num = 0
                    while num < length:
                        insert_dict = {}
                        if "id" not in result[num]:
                            insert_dict["id"] = None
                        else:
                            insert_dict["id"] = result[num]["id"]
                        if "login" not in result[num]:
                            insert_dict["login"] = None
                        else:
                            insert_dict["login"] = result[num]["login"]
                        if "type" not in result[num]:
                            insert_dict["type"] = None
                        else:
                            insert_dict["type"] = result[num]["type"]
                        if "contributions" not in result[num]:
                            insert_dict["contributions"] = None
                        else:
                            insert_dict["contributions"] = result[num]["contributions"]
                        print "insert info: " + str(insert_dict)

                        # insert data to database table
                        try:    # if insert data error, should keep on
                            if insert_dict is not None:
                                cur.execute("insert into github_contributor "
                                            "(id, login, owner_login, repo_id, repo, type, contributions) "
                                            "values (%s, %s, %s, %s, %s, %s, %s)",
                                            (insert_dict["id"], insert_dict["login"],
                                             owner, id, repo, insert_dict["type"], insert_dict["contributions"]))
                                db.commit()
                        except Exception as e:
                            print str(e)
                        num += 1
                except urllib2.HTTPError as e:
                    print str(e.code) + " error with this page: " + url
                    if e.code != 404:
                        # mainly 403, sometimes 503
                        # token rate limit
                        self.q.put(work)  # put into the queue again
                        sleep_time_tokens[github_token] = time.time()  # set sleep time for that token
                        insert_dict = None
                    else:
                        insert_dict["body"] = "404 error"
                        insert_dict["created_at"] = None
                        insert_dict["updated_at"] = None
                else:
                    pass  # 403... error
            except Exception as e:
                print str(e) # unexpected error, don't interrupt the program



if __name__ == "__main__":

    workQueue = Queue.Queue()

    # create database connection
    db = connectMysqlDB(config)
    cur = db.cursor()

    # read all the repos
    unhandled_tasks = []
    cur.execute("select id, owner, name "
                "from github_repo ")
    items = cur.fetchall()
    for item in items:
        unhandled_tasks.append({"repo_id": int(item[0]),
                                "owner": item[1],
                                "repo": item[2]
                                })
    print "finish reading repos"
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

    # print time_handler("2020-09-23T13:53:35Z")