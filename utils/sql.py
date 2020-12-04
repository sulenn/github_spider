### for compare between sponsoring prev and sponsoring tail
# for user commits per day
user_commit_sql = """
                SELECT sum(contribution_count)
                FROM github_user_commits_per_day
                WHERE login='%s' AND date>='%s' AND date<'%s'
                """

user_issue_sql = """
                SELECT count(*)
                FROM github_user_issue
                WHERE login='%s' AND created_at>='%s' AND created_at<='%s'
                """

user_pr_sql = """
                SELECT count(*)
                FROM github_user_pr
                WHERE login='%s' AND created_at>='%s' AND created_at<='%s'
                """

user_pr_review_sql = """
                SELECT count(*)
                FROM github_user_pr_review
                WHERE login='%s' AND created_at>='%s' AND created_at<='%s'
                """

user_repository_sql = """
                SELECT count(*)
                FROM github_repository
                WHERE login='%s' AND created_at>='%s' AND created_at<='%s'
                """

user_commit_comment_sql = """
                SELECT count(*)
                FROM github_commit_comment
                WHERE login='%s' AND created_at>='%s' AND created_at<='%s'
                """

user_issue_comment_sql = """
                SELECT count(*)
                FROM github_issue_comment
                WHERE login='%s' AND created_at>='%s' AND created_at<='%s'
                """

all_user_earliest_maintainer_time = """
                SELECT login, min(created_at) AS created_at
                FROM github_sponsorships_as_maintainer
                GROUP BY login
                HAVING COUNT(*) >= %s
                """

get_user_created_time = """
                SELECT created_at
                FROM github_user
                WHERE login='%s'
                """

get_sponsor_times_between_midtime_endtime = """
                SELECT COUNT(*)
                FROM github_sponsorships_as_maintainer
                WHERE login='%s' AND created_at<='%s'
                """

get_users_having_maintainer = """
                SELECT DISTINCT login
                FROM github_sponsorships_as_maintainer
                """

get_user_maintainer_count = """
                SELECT count(*)
                FROM github_sponsorships_as_maintainer
                WHERE login='%s'
                """

get_user_maintainer_created_time_by_times = """
                SELECT login, created_at
                FROM github_sponsorships_as_maintainer
                WHERE login='%s'
                ORDER BY created_at ASC
                LIMIT %s,%s
                """

get_all_spon_maintainer_count = """
                SELECT spon_maintainer_count
                FROM github_user
                WHERE spon_maintainer_count>0
                ORDER BY spon_maintainer_count DESC
                """