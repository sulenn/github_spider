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


# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)
THREAD_NUM = 10

# read all the tokens
f = open('github_tokens.txt', 'r')
github_tokens = f.read().strip().split("\n")

use_time_count = {} # record the times of each token
sleep_time_tokens = {} # record the sleep time of each token
sleep_gap_token = 1800 # the sleep time of each token
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
            if time.time() - sleep_time_tokens[token] > sleep_gap_token:
                # remain_times = get_remain_times(token)
                # print token + " remain: " + str(remain_times)
                # if remain_times >= 100:
                #     use_time_count[token] += 1
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

                         sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION',

                         autocommit=autocommit)
    return db

# the thread for processing each pr
class crawlThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        while True:
            try:

                work = self.q.get(timeout=0)

                print self.q.qsize()

                owner = work["owner"]
                repo = work["repo"]
                github_id = work["github_id"]
                comment_id = work["comment_id"]
                issue_id = work["issue_id"]

                url = "https://api.github.com/repos/" + owner + "/" + repo + "/issues/comments/" + str(comment_id)

                # get a suitable token
                github_token = get_token()
                url = url + "?access_token=" + github_token
                print url

                # get db connection
                db = connectMysqlDB(config, autocommit=False)
                cur = db.cursor()

                # handle this url
                insert_dict = {}
                try:
                    req = urllib2.urlopen(url)
                    result = json.loads(req.read().decode("utf-8"))

                    if "body" not in result:
                        insert_dict["body"] = None
                    else:
                        insert_dict["body"] = result["body"]

                    if "created_at" not in result:
                        insert_dict["created_at"] = None
                    else:
                        insert_dict["created_at"] = result["created_at"]

                    if "updated_at" not in result:
                        insert_dict["updated_at"] = None
                    else:
                        insert_dict["updated_at"] = result["updated_at"]

                except urllib2.HTTPError as e:
                    print str(e.code) + " error with this page: " + url
                    if e.code != 404:
                        # mainly 403, sometimes 503
                        # token rate limit
                        self.q.put(work) # put into the queue again
                        sleep_time_tokens[github_token] = time.time() # set sleep time for that token
                        insert_dict = None
                    else:
                        insert_dict["body"] = "404 error"
                        insert_dict["created_at"] = None
                        insert_dict["updated_at"] = None

                if insert_dict is not None:
                    cur.execute("insert into reduced_issue_comments_mongo "
                                "(issue_id, mongo_comment_id, created_at, updated_at, body, owner, repo, mongo_github_id) "
                                "values (%s, %s, %s, %s, %s, %s, %s, %s)",
                                (issue_id, comment_id, insert_dict["created_at"], insert_dict["updated_at"], insert_dict["body"], owner, repo, github_id))
                else:
                    pass # 403... error
                # commit for this pr and close the db connection
                db.commit()
                cur.close()
                db.close()

            except Queue.Empty:
                return
            except Exception as e:
                print str(e) # unexpected error, don't interrupt the program
            self.q.task_done()



if __name__ == "__main__":

    workQueue = Queue.Queue()

    # create database connection
    db = connectMysqlDB(config)
    cur = db.cursor()

    # read all the comment_id related owner, repo, github_id
    comment_dict = {}
    cur.execute("select ru.login, rp.name, ri.issue_id, ric.comment_id, ric.issue_id "
                "from reduced_issues ri, reduced_users ru, reduced_projects rp, reduced_issue_comments ric "
                "where ric.issue_id = ri.id "
                "and ri.repo_id = rp.id "
                "and rp.owner_id = ru.id")
    items = cur.fetchall()
    for item in items:
        owner = item[0]
        repo = item[1]
        github_id = int(item[2])
        comment_id = long(item[3])
        issue_id = int(item[4])
        comment_dict[comment_id] = (owner, repo, github_id, issue_id)
    print "finish reading comment_dict"

    # read all the handled tasks
    handled_tasks = set()
    cur.execute("select mongo_comment_id from reduced_issue_comments_mongo")
    items = cur.fetchall()
    for item in items:
        comment_id = long(item[0])
        handled_tasks.add(comment_id)

    # read all the github_ids, and get the unhandled tasks
    unhandled_tasks = []
    cur.execute("select distinct comment_id "
                "from reduced_issue_comments")
    items = cur.fetchall()
    for item in items:
        comment_id = long(item[0])

        if comment_id in handled_tasks:
            continue # already handled

        owner, repo, github_id, issue_id = comment_dict[comment_id]

        unhandled_tasks.append({"owner": owner,
                                "repo": repo,
                                "github_id": github_id,
                                "comment_id": comment_id,
                                "issue_id": issue_id})

    print "finish getting unhandled tasks"
    print "%d tasks left for handling" % (len(unhandled_tasks))

    # close this database connection
    cur.close()
    db.close()

    for task in unhandled_tasks:
        workQueue.put_nowait(task)

    for _ in range(THREAD_NUM):
        crawlThread(workQueue).start()
    workQueue.join()

    print "final finish"