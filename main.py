
import GraphQL, Database
from utils import paths
from utils import queries

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
    sql_for_sponsorships_as_maintainer = "select login \
                                    from init_user \
                                    WHERE login NOT IN (SELECT DISTINCT login from github_sponsorships_as_maintainer)"
    GraphQL.crawlCommonSponsorships(paths.github_user_sponsorships_as_maintainer, queries.query_github_user_sponsorships_as_maintainer_info,
                                    sql_for_sponsorships_as_maintainer)