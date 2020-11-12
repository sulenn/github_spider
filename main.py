
import GraphQL, Database
from utils import paths
from utils import queries

start_time = ["2017-09-01T00:00:00Z", "2018-09-02T00:00:00Z", "2019-09-02T00:00:00Z", "2020-09-02T00:00:00Z"]
end_time = ["2018-09-01T00:00:00Z", "2019-09-01T00:00:00Z", "2020-09-01T00:00:00Z", "2020-11-12T00:00:00Z"]

if __name__ == "__main__":
    # handle github user info
    # sql_for_user = "select login \
    #                 from init_user \
    #                 WHERE login NOT IN (SELECT login from github_user)"
    # GraphQL.crawlGithubUser(paths.github_user_info, queries.query_github_user_info, sql_for_user)
    # Database.writeGithubUser(paths.github_user_info)

    # handle github user sponsor listing info
    # sql_for_sponsor_listing = "select login \
    #                             from init_user \
    #                             WHERE login NOT IN (SELECT login from github_sponsor_listing)"
    # GraphQL.crawlCommon(paths.github_user_sponsor_listing_info, queries.query_github_user_sponsor_listing_info, sql_for_sponsor_listing)
    # Database.writeGithubSponsorListing(paths.github_user_sponsor_listing_info, sql_for_sponsor_listing)

    # handle github user sponsor listing tiers info
    # sql_for_sponsor_listing_tiers = "select login \
    #                                 from init_user \
    #                                 WHERE login NOT IN (SELECT DISTINCT login from github_sponsor_listing_tiers)"
    # GraphQL.crawlCommon(paths.github_user_sponsor_listing_tiers_info, queries.query_github_user_sponsor_listing_tiers_info, sql_for_sponsor_listing_tiers)
    # Database.writeGithubSponsorListingTiers(paths.github_user_sponsor_listing_tiers_info, sql_for_sponsor_listing_tiers)

    # handle github user sponsorships info as maintainer
    # sql_for_sponsorships_as_maintainer = "select login \
    #                                 from init_user \
    #                                 WHERE login NOT IN (SELECT DISTINCT login from github_sponsorships_as_maintainer)"
    # GraphQL.crawlSponsorshipsAsMaintainer(paths.github_user_sponsorships_as_maintainer, queries.query_github_user_sponsorships_as_maintainer_info,
    #                                 sql_for_sponsorships_as_maintainer)
    # Database.writeGithubSponsorshipsAsMaintainer(paths.github_user_sponsorships_as_maintainer, sql_for_sponsorships_as_maintainer)

    # handle github user sponsorships info as sponsor
    # sql_for_sponsorships_as_sponsor = "select login \
    #                                 from init_user \
    #                                 WHERE login NOT IN (SELECT DISTINCT login from github_sponsorships_as_sponsor)"
    # GraphQL.crawlSponsorshipsAsSponsor(paths.github_user_sponsorships_as_sponsor, queries.query_github_user_sponsorships_as_sponsor_info,
    #                                 sql_for_sponsorships_as_sponsor)
    # Database.writeGithubSponsorshipsAsSponsor(paths.github_user_sponsorships_as_sponsor, sql_for_sponsorships_as_sponsor)

    # handle github user commit info
    # sql_for_user_commits = "select login \
    #                                     from init_user \
    #                                     WHERE login NOT IN (SELECT DISTINCT login from github_user_commits_per_day)"
    # for index in range(len(start_time)):
    #     GraphQL.crawlUserCommits(paths.github_user_commits, queries.query_github_user_commits,
    #                              sql_for_user_commits, start_time[index], end_time[index])
    #     print "the data between " + start_time[index] + " and " + end_time[index] + " is finished\n\n"
    # Database.writeUserCommits(paths.github_user_commits, sql_for_user_commits)

    # handle github user issue info
    # sql_for_user_issues = "select login \
    #                                     from init_user \
    #                                     WHERE login NOT IN (SELECT DISTINCT login from github_user_issue)"
    # for index in range(len(start_time)):
    #     GraphQL.crawlUserIssues(paths.github_user_issues, queries.query_github_user_issues,
    #                              sql_for_user_issues, start_time[index], end_time[index])
    #     print "the data between " + start_time[index] + " and " + end_time[index] + " is finished\n\n"
    # Database.writeUserIssues(paths.github_user_issues, sql_for_user_issues)

    # handle github user pull request
    sql_for_user_pull_request = "select login \
                                        from init_user \
                                        WHERE login NOT IN (SELECT DISTINCT login from github_user_pr)"
    for index in range(len(start_time)):
        GraphQL.crawlUserPullRequests(paths.github_user_pull_requests, queries.query_github_user_pull_requests,
                                 sql_for_user_pull_request, start_time[index], end_time[index])
        print "the data between " + start_time[index] + " and " + end_time[index] + " is finished\n\n"
    Database.writeUserPullRequests(paths.github_user_pull_requests, sql_for_user_pull_request)