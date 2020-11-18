# encoding=utf8
# crawl missed issue comments in mongodb

import time
import threading
import Queue

import MySQLdb
import yaml as yaml
import urllib2
import json
from utils import base


# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 1
base_path = "/home/qiubing/github/commits"

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

                # combine url
                url = "https://api.github.com/repos/" + owner + "/" + repo + "/commits"
                url = url + "?page=" + str(page)
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
                        if "sha" not in result[num]:
                            insert_dict["commit_hash"] = None
                        else:
                            insert_dict["commit_hash"] = result[num]["sha"]
                        if "author" not in result[num]["commit"]:
                            insert_dict["author"] = None
                        else:
                            insert_dict["author"] = result[num]["commit"]["author"]["name"]
                            insert_dict["email"] = result[num]["commit"]["author"]["email"]
                            insert_dict["time"] = result[num]["commit"]["author"]["date"]
                        if "message" not in result[num]["commit"]:
                            insert_dict["message"] = None
                        else:
                            insert_dict["message"] = result[num]["commit"]["message"]
                        print "insert info: " + str(insert_dict)

                        # insert data to database table
                        try:
                            if insert_dict is not None:
                                cur.execute("insert into github_commit "
                                            "(commit_hash, repo_id, author, email, time, message) "
                                            "values (%s, %s, %s, %s, %s, %s)",
                                            (insert_dict["commit_hash"], id, insert_dict["author"],
                                             insert_dict["email"], base.time_handler(insert_dict["time"]), insert_dict["message"]))
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
        if item[1] == "FISCO-BCOS":
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
