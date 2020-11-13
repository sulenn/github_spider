
from utils import base
from utils import sql
import yaml as yaml
from matplotlib import pyplot as plt

end_time = "2020-11-12 00:00:00"

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
        print "get_time_range failed"
        print e
    last_time = base.time_string_to_timestamp(end_time)
    first_time = 2*earliest_sponsor_time - last_time
    mid_time = earliest_sponsor_time
    return [first_time, mid_time, last_time]

def analyze_nums_change(username, sql, compare_name):
    times = get_time_range(username)
    first_time = base.timestamp_to_time(times[0])
    mid_time = base.timestamp_to_time(times[1])
    last_time = base.timestamp_to_time(times[2])
    print "first_time: " + first_time + ", mid_time: " + mid_time + ", last_time: " + last_time

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

    print "sum1: " + str(sum1) + ", sum2: " + str(sum2)

if __name__ == "__main__":
    analyze_nums_change("calebporzio", sql.user_issue_comment_sql, "user issue comment")
    print "qiubing"
