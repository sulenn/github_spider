### for compare between sponsoring prev and sponsoring tail
# for user commits per day
user_commit_sql = """
                SELECT sum(contribution_count)
                FROM github_user_commits_per_day
                WHERE login='%s' AND date>='%s' AND date<='%s'
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
