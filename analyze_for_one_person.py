
from utils import base
from utils import sql
import yaml as yaml
from matplotlib import pyplot as plt
import logging

# load logger
base.setup_logging(base.logging_path, logging.DEBUG)

end_time = "2020-11-12 00:00:00"
two_month = 5184000

f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)

def get_time_range(username):
    try:
        # create database connection
        db = base.connectMysqlDB(config)
        cur = db.cursor()

        sql = "select min(created_at) \
                from github_sponsorships_as_maintainer \
                where login='"+ username + "'"
        cur.execute(sql)
        times = cur.fetchall()
        earliest_sponsor_time = base.datetime_to_timestamp(times[0][0])

        # close this database connection
        cur.close()
        db.close()
    except Exception as e:
        logging.error("get_time_range failed")
        logging.error(e)
    last_time = base.time_string_to_timestamp(end_time)
    first_time = 2*earliest_sponsor_time - last_time
    mid_time = earliest_sponsor_time
    return [first_time, mid_time, last_time]

def analyze_nums_change(username, sql, compare_name):
    times = get_time_range(username)
    first_time = base.timestamp_to_time(times[0])
    mid_time = base.timestamp_to_time(times[1])
    last_time = base.timestamp_to_time(times[2])
    logging.info("first_time: " + first_time + ", mid_time: " + mid_time + ", last_time: " + last_time)

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # get commit sum between first_time and mid_time
    sql1 = sql % (username, first_time, mid_time)
    cur.execute(sql1)
    items = cur.fetchall()
    sum1 = items[0][0]

    # get commit sum between mid_time and last_time
    sql2 = sql % (username, mid_time, end_time)
    cur.execute(sql2)
    items = cur.fetchall()
    sum2 = items[0][0]

    # close this database connection
    cur.close()
    db.close()

    # draw picture
    x1 = ["before sponsoring"]
    y1 = [sum1]
    x2 = ["after sponsoring"]
    y2 = [sum2]
    plt.bar(x1, y1, color='g', align='center')
    plt.bar(x2, y2, color='b', align='center')
    plt.title(compare_name)
    plt.show()

    logging.info("sum1: " + str(sum1) + ", sum2: " + str(sum2))

def get_all_user_earliest_maintainer_time(month, sql=sql.all_user_earliest_maintainer_time):
    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # get get_all_user_earliest_maintainer_time
    sql1 = sql
    cur.execute(sql1)
    items = cur.fetchall()
    logging.info(str(items))

    # generate time interval
    users_time_interval = []
    for item in items:
        start_time = base.timestamp_to_time(base.datetime_to_timestamp(item[1])-month)
        end_time = base.timestamp_to_time(base.datetime_to_timestamp(item[1])+month)
        users_time_interval.append([item[0], start_time, item[1], end_time])

    # generate activity change
    users_acticity_change = []
    for item in users_time_interval:
        first_time = base.timestamp_to_time(item[1])
        mid_time = base.timestamp_to_time(item[2])
        last_time = base.timestamp_to_time(item[3])
        logging.info("first_time: " + first_time + ", mid_time: " + mid_time + ", last_time: " + last_time)

    # close this database connection
    cur.close()
    db.close()

if __name__ == "__main__":
    # analyze_nums_change("calebporzio", sql.user_issue_comment_sql, "user issue comment")
    # logging.info("qiubing")
    get_all_user_earliest_maintainer_time(two_month)

