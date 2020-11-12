# encoding=utf8
import os
import json
from datetime import datetime, timedelta
import time
import MySQLdb

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
                sleep_time_tokens[token] = cur_time
                return token
        time.sleep(50)

def judge_http_response(response):
    if response.status_code != 200:
        print("response.status_code: " + str(response.status_code))
        return False
    response_json = response.json()
    if "errors" in response_json:
        print json.dumps(response_json)
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
    print read_all_filename_in_directory("/home/qiubing/github/sponsor/user/issue")