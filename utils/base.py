# encoding=utf8
import os
import json
from datetime import datetime, timedelta
import time
import MySQLdb
import yaml
import logging
import logging.config

config_path = "/home/qiubing/PycharmProjects/spider-python/config.yaml"
logging_path = "/home/qiubing/PycharmProjects/spider-python/logging.yaml"

# flag0 is user
flag0 = 0
# flag1 is organization
flag1 = 1
# flag2 is private
flag2 = 2
# flag3 is unknown
flag3 = 3
# flag4: sponsor_login didn't have sponsor others
flag4 = 4
# flag5: login is not existed
flag5 = 5

# if the file or directory is exited, return True, or False
def judge_file_exist(filename):
    return os.path.exists(filename)

def generate_dir(path):
    if judge_file_exist(path):
        return "dir " + path + " is existed"
    try:
        os.makedirs(path)
        return True
    except Exception as e:
        return False

def generate_file(filename, text):
    try:
        index = filename.rfind('/')    # only for linux
        if index != -1 and judge_file_exist(filename[:index]) is False:
            generate_dir(filename[:index])
        if judge_file_exist(filename):
            return False
        file = open(filename, 'w')
        file.write(text)  # 写入内容信息
        file.close()
        return True
    except Exception as e:
        return str(e)

def get_info_from_file(filename):
    if judge_file_exist(filename) is False:
        return False
    file = open(filename, 'r')
    text = file.read()  # 写入内容信息
    file.close()
    return text

def time_handler(target_time):
    _date = datetime.strptime(target_time, "%Y-%m-%dT%H:%M:%SZ")
    local_time = _date + timedelta(hours=8)
    end_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return end_time

# get a suitable token
def get_token(github_tokens, sleep_time_tokens, sleep_gap_token):
    while(True):
        # get the minimum count times for token
        for token in github_tokens:
            cur_time = time.time()
            if cur_time - sleep_time_tokens[token] > sleep_gap_token:
                return token
        time.sleep(50)

def judge_http_response(response):
    if response.status_code != 200:
        logging.error("response.status_code: " + str(response.status_code))
        return False
    response_json = response.json()
    if "errors" in response_json:
        logging.error(json.dumps(response_json))
        return False
    return True

# read all recursive file path in directory, not include directory name in returns
def read_all_filename_in_directory(path):
    g = os.walk(path)
    files_path = []
    for path, dir_list, file_list in g:
        for file_name in file_list:
            files_path.append(os.path.join(path, file_name))
    return files_path

# read all file name
def read_all_filename_none_path(path):
    return os.listdir(path)

# return unix time
def time_string_to_timestamp(t):
    time_Array = time.strptime(t, "%Y-%m-%d %H:%M:%S")
    time_stamp = time.mktime(time_Array)
    return time_stamp

# return unix time
def datetime_to_timestamp(t):
    time_tuple = t.timetuple()
    time_stamp = time.mktime(time_tuple)
    return time_stamp

# input unix time
def timestamp_to_time(timestamp, format="%Y-%m-%d %H:%M:%S"):
    time_local = time.localtime(timestamp)
    dt = time.strftime(format, time_local)
    return dt

def read_database_config():
    f = open(config_path, 'r')
    config = yaml.load(f.read(), Loader=yaml.BaseLoader)
    return config

# judge the result of sql is null
def judge_sql_result(sql):
    # create database connection
    db = connectMysqlDB(read_database_config())
    cur = db.cursor()

    # read all the repos
    cur.execute(sql)
    items = cur.fetchall()

    # close this database connection
    cur.close()
    db.close()
    if len(items) == 0:
        return False
    else:
        return True

def setup_logging(default_path=logging_path, default_level=logging.INFO):
    path = default_path
    if os.path.exists(path):
        with open(path, 'r') as f:
            config = yaml.load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

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

if __name__ == "__main__":
    # print judge_file_exist("/home/qiubing/github/issues/rails&rails/")
    # print generate_dir("/home/qiubing/github/issues/rails&rails/")
    # print judge_file_exist("/home/qiubing/github/issues/rails&rails/")

    # print judge_file_exist("/home/qiubing/github/issues/rails&rails/hello/1.json")
    # print generate_file("/home/qiubing/github/issues/rails&rails/hello/1.json", "hello, world!")
    # print judge_file_exist("/home/qiubing/github/issues/rails&rails/hello/1.json")

    # json_str = get_info_from_file("/home/qiubing/github/issues/sulenn&blogDir&1/1.json")
    # print json_str
    # json_obj = json.loads(json_str)
    # print json_obj

    # print judge_file_exist("/home/qiubing/github/sponsor/user/issue/calebporzio/2020-09-02T00:00:00Z_2020-11-12T00:00:00Z/1.json")
    #
    # print judge_file_exist(
    #     "/home/qiubing/github/sponsor/user/issue/calebporzio/2020-09-02T00:00:00Z_2020-11-12T00:00:00Z/")
    #
    # print os.listdir("/home/qiubing/github/sponsor/user/issue/calebporzio/2020-09-02T00:00:00Z_2020-11-12T00:00:00Z")
    # print os.listdir("/home/qiubing/github/sponsor/user/issue/calebporzio/2020-09-02T00:00:00Z_2020-11-12T00:00:00Z/1.json")

    # g = os.walk(r"/home/qiubing/github/sponsor/user/issue/calebporzio/2017-09-01T00:00:00Z_2018-09-01T00:00:00Z/1.json")
    #
    # for path, dir_list, file_list in g:
    #     for file_name in file_list:
    #         print(os.path.join(path, file_name))
    # print read_all_filename_none_path("/home/qiubing/github/sponsor/all/user/sponsorlisting")
    temp = os.listdir("/home/qiubing/github/sponsor/user/issue-comments")
    logging.info(temp)