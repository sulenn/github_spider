# encoding=utf8
# crawl missed issue comments in mongodb

import MySQLdb
import yaml as yaml
import matplotlib.pyplot as plt

# define some global things
# db config file
f = open('../config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)

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

# show height
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        plt.text(rect.get_x()+rect.get_width()/2.- 0.2, 1.03*height, '%s' % int(height))

if __name__ == "__main__":
    # create database connection
    db = connectMysqlDB(config)
    cur = db.cursor()

    owner_login = "rails"
    repo = "rails"
    total_sum = dict()

    # read all the info
    # read issue emoji sum
    cur.execute("select user_login as username, sum(up) as up_sum, sum(down) as down_sum, sum(laugh) as laugh_sum, "
			    "sum(confused) as confused_sum, sum(heart) as heart_sum, sum(hooray) as hooray_sum, sum(rocket) as rocket_sum, "
			    "sum(eyes) as eyes_sum "
                "from github_issue "
                "where owner_login='" + owner_login + "' and repo='" + repo + "' and flag=0 "
                "group by user_login "
                "having sum(total_count)>0")
    issue_emoji_sum_items = cur.fetchall()
    for item in issue_emoji_sum_items:  # calculate all positive emojis
        username = item[0]
        up_sum = int(item[1])
        up_down = int(item[2])
        up_laugh = int(item[3])
        up_confused = int(item[4])
        up_heart = int(item[5])
        up_hooray = int(item[6])
        up_rocket = int(item[7])
        up_eyes = int(item[8])
        total_sum[username] = (up_sum + up_laugh + up_heart + up_hooray + up_rocket) * 5 - up_down * 2

    # read pull request emoji sum
    cur.execute("select user_login as username, sum(up) as up_sum, sum(down) as down_sum, sum(laugh) as laugh_sum, "
                "sum(confused) as confused_sum, sum(heart) as heart_sum, sum(hooray) as hooray_sum, sum(rocket) as rocket_sum, "
                "sum(eyes) as eyes_sum "
                "from github_issue "
                "where owner_login='" + owner_login + "' and repo='" + repo + "' and flag=1 "
                "group by user_login "
                "having sum(total_count)>0")
    pull_request_emoji_sum_items = cur.fetchall()
    for item in pull_request_emoji_sum_items:  # calculate all positive emojis
        username = item[0]
        up_sum = int(item[1])
        up_down = int(item[2])
        up_laugh = int(item[3])
        up_confused = int(item[4])
        up_heart = int(item[5])
        up_hooray = int(item[6])
        up_rocket = int(item[7])
        up_eyes = int(item[8])
        total_sum[username] = (up_sum + up_laugh + up_heart + up_hooray + up_rocket) * 8 - up_down * 3

    # read issue comment emoji sum
    cur.execute("select user_login as username, sum(up) as up_sum, sum(down) as down_sum, sum(laugh) as laugh_sum, "
			    "sum(confused) as confused_sum, sum(heart) as heart_sum, sum(hooray) as hooray_sum, sum(rocket) as rocket_sum, "
			    "sum(eyes) as eyes_sum "
                "from github_comment "
                "where owner_login='" + owner_login + "' and repo='" + repo + "' and issue_number in (select distinct number from github_issue where flag=0 and owner_login='" + owner_login + "' and repo='" + repo + "') "
                "GROUP BY user_login "
                "having sum(total_count)>0 "
                "ORDER BY up_sum desc")
    issue_comment_emoji_sum_items = cur.fetchall()
    for item in issue_comment_emoji_sum_items:  # calculate all positive emojis
        username = item[0]
        up_sum = int(item[1])
        up_down = int(item[2])
        up_laugh = int(item[3])
        up_confused = int(item[4])
        up_heart = int(item[5])
        up_hooray = int(item[6])
        up_rocket = int(item[7])
        up_eyes = int(item[8])
        total_sum[username] = (up_sum + up_laugh + up_heart + up_hooray + up_rocket) * 5 - up_down * 2

    # read pull request comment emoji sum
    cur.execute("select user_login as username, sum(up) as up_sum, sum(down) as down_sum, sum(laugh) as laugh_sum, "
                "sum(confused) as confused_sum, sum(heart) as heart_sum, sum(hooray) as hooray_sum, sum(rocket) as rocket_sum, "
                "sum(eyes) as eyes_sum "
                "from github_comment "
                "where owner_login='" + owner_login + "' and repo='" + repo + "' and issue_number in (select distinct number from github_issue where flag=1 and owner_login='" + owner_login + "' and repo='" + repo + "') "
                "GROUP BY user_login "
                "having sum(total_count)>0 "
                "ORDER BY up_sum desc")
    pull_request_comment_emoji_sum_items = cur.fetchall()
    for item in pull_request_emoji_sum_items:  # calculate all positive emojis
        username = item[0]
        up_sum = int(item[1])
        up_down = int(item[2])
        up_laugh = int(item[3])
        up_confused = int(item[4])
        up_heart = int(item[5])
        up_hooray = int(item[6])
        up_rocket = int(item[7])
        up_eyes = int(item[8])
        total_sum[username] = (up_sum + up_laugh + up_heart + up_hooray + up_rocket) * 8 - up_down * 3

    # cur.execute("select user_login, count(*) as sum "
    #             "from github_reaction "
    #             "where owner_login='rails' and repo='rails' and content='-1' "
    #             "group by user_login "
    #             "order by sum desc")
    # persons_to_down_items = cur.fetchall()

    # for item in persons_to_down_items:   # calculate all negative emojis
    #     username = item[0]
    #     sum = int(item[1])
    #     if total_sum.has_key(username):
    #         total_sum[username] -= sum

    # close this database connection
    cur.close()
    db.close()

    # sort by desc
    total_sum_list = sorted(total_sum.iteritems(), key = lambda asd:asd[1], reverse=True)

    # draw picture
    name_list = list()
    num_list = list()
    for list in total_sum_list[:10]:
        name_list.append(list[0])
        num_list.append(list[1])
    params = {
        'figure.figsize': '12, 4'
    }
    plt.rcParams.update(params)
    autolabel(plt.bar(range(len(num_list)), num_list, color='rgb', tick_label=name_list))
    plt.show()

