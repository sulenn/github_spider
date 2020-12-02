
import GraphQL, Database
from utils import paths
from utils import queries
from utils import base
import logging
import yaml

# load logger
base.setup_logging(base.logging_path, logging.DEBUG)

start_time = ["2017-09-01T00:00:00Z", "2018-09-02T00:00:00Z", "2019-09-02T00:00:00Z", "2020-09-02T00:00:00Z"]
end_time = ["2018-09-01T00:00:00Z", "2019-09-01T00:00:00Z", "2020-09-01T00:00:00Z", "2020-11-12T00:00:00Z"]

# supply github_user table data by cycling the procedure
# 1. get github_user table data from github_sponsorships_as_sponsor table
# 2. get github_sponsorships_as_sponsor table data from github_user table
# 3. get github_user table data from github_sponsorships_as_maintainer table
# 4. get github_sponsorships_as_maintainer table fata from github_user table
def cycle_supply_user_data_by_sponsorships_as_sponsor_and_maintainer():
    while True:
        flag1, flag2, flag3, flag4 =0, 0, 0, 0
        # crawl user data, save json file and write database from github_sponsorships_as_sponsor table
        sql_for_login = "select distinct login \
                            from github_sponsorships_as_sponsor \
                            WHERE flag!=1 and login NOT IN (SELECT login from github_user)"
        if not base.judge_sql_result(sql_for_login):
            logging.info("no more login to crawl and write from github_sponsorships_as_sponsor")
            flag1 = 1
        logging.info("crawl user data, save json file from github_sponsorships_as_sponsor")
        GraphQL.crawlUser(paths.github_user_info, queries.query_github_user_info, sql_for_login)
        logging.info("write user database from github_sponsorships_as_sponsor")
        Database.writeGithubUser(paths.github_user_info, sql_for_login)

        # crawl user sponsorships as sponsor data, save json file and write database from github_user table
        sql_for_sponsorships_as_sponsor = "select distinct login \
                                            from github_user \
                                            WHERE spon_sponsor_count!=0 " \
                                          "AND login NOT IN (SELECT distinct sponsor_login from github_sponsorships_as_sponsor)"
        if not base.judge_sql_result(sql_for_sponsorships_as_sponsor):
            logging.info("no more user sponsorships as sponsor data to crawl and write from github_user")
            flag2 = 1
        logging.info("crawl user sponsorships as sponsor data, save json file")
        GraphQL.crawlSponsorshipsAsSponsor(paths.github_user_sponsorships_as_sponsor, queries.query_github_user_sponsorships_as_sponsor_info,
                                        sql_for_sponsorships_as_sponsor)
        logging.info("write user sponsorships as sponsor database")
        Database.writeGithubSponsorshipsAsSponsor(paths.github_user_sponsorships_as_sponsor, sql_for_sponsorships_as_sponsor)

        # crawl user data, save json file and write database from github_sponsorships_as_maintainer
        sql_for_login_from_maintainer = "select distinct sponsor_login \
                                    from github_sponsorships_as_maintainer \
                                    WHERE flag=0 and sponsor_login NOT IN (SELECT login from github_user)"
        if not base.judge_sql_result(sql_for_login_from_maintainer):
            logging.info("no more login to crawl and write from github_sponsorships_as_maintainer")
            flag3 = 1
        logging.info("crawl user data, save json file from github_sponsorships_as_maintainer")
        GraphQL.crawlUserForSponsorshipsAsMaintainer(paths.github_user_info, queries.query_github_user_info, sql_for_login_from_maintainer)
        logging.info("write user database from github_sponsorships_as_maintainer")
        Database.writeGithubUser(paths.github_user_info, sql_for_login_from_maintainer)

        # crawl user sponsorships as maintainer data, save json file and write database from github_user
        sql_for_sponsorships_as_maintainer = "select distinct login \
                                            from github_user \
                                            WHERE spon_maintainer_count!=0 " \
                                          "AND login NOT IN (SELECT distinct login from github_sponsorships_as_maintainer)"
        if not base.judge_sql_result(sql_for_sponsorships_as_maintainer):
            logging.info("no more user sponsorships as maintainer data to crawl and write from github_user")
            flag4 = 1
        logging.info("crawl user sponsorships as maintainer data, save json file")
        GraphQL.crawlSponsorshipsAsMaintainer(paths.github_user_sponsorships_as_maintainer,
                                           queries.query_github_user_sponsorships_as_maintainer_info,
                                           sql_for_sponsorships_as_maintainer)
        logging.info("write user sponsorships as sponsor database")
        Database.writeGithubSponsorshipsAsMaintainer(paths.github_user_sponsorships_as_maintainer,
                                                  sql_for_sponsorships_as_maintainer)
        if flag1 == 1 and flag2 ==1 and flag3 == 1 and flag4 == 1:
            logging.info("cycle over!!!!!!!!!!")
            break

# define some global things
# db config file
f = open('config.yaml', 'r')
config = yaml.load(f.read(), Loader=yaml.BaseLoader)

def insert_user():
    # read all the users
    f = open('users_with_sponsorList.txt', 'r')
    logins = f.read().strip().split("\n")
    # get db connection
    db = base.connectMysqlDB(config, autocommit=False)
    cur = db.cursor()

    # read data from file
    for username in logins:
        logging.info(username)
        try:
            cur.execute("insert into init_user "
                        "(login) "
                        "value ('" + username + "')")
            db.commit()
        except Exception as e:
            logging.fatal(e)
    cur.close()
    db.close()

if __name__ == "__main__":
    insert_user()
    # cycle_supply_user_data_by_sponsorships_as_sponsor_and_maintainer()

    # # handle github user info
    # sql_for_user = "select sponsor_login \
    #                 from github_sponsorships_as_maintainer \
    #                 WHERE sponsor_login NOT IN (SELECT login from github_user)"
    # GraphQL.crawlGithubUser(paths.github_user_info, queries.query_github_user_info, sql_for_user)
    # Database.writeGithubUser(paths.github_user_info)

    # # handle github user sponsor listing info
    # sql_for_sponsor_listing = "select login \
    #                             from github_user \
    #                             WHERE spon_maintainer_count>0 and login NOT IN (SELECT login from github_sponsor_listing)"
    # logging.info("handle github user sponsor listing info")
    # GraphQL.crawlCommon(paths.github_user_sponsor_listing_info, queries.query_github_user_sponsor_listing_info, sql_for_sponsor_listing)
    # Database.writeGithubSponsorListing(paths.github_user_sponsor_listing_info, sql_for_sponsor_listing)

    # # handle github user sponsor listing tiers info
    # sql_for_sponsor_listing_tiers = "select login \
    #                                 from github_user \
    #                                 WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_sponsor_listing_tiers)"
    # GraphQL.crawlCommon(paths.github_user_sponsor_listing_tiers_info, queries.query_github_user_sponsor_listing_tiers_info, sql_for_sponsor_listing_tiers)
    # Database.writeGithubSponsorListingTiers(paths.github_user_sponsor_listing_tiers_info, sql_for_sponsor_listing_tiers)

    # # handle github user sponsorships info as maintainer
    # sql_for_sponsorships_as_maintainer = "select login \
    #                                 from github_user \
    #                                 WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_sponsorships_as_maintainer)"
    # GraphQL.crawlSponsorshipsAsMaintainer(paths.github_user_sponsorships_as_maintainer, queries.query_github_user_sponsorships_as_maintainer_info,
    #                                 sql_for_sponsorships_as_maintainer)
    # Database.writeGithubSponsorshipsAsMaintainer(paths.github_user_sponsorships_as_maintainer, sql_for_sponsorships_as_maintainer)

    # # handle github user sponsorships info as sponsor
    # sql_for_sponsorships_as_sponsor = "select distinct login \
    #                                     from github_user \
    #                                     WHERE spon_sponsor_count!=0 " \
    #                                     "AND login NOT IN (SELECT distinct sponsor_login from github_sponsorships_as_sponsor)"
    # GraphQL.crawlSponsorshipsAsSponsor(paths.github_user_sponsorships_as_sponsor, queries.query_github_user_sponsorships_as_sponsor_info,
    #                                 sql_for_sponsorships_as_sponsor)
    # Database.writeGithubSponsorshipsAsSponsor(paths.github_user_sponsorships_as_sponsor, sql_for_sponsorships_as_sponsor)

    # # handle github user commit info
    # sql_for_user_commits = "select login \
    #                         from github_user \
    #                         WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_user_commits_per_day)"
    # for index in range(len(start_time)):
    #     GraphQL.crawlUserCommits(paths.github_user_commits, queries.query_github_user_commits,
    #                              sql_for_user_commits, start_time[index], end_time[index])
    #     logging.info("the data between " + start_time[index] + " and " + end_time[index] + " is finished\n\n")
    # Database.writeUserCommits(paths.github_user_commits, sql_for_user_commits)

    # # handle github user issue info
    # sql_for_user_issues = "select login \
    #                         from github_user \
    #                         WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_user_issue)"
    # for index in range(len(start_time)):
    #     GraphQL.crawlUserIssues(paths.github_user_issues, queries.query_github_user_issues,
    #                              sql_for_user_issues, start_time[index], end_time[index])
    #     logging.info("the data between " + start_time[index] + " and " + end_time[index] + " is finished")
    # Database.writeUserIssues(paths.github_user_issues, sql_for_user_issues)

    # # handle github user pull request
    # sql_for_user_pull_request = "select login \
    #                                     from github_user \
    #                                     WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_user_pr)"
    # for index in range(len(start_time)):
    #     GraphQL.crawlUserPullRequests(paths.github_user_pull_requests, queries.query_github_user_pull_requests,
    #                              sql_for_user_pull_request, start_time[index], end_time[index])
    #     logging.info("the data between " + start_time[index] + " and " + end_time[index] + " is finished")
    # Database.writeUserPullRequests(paths.github_user_pull_requests, sql_for_user_pull_request)

    # # handle github user pull request review
    # sql_for_user_pull_request_review = "select login \
    #                                     from github_user \
    #                                     WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_user_pr_review)"
    # for index in range(len(start_time)):
    #     GraphQL.crawlUserPullRequestReview(paths.github_user_pull_request_review, queries.query_github_user_pull_request_review,
    #                              sql_for_user_pull_request_review, start_time[index], end_time[index])
    #     logging.info("the data between " + start_time[index] + " and " + end_time[index] + " is finished")
    # Database.writeUserPullRequestReview(paths.github_user_pull_request_review, sql_for_user_pull_request_review)

    # # handle github user repository
    # sql_for_user_repository = "select login \
    #                                     from github_user \
    #                                     WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_repository)"
    # for index in range(len(start_time)):
    #     GraphQL.crawlUserRepository(paths.github_user_repositories, queries.query_github_user_repositories,
    #                              sql_for_user_repository, start_time[index], end_time[index])
    #     logging.info("the data between " + start_time[index] + " and " + end_time[index] + " is finished")
    # Database.writeUserRepository(paths.github_user_repositories, sql_for_user_repository)

    # # handle github user commit comment
    # sql_for_user_commit_comment = "select login \
    #                                     from github_user \
    #                                     WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_commit_comment)"
    # GraphQL.crawlUserCommitComment(paths.github_user_commit_comments, queries.query_github_user_commit_comments,
    #                              sql_for_user_commit_comment)
    # Database.writeUserCommitComment(paths.github_user_commit_comments, sql_for_user_commit_comment)

    # # handle github user issue comment
    # sql_for_user_issue_comment = "select login \
    #                                     from github_user \
    #                                     WHERE spon_maintainer_count>0 and login NOT IN (SELECT DISTINCT login from github_issue_comment)"
    # # GraphQL.crawlUserIssueComment(paths.github_user_issue_comments, queries.query_github_user_issue_comments,
    # #                              sql_for_user_issue_comment)
    # Database.writeUserIssueComment(paths.github_user_issue_comments, sql_for_user_issue_comment)