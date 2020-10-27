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
import datetime


# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 10
base_path = "/home/qiubing/github/comments"

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
        # get db connection
        db = connectMysqlDB(config, autocommit=False)
        cur = db.cursor()

        while True:
            try:
                print ""
                work = self.q.get(timeout=0)
                print "the number of work in queue: " + str(self.q.qsize())

                number = work["number"]
                owner = work["owner"]
                repo = work["repo"]
                page = 1
                sum = 0  # sum of inserted db

                # every issue has several pages
                while True:
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
                    url = "https://api.github.com/repos/" + owner + "/" + repo + "/issues" + "/" + str(number) + "/comments"
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


                        length = len(result)
                        sum += length
                        if length == 0:
                            print "finish, issue " + str(number) + " has comments: " + str(sum)
                            self.q.task_done()
                            break

                        # write file
                        json_str = json.dumps(result)
                        # print "json format data: " + json_str
                        filename = base_path + "/" + owner + "&" + repo + "/" + str(number) + "/" + str(page) + ".json"
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
                            if "login" not in result[num]["user"]:
                                insert_dict["user_login"] = None
                            else:
                                insert_dict["user_login"] = result[num]["user"]["login"]
                            if "created_at" not in result[num]:
                                insert_dict["created_at"] = None
                            else:
                                insert_dict["created_at"] = result[num]["created_at"]
                            if "updated_at" not in result[num]:
                                insert_dict["updated_at"] = None
                            else:
                                insert_dict["updated_at"] = result[num]["updated_at"]
                            if "heart" not in result[num]["reactions"]:
                                insert_dict["heart"] = None
                            else:
                                insert_dict["heart"] = result[num]["reactions"]["heart"]
                            if "eyes" not in result[num]["reactions"]:
                                insert_dict["eyes"] = None
                            else:
                                insert_dict["eyes"] = result[num]["reactions"]["eyes"]
                            if "rocket" not in result[num]["reactions"]:
                                insert_dict["rocket"] = None
                            else:
                                insert_dict["rocket"] = result[num]["reactions"]["rocket"]
                            if "total_count" not in result[num]["reactions"]:
                                insert_dict["total_count"] = None
                            else:
                                insert_dict["total_count"] = result[num]["reactions"]["total_count"]
                            if "confused" not in result[num]["reactions"]:
                                insert_dict["confused"] = None
                            else:
                                insert_dict["confused"] = result[num]["reactions"]["confused"]
                            if "hooray" not in result[num]["reactions"]:
                                insert_dict["hooray"] = None
                            else:
                                insert_dict["hooray"] = result[num]["reactions"]["hooray"]
                            if "+1" not in result[num]["reactions"]:
                                insert_dict["up"] = None
                            else:
                                insert_dict["up"] = result[num]["reactions"]["+1"]
                            if "laugh" not in result[num]["reactions"]:
                                insert_dict["laugh"] = None
                            else:
                                insert_dict["laugh"] = result[num]["reactions"]["laugh"]
                            if "-1" not in result[num]["reactions"]:
                                insert_dict["down"] = None
                            else:
                                insert_dict["down"] = result[num]["reactions"]["-1"]
                            print "insert info: " + str(insert_dict)

                            # insert data to database table
                            try:
                                if insert_dict is not None:
                                    cur.execute("insert into github_comment "
                                                "(id, issue_number, user_login, owner_login, repo, created_at, updated_at, total_count, up, down, laugh, confused, heart, hooray, rocket, eyes) "
                                                "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                                (insert_dict["id"], number, insert_dict["user_login"],
                                                 owner, repo, base.time_handler(insert_dict["created_at"]), base.time_handler(insert_dict["updated_at"]),
                                                 insert_dict["total_count"], insert_dict["up"], insert_dict["down"],
                                                 insert_dict["laugh"], insert_dict["confused"], insert_dict["heart"],
                                                 insert_dict["hooray"], insert_dict["rocket"], insert_dict["eyes"]))
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
            except Queue.Empty:
                cur.close()
                db.close()
                return
            except Exception as e:
                print str(e) # unexpected error, don't interrupt the program



if __name__ == "__main__":

    workQueue = Queue.Queue()

    # create database connection
    db = connectMysqlDB(config)
    cur = db.cursor()

    # read all the info
    unhandled_tasks = []
    cur.execute("select issue.number, issue.owner_login, issue.repo "
                "from github_issue as issue "
                "where issue.number not in (select distinct issue_number from github_comment) and issue.comments!=0")
    items = cur.fetchall()

    for item in items:
        unhandled_tasks.append({"number": int(item[0]),
                                "owner": item[1],
                                "repo": item[2],
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