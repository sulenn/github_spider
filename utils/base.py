# encoding=utf8
import os
import json
from datetime import datetime, timedelta

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

if __name__ == "__main__":
    # print judge_file_exist("/home/qiubing/github/issues/rails&rails/")
    # print generate_dir("/home/qiubing/github/issues/rails&rails/")
    # print judge_file_exist("/home/qiubing/github/issues/rails&rails/")

    # print judge_file_exist("/home/qiubing/github/issues/rails&rails/hello/1.json")
    # print generate_file("/home/qiubing/github/issues/rails&rails/hello/1.json", "hello, world!")
    # print judge_file_exist("/home/qiubing/github/issues/rails&rails/hello/1.json")

    json_str = get_info_from_file("/home/qiubing/github/issues/sulenn&blogDir&1/1.json")
    print json_str
    json_obj = json.loads(json_str)
    print json_obj