
from utils import base
from utils import sql
import yaml as yaml
from matplotlib import pyplot as plt
import logging
from scipy import stats
import pandas as pd
import seaborn as sns
import numpy as np

# load logger
base.setup_logging(base.logging_path, logging.DEBUG)

one_day = 86400
two_day = 172800
one_week = one_day*7
two_week = one_week*2
two_month = 5184000
one_month = 2592000
three_month = 7776000
four_month = three_month + one_month
five_month = four_month + one_month
six_month = five_month + one_month
one_year = 31104000
two_year = 62208000
three_year = one_year + two_year
global_end_time = "2020-11-12 00:00:00"

f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)

def analyze_nums_change(sql, username, start_time, mid_time, end_time):
    first_time = start_time
    last_time = end_time
    # logging.info("first_time: " + first_time + ", mid_time: " + mid_time + ", last_time: " + last_time)

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # get commit sum between first_time and mid_time
    sql1 = sql % (username, first_time, mid_time)
    cur.execute(sql1)
    items = cur.fetchall()
    sum1 = items[0][0]

    # get commit sum between mid_time and last_time
    sql2 = sql % (username, mid_time, last_time)
    cur.execute(sql2)
    items = cur.fetchall()
    sum2 = items[0][0]

    # close this database connection
    cur.close()
    db.close()

    # logging.info("sum1: " + str(sum1) + ", sum2: " + str(sum2))

    return [sum1, sum2]

def get_activity_changes(month, activity_sql, accepted_time, sponsored_times):
    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    # get all user maintainer time by sponsored_times
    # cur.execute(sql.get_users_having_maintainer)
    # items = cur.fetchall()
    # login_maintainer_time = []
    # for item in items:
    #     cur.execute(sql.get_user_maintainer_count % item[0])
    #     count = cur.fetchone()
    #     if count[0] < sponsored_times:
    #         continue
    #     cur.execute(sql.get_user_maintainer_created_time_by_times % (item[0], sponsored_times-1, 1))
    #     created_time = cur.fetchone()
    #     login_maintainer_time.append([item[0], created_time[1]])
    cur.execute(sql.all_user_earliest_maintainer_time % sponsored_times)
    login_maintainer_time = cur.fetchall()

    # generate time interval
    users_time_interval = []
    for item in login_maintainer_time:
        start_time = base.timestamp_to_time(base.datetime_to_timestamp(item[1]) - month)
        end_time = base.timestamp_to_time(base.datetime_to_timestamp(item[1]) + month)

        # data clean, delete the data that end_time is greater than global_end_time
        if base.time_string_to_timestamp(end_time) > base.time_string_to_timestamp(global_end_time):
            continue

        # data clean, delete the user that time between created_time and sponsored_time is not satisfied one year
        sql1 = sql.get_user_created_time % (item[0])
        cur.execute(sql1)
        created_time = cur.fetchone()
        if base.datetime_to_timestamp(item[1]) - base.datetime_to_timestamp(created_time[0]) < accepted_time:
            continue

        # data clean, delete the user that sponsor times between mid_time and end_time is
        # not exceeded and equaled sponsored_times
        sql2 = sql.get_sponsor_times_between_midtime_endtime % (item[0], end_time)
        cur.execute(sql2)
        sponsor_count = cur.fetchone()
        if sponsor_count[0] < sponsored_times:
            continue

        users_time_interval.append([item[0], start_time,
                                    base.timestamp_to_time(base.datetime_to_timestamp(item[1])),
                                    end_time])

    # generate activity change
    users_activity_change = []
    for item in users_time_interval:
        activity_change = analyze_nums_change(activity_sql, item[0], item[1],
                                              item[2], item[3])
        if activity_change[0] is None:
            activity_change[0] = 0
        if activity_change[1] is None:
            activity_change[1] = 0
        users_activity_change.append([item[0], activity_change[0], activity_change[1]])
        # logging.info("item[0]: " + item[0] + ", activity_change[0]: " +
        #              str(int(activity_change[0])) + ", activity_change[1]: " +
        #              str(int(activity_change[1])))

    # close this database connection
    cur.close()
    db.close()

    return users_activity_change

# IQR data clean
def data_clean_IQR(datas):
    while True:
        flag = False
        for items in datas[:1]:
            percentile = np.percentile(items, [0, 25, 50, 75, 100])
            iqr = percentile[3] - percentile[1]
            up_limit = percentile[3] + iqr * 1.5
            down_limit = percentile[1] - iqr * 1.5
            length = len(items)
            i = 0
            while i < length:
                if items[i] > up_limit or items[i] < down_limit or items[i] == 0:
                    j = 0
                    while j < len(datas):
                        del datas[j][i]
                        j += 1
                        flag = True
                    length -= 1
                    continue
                i += 1
        if flag is False:
            break

def analyze_user_commit_activity(month, accepted_time, sponsor_times):
    users_activity_change = get_activity_changes(month, sql.user_commit_sql, accepted_time, sponsor_times)
    first_half_data = []
    second_half_data = []
    all_data = []
    diff_values = []
    positive_sum = 0
    negtive_sum = 0
    for item in users_activity_change:
        if int(item[2]) - int(item[1]) > 0:
            positive_sum += 1
        else:
            negtive_sum += 1
            # continue
        first_half_data.append(int(item[1]))
        second_half_data.append(int(item[2]))
        # logging.info("username: " + item[0] + ", sum1: " + str(item[1]) +
        #              ", sum2: " + str(item[2]))
        all_data.append(int(item[2]) + int(item[1]))
        diff_values.append(int(item[2]) - int(item[1]))

    logging.info("data sum: " + str(len(users_activity_change)))
    logging.info("positive_sum: " + str(positive_sum) + ", negtive_sum: " + str(negtive_sum))

    # IQR, data clean
    datas = [all_data, first_half_data, second_half_data]
    data_clean_IQR(datas)

    logging.info("real data sum: " + str(len(datas[0])))

    # x = range(1, len(datas[0])+1, 1)
    # plt.figure(1, figsize=(20, 8), dpi=80)
    # plt.subplot(2, 3, 1)
    # plt.scatter(x, datas[0], s=10)
    # plt.subplot(2, 3, 2)
    # plt.scatter(x, datas[1], s=10)
    # plt.subplot(2, 3, 3)
    # plt.scatter(x, datas[2], s=10)
    # plt.subplot(2, 3, 4)
    # sns.boxplot(y=datas[0])
    # plt.subplot(2, 3, 5)
    # sns.boxplot(y=datas[1])
    # plt.subplot(2, 3, 6)
    # sns.boxplot(y=datas[2])
    # plt.show()
    #
    # # pandas.describe
    # s = pd.Series(datas[0])
    # logging.info(s.describe())
    # s = pd.Series(datas[1])
    # logging.info(s.describe())
    # s = pd.Series(datas[2])
    # logging.info(s.describe())
    #
    # logging.info("datas[0]: " + str(len(datas[0])))
    # logging.info("datas[1]: " + str(len(datas[1])))
    # logging.info("datas[1]: " + str(len(datas[2])))

    # Wilcoxon
    logging.info(stats.wilcoxon(datas[1], datas[2]))
    _, p = stats.wilcoxon(datas[1], datas[2])
    logging.info(stats.mannwhitneyu(datas[1], datas[2]))

    # Sponsor The ratio of the number of commits
    # after sponsorship to before sponsorship
    return float(sum(datas[2])) / float(sum(datas[1]))

def analyze_user_commit_activity_by_four_bit_picture(month, accepted_time, sponsor_times):
    users_activity_change = get_activity_changes(month, sql.user_commit_sql, accepted_time, sponsor_times)
    first_half_data = []
    second_half_data = []
    all_data = []
    diff_values = []
    positive_sum = 0
    negtive_sum = 0
    for item in users_activity_change:
        if int(item[2]) - int(item[1]) > 0:
            positive_sum += 1
        else:
            negtive_sum += 1
            # continue
        first_half_data.append(int(item[1]))
        second_half_data.append(int(item[2]))
        # logging.info("username: " + item[0] + ", sum1: " + str(item[1]) +
        #              ", sum2: " + str(item[2]))
        all_data.append(int(item[2]) + int(item[1]))
        diff_values.append(int(item[2]) - int(item[1]))

    logging.info("data sum: " + str(len(users_activity_change)))
    logging.info("positive_sum: " + str(positive_sum) + ", negtive_sum: " + str(negtive_sum))

    # IQR, data clean
    datas = [all_data, first_half_data, second_half_data]
    data_clean_IQR(datas)

    # data clean
    s = pd.Series(datas[0])
    logging.info(s.describe())
    # clean small than 75% data
    percent75 = s.describe().get("75%")
    length = len(datas[0])
    i = 0
    while i < length:
        if datas[0][i]<percent75:
            j = 0
            while j < len(datas):
                del datas[j][i]
                j += 1
            length -= 1
            continue
        i += 1

    # Wilcoxon
    logging.info(stats.wilcoxon(datas[1], datas[2]))
    _, p = stats.wilcoxon(datas[1], datas[2])
    logging.info(stats.mannwhitneyu(datas[1], datas[2]))

    # Sponsor The ratio of the number of commits
    # after sponsorship to before sponsorship
    return float(sum(datas[2])) / float(sum(datas[1]))

def analyze_user_issue_comment_activity(month, accepted_time, sponsor_times):
    users_activity_change = get_activity_changes(month, sql.user_issue_comment_sql, accepted_time, sponsor_times)
    first_half_data = []
    second_half_data = []
    all_data = []
    diff_values = []
    positive_sum = 0
    negtive_sum = 0
    for item in users_activity_change:
        if int(item[2]) - int(item[1]) > 0:
            positive_sum += 1
        else:
            negtive_sum += 1
            # continue
        first_half_data.append(int(item[1]))
        second_half_data.append(int(item[2]))
        # logging.info("username: " + item[0] + ", sum1: " + str(item[1]) +
        #              ", sum2: " + str(item[2]))
        all_data.append(int(item[2]) + int(item[1]))
        diff_values.append(int(item[2]) - int(item[1]))

    logging.info("data sum: " + str(len(users_activity_change)))
    logging.info("positive_sum: " + str(positive_sum) + ", negtive_sum: " + str(negtive_sum))

    # IQR, data clean
    datas = [all_data, first_half_data, second_half_data]
    data_clean_IQR(datas)

    # x = range(1, len(datas[0])+1, 1)
    # plt.figure(1, figsize=(20, 8), dpi=80)
    # plt.subplot(2, 3, 1)
    # plt.scatter(x, datas[0], s=10)
    # plt.subplot(2, 3, 2)
    # plt.scatter(x, datas[1], s=10)
    # plt.subplot(2, 3, 3)
    # plt.scatter(x, datas[2], s=10)
    # plt.subplot(2, 3, 4)
    # sns.boxplot(y=datas[0])
    # plt.subplot(2, 3, 5)
    # sns.boxplot(y=datas[1])
    # plt.subplot(2, 3, 6)
    # sns.boxplot(y=datas[2])
    # plt.show()
    #
    # # pandas.describe
    # s = pd.Series(datas[0])
    # logging.info(s.describe())
    # s = pd.Series(datas[1])
    # logging.info(s.describe())
    # s = pd.Series(datas[2])
    # logging.info(s.describe())
    #
    # logging.info("datas[0]: " + str(len(datas[0])))
    # logging.info("datas[1]: " + str(len(datas[1])))
    # logging.info("datas[1]: " + str(len(datas[2])))

    # Wilcoxon
    logging.info(stats.wilcoxon(datas[0], datas[1]))
    _, p = stats.wilcoxon(datas[0], datas[1])
    logging.info(stats.mannwhitneyu(datas[0], datas[1]))

    # Sponsor The ratio of the number of commits
    # after sponsorship to before sponsorship
    return float(sum(datas[2])) / float(sum(datas[1]))

def cal_quantile():
    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()

    cur.execute(sql.get_all_spon_maintainer_count)
    items = cur.fetchall()
    spon_maintainer_count_list = []
    for item in items:
        spon_maintainer_count_list.append(item[0])

    percent = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80,
               85, 90, 95, 100]
    percentile = np.percentile(spon_maintainer_count_list, percent)

    # close this database connection
    cur.close()
    db.close()

    logging.info(percentile)

# analyze commit changes with sponsor times
def analyze_commit_changes_with_sponsor_times(login, sponsor_count):
    sql_for_created_at = """
        SELECT created_at
        FROM github_sponsorships_as_maintainer
        WHERE login='%s'
        ORDER BY created_at ASC
    """
    sql_for_created_at = sql_for_created_at % login

    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()
    cur.execute(sql_for_created_at)
    items = cur.fetchall()
    created_at_list = []
    for item in items:
        created_at_list.append(base.timestamp_to_time(base.datetime_to_timestamp((item[0]))))

    sponsor_counts = []
    commit_counts = []
    commit_count = 0
    i = 0
    while i < len(created_at_list):
        first_time = created_at_list[i]
        i += sponsor_count
        if i >= len(created_at_list):
            break
        second_time = created_at_list[i]
        cur.execute(sql.user_commit_sql % (login, first_time, second_time))
        item = cur.fetchone()
        if item[0] is None:
            commit_count += 0
        else:
            commit_count += item[0]
        sponsor_counts.append(second_time)
        commit_counts.append(commit_count)

    return sponsor_counts, commit_counts

    # logging.info("the first sponsor time: " + str(created_at_list[0]))
    # logging.info("the last sponsor time: " + str(created_at_list[len(created_at_list)-1]))
    # logging.info("length: " + str(len(sponsor_counts)))
    # plt.figure(1, figsize=(20, 8), dpi=80)
    # plt.subplot(1, 2, 1)
    # plt.xlabel("sponsor times")
    # plt.ylabel("commit times")
    # plt.plot(sponsor_counts, commit_counts)

    # # get commit picture before sponsor ago
    # time2 = created_at_list[0]
    # time3 = created_at_list[len(created_at_list)-1]
    # time1 = base.timestamp_to_time(2*base.time_string_to_timestamp(time2) - base.time_string_to_timestamp(time3))
    # arg1, arg2 = generate_commit_line_chart(login, time1, time2)
    # plt.subplot(1, 2, 2)
    # plt.xlabel("time")
    # plt.ylabel("commit times")
    # plt.plot(arg1, arg2)
    # plt.show()
    #
    # # close this database connection
    # cur.close()
    # db.close()

def generate_commit_line_chart(login, start_time, end_time):
    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()
    first_time = base.time_string_to_timestamp(start_time)
    time_interval = 172800
    second_time = first_time+time_interval
    end_time = base.time_string_to_timestamp(end_time)
    x_s = []
    commit_counts = []
    commit_count = 0
    while second_time <= end_time:
        x_s.append(base.timestamp_to_time(second_time))
        cur.execute(sql.user_commit_sql % (login, base.timestamp_to_time(first_time), base.timestamp_to_time(second_time)))
        item = cur.fetchone()
        if item[0] is None:
            commit_count += 0
        else:
            commit_count += item[0]
        commit_counts.append(commit_count)
        first_time = second_time
        second_time += time_interval

    # close this database connection
    cur.close()
    db.close()
    return x_s,

# generate the activity changes picture of one user, include line chart and scatter diagram
def generate_picture1(login):
    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()
    sql_for_min_max_time = """
            SELECT MIN(created_at), MAX(created_at)
            FROM github_sponsorships_as_maintainer
            WHERE login='%s'
        """
    cur.execute(sql_for_min_max_time % login)
    item = cur.fetchall()
    mid_time = base.datetime_to_timestamp(item[0][0])
    max_time = base.datetime_to_timestamp(item[0][1])
    min_time = 2*mid_time - max_time
    first_time = min_time
    second_time = first_time + two_day
    x_s = []
    commit_counts = []
    commit_count = 0
    while second_time <= max_time:
        x_s.append(second_time)
        cur.execute(
            sql.user_commit_sql % (login, base.timestamp_to_time(first_time), base.timestamp_to_time(second_time)))
        item = cur.fetchone()
        if item[0] is None:
            commit_count += 0
        else:
            commit_count += item[0]
        commit_counts.append(commit_count)
        first_time = second_time
        second_time += two_day

    logging.info(str(base.timestamp_to_time(min_time)))
    logging.info(str(base.timestamp_to_time(mid_time)))
    logging.info(str(base.timestamp_to_time(max_time)))

    plt.figure(1, figsize=(20, 8), dpi=80)
    # plt.subplot(1, 2, 1)
    plt.xlabel("time")
    plt.ylabel("commit times")
    plt.plot(x_s, commit_counts)

    cur.execute(
        sql.user_commit_sql % (login, base.timestamp_to_time(min_time), base.timestamp_to_time(mid_time)))
    item = cur.fetchone()
    data1, data2 = analyze_commit_changes_with_sponsor_times(login, 1)
    j = 0
    while j<len(data2):
        data2[j] += item[0]
        data1[j] = base.time_string_to_timestamp(data1[j])
        j += 1
    plt.scatter(data1, data2, s=15, c='red')
    plt.show()

    # close this database connection
    cur.close()
    db.close()
    # return x_s, commit_counts

def classify_user_by_commit_sum():
    time_interval = one_month
    sql_for_all_sponsorlisting_created_at =  """
                            SELECT login, created_at
                            FROM github_sponsor_listing
                            WHERE login in (SELECT login FROM github_user WHERE spon_maintainer_count > 0)
                            """
    # create database connection
    db = base.connectMysqlDB(config)
    cur = db.cursor()
    # classify user by commit sum
    cur.execute(sql_for_all_sponsorlisting_created_at)
    items = cur.fetchall()
    login_and_commit_list = []
    commit_list = []
    for item in items:
        end_time = base.timestamp_to_time(base.datetime_to_timestamp(item[1]))
        start_time = base.timestamp_to_time(base.datetime_to_timestamp(item[1])-time_interval)
        cur.execute(sql.user_commit_sql % (item[0], start_time, end_time))
        sub_item = cur.fetchone()
        commit_sum = int(sub_item[0])
        login_and_commit_list.append([item[0], commit_sum])
        commit_list.append(commit_sum)

    percentile = np.percentile(commit_list, [33, 67])
    percent33 = percentile[0]
    percent67 = percentile[1]
    logging.info("33% num of commit sum is: " + str(percent33))
    logging.info("67% num of commit sum is: " + str(percent67))
    login_percent33_list = []
    login_percent67_list = []
    login_percent100_list = []
    for login_and_commit in login_and_commit_list:
        if login_and_commit[1] <= percent33:
            login_percent33_list.append(login_and_commit[0])
        elif login_and_commit[1] <= percent67:
            login_percent67_list.append(login_and_commit[0])
        else:
            login_percent100_list.append(login_and_commit[0])
    login_percent_lists = [login_percent33_list, login_percent67_list, login_percent100_list]

    # wilcoxon analysis
    sql_for_sponsorlisting_created_at = """
                                SELECT created_at
                                FROM github_sponsor_listing
                                WHERE login='%s'
                                """
    time_interval_for_wilcoxon = one_month
    for login_percent_list in login_percent_lists:
        activity_change_list = []
        for login in login_percent_list:
            cur.execute(sql_for_sponsorlisting_created_at % login)
            sub_item = cur.fetchone()
            mid_time = base.datetime_to_timestamp(sub_item[0])
            start_time = mid_time - time_interval_for_wilcoxon
            end_time = mid_time + time_interval_for_wilcoxon
            # data clean, delete the data that end_time is greater than global_end_time
            if end_time > base.time_string_to_timestamp(global_end_time):
                continue

            # data clean, delete the user that time between created_time and sponsored_time is not satisfied one year
            cur.execute(sql.get_user_created_time % login)
            created_time = cur.fetchone()
            if mid_time - base.datetime_to_timestamp(created_time[0]) < one_year:
                continue

            activity_change = analyze_nums_change(sql.user_commit_sql, login, base.timestamp_to_time(start_time),
                                                  base.timestamp_to_time(mid_time),
                                                  base.timestamp_to_time(end_time))
            if activity_change[0] is None:
                activity_change[0] = 0
            if activity_change[1] is None:
                activity_change[1] = 0
            activity_change_list.append([int(activity_change[0])+int(activity_change[1]), int(activity_change[0]), int(activity_change[1])])
        datas = [[], [], []]
        for activity_change in activity_change_list:
            datas[0].append(activity_change[0])
            datas[1].append(activity_change[1])
            datas[2].append(activity_change[2])
        logging.info("data sum: " + str(len(datas[0])))
        # IQR, data clean
        data_clean_IQR(datas)
        logging.info("real data sum: " + str(len(datas[0])))
        s = pd.Series(datas[1])
        logging.info(s.describe())
        s = pd.Series(datas[2])
        logging.info(s.describe())
        logging.info(stats.wilcoxon(datas[1], datas[2]))
        logging.info(stats.mannwhitneyu(datas[1], datas[2]))
    # close this database connection
    cur.close()
    db.close()
    # return login_percent33_list, login_percent67_list, login_percent100_list

if __name__ == "__main__":
    # analyze_nums_change("calebporzio", sql.user_issue_comment_sql, "user issue comment")
    # logging.info("qiubing")
    # analyze_user_commit_activity(three_month, one_year, 64)
    # analyze_user_issue_comment_activity(two_month, one_year, 1)

    # # statistics the radio of sponsor changes
    # count = 64
    # i = 1
    # compare_value_list = []
    # step_size = 1
    # x = range(1, count + 1, step_size)
    # while i <= count:
    #     logging.info(str(i))
    #     compare_value = analyze_user_commit_activity(two_week, one_year, i)
    #     # compare_value = analyze_user_issue_comment_activity(three_month, one_year, i)
    #     # compare_value = analyze_user_commit_activity_by_four_bit_picture(three_month, one_year, i)
    #     compare_value_list.append(compare_value)
    #     i += step_size
    # logging.info(compare_value_list)
    # plt.figure(1, figsize=(20, 8), dpi=80)
    # plt.xlabel("sponsor times")
    # plt.ylabel("commit ratio")
    # plt.plot(x, compare_value_list)
    # plt.show()

    # analyze_commit_changes_with_sponsor_times("rstoenescu", 1)
    # generate_commit_line_chart("rstoenescu", "2019-06-18 15:06:12", "2020-11-15 05:44:26")
    # generate_picture1("rstoenescu")

    classify_user_by_commit_sum()