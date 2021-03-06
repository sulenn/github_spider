query_github_user_info = """
            query {
                user(login:"%s") {
                    name
                    email
                    login
                    bio
                    company
                    createdAt
                    updatedAt
                    databaseId
                    hasSponsorsListing
                    isBountyHunter
                    isCampusExpert
                    isDeveloperProgramMember
                    isEmployee
                    isHireable
                    isSiteAdmin
                    location
                    projectsResourcePath
                    projectsUrl
                    url
                    websiteUrl
                    resourcePath
                    twitterUsername
                    sponsorshipsAsMaintainer(includePrivate: true) {
                        totalCount
                    }
                    sponsorshipsAsSponsor {
                        totalCount
                    }
                    sponsorsListing {
                        createdAt
                        fullDescription
                        name
                        shortDescription
                        slug
                        tiers(first:100) {
                            edges {
                                node {
                                    createdAt
                                    description
                                    monthlyPriceInCents
                                    monthlyPriceInDollars
                                    name
                                    updatedAt
                                }
                            }
                            totalCount
                        }
                    }
                }      
            }
        """

query_github_user_sponsorships_as_maintainer_info = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    sponsorshipsAsMaintainer(first:100, after:"%s", includePrivate: true) {
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                        edges {
                            cursor
                            node {
                                createdAt
                                privacyLevel
                                tier {
                                    createdAt
                                    description
                                    monthlyPriceInCents
                                    monthlyPriceInDollars
                                    name
                                    updatedAt
                                }
                                sponsorEntity {
                                    ... on User {
                                        login
                                        databaseId
                                        company
                                    }
                                    ... on Organization {
                                        login
                                        databaseId
                                        description
                                    }
                                }
                            }
                        }
                        totalCount
                    }
                }
            }
        """

query_github_user_sponsorships_as_sponsor_info = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    sponsorshipsAsSponsor(first:100, after:"%s") {
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                        edges {
                            cursor
                            node {
                                createdAt
                                privacyLevel
                                tier {
                                createdAt
                                description
                                monthlyPriceInCents
                                monthlyPriceInDollars
                                name
                                updatedAt
                                }
                                sponsorable {
                                    sponsorsListing {
                                        name
                                        slug
                                    }
                                }
                                sponsorEntity {
                                ... on User {
                                    login
                                    databaseId
                                    company
                                }
                                ... on Organization {
                                    login
                                    databaseId
                                    description
                                }
                                }
                            }
                        }
                        totalCount
                    }
                }
            }
        """

query_github_user_commits = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    contributionsCollection(from:"%s", to:"%s") {
                        contributionYears
                        doesEndInCurrentMonth
                        earliestRestrictedContributionDate
                        startedAt
                        endedAt
                        hasActivityInThePast
                        hasAnyContributions
                        hasAnyRestrictedContributions
                        latestRestrictedContributionDate
                        restrictedContributionsCount
                        isSingleDay
                        totalCommitContributions
                        totalIssueContributions
                        totalPullRequestContributions
                        totalPullRequestReviewContributions
                        totalRepositoriesWithContributedCommits
                        totalRepositoriesWithContributedIssues
                        totalRepositoriesWithContributedPullRequestReviews
                        totalRepositoriesWithContributedPullRequests
                        totalRepositoryContributions
                        contributionCalendar {
                            totalContributions
                            weeks {
                                firstDay
                                contributionDays {
                                    color
                                    contributionCount
                                    date
                                    weekday
                                }
                            }
                        }
                    }
                }
            }
        """

query_github_user_issues = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    issues(%s) {
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                        totalCount
                        edges {
                            node {
                                body
                                closed
                                updatedAt
                                locked
                                createdAt
                                closed
                                author {
                                login
                            }
                                databaseId
                                number
                                title
                                repository {
                                    createdAt
                                    databaseId
                                    name
                                    owner {
                                        login
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

query_github_user_issues_empty = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    issues(%s) {
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                        totalCount
                    }
                }
            }
        """

query_github_user_pull_requests = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    pullRequests(%s) {
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                        totalCount
                        edges {
                            node {
                                body
                                closed
                                updatedAt
                                locked
                                createdAt
                                closed
                                author {
                                    login
                                }
                                databaseId
                                number
                                title
                                repository {
                                    createdAt
                                    databaseId
                                    name
                                    owner {
                                        login
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

query_github_user_pull_requests_empty = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    pullRequests(%s) {
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                        totalCount
                    }
                }
            }
        """

query_github_user_contributionYears = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    contributionsCollection(from:"2020-01-01T00:00:00Z", to:"2021-01-01T00:00:00Z") {
                        contributionYears
                    }
                }
            }
        """

query_github_user_pull_request_review = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    contributionsCollection(from:"%s", to:"%s") {
                        contributionYears
                        doesEndInCurrentMonth
                        earliestRestrictedContributionDate
                        startedAt
                        endedAt
                        hasActivityInThePast
                        hasAnyContributions
                        hasAnyRestrictedContributions
                        latestRestrictedContributionDate
                        restrictedContributionsCount
                        isSingleDay
                        totalCommitContributions
                        totalIssueContributions
                        totalPullRequestContributions
                        totalPullRequestReviewContributions
                        totalRepositoriesWithContributedCommits
                        totalRepositoriesWithContributedIssues
                        totalRepositoriesWithContributedPullRequestReviews
                        totalRepositoriesWithContributedPullRequests
                        totalRepositoryContributions
                        pullRequestReviewContributions(first:100, after:"%s") {
                            totalCount
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                            edges {
                                node {
                                    pullRequestReview {
                                        author {
                                            login
                                        }
                                        createdAt
                                        databaseId
                                        lastEditedAt
                                        body
                                        submittedAt
                                        updatedAt
                                    }
                                    occurredAt
                                    isRestricted
                                    pullRequest {
                                        body
                                        closed
                                        updatedAt
                                        locked
                                        createdAt
                                        closed
                                        author {
                                            login
                                        }
                                        databaseId
                                        number
                                        title
                                        repository {
                                            createdAt
                                            databaseId
                                            name
                                            owner {
                                                login
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

query_github_user_repositories = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    contributionsCollection(from:"%s", to:"%s") {
                        contributionYears
                        doesEndInCurrentMonth
                        earliestRestrictedContributionDate
                        startedAt
                        endedAt
                        hasActivityInThePast
                        hasAnyContributions
                        hasAnyRestrictedContributions
                        latestRestrictedContributionDate
                        restrictedContributionsCount
                        isSingleDay
                        totalCommitContributions
                        totalIssueContributions
                        totalPullRequestContributions
                        totalPullRequestReviewContributions
                        totalRepositoriesWithContributedCommits
                        totalRepositoriesWithContributedIssues
                        totalRepositoriesWithContributedPullRequestReviews
                        totalRepositoriesWithContributedPullRequests
                        totalRepositoryContributions
                        repositoryContributions(first:100, after:"%s") {
                            totalCount
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                            edges {
                                node {
                                    occurredAt
                                    isRestricted
                                    repository {
                                            createdAt
                                            databaseId
                                            name
                                        }
                                }
                            }
                        }
                    }
                }
            }
        """

query_github_user_commit_comments = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    commitComments(%s) {
                        totalCount
                        pageInfo {
                            endCursor
                            hasPreviousPage
                            hasNextPage
                        }
                        edges {
                            cursor
                            node {
                                author {
                                    login
                                }
                                databaseId
                                body
                                createdAt
                                updatedAt
                                commit {
                                    oid
                                    message
                                    author {
                                        name
                                        email
                                        date
                                        user {
                                            login
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

query_github_user_commit_comments_empty = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    commitComments(%s) {
                        totalCount
                        pageInfo {
                            endCursor
                            hasPreviousPage
                            hasNextPage
                        }
                    }
                }
            }
        """

query_github_user_issue_comments = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    issueComments(%s) {
                        totalCount
                        pageInfo {
                            endCursor
                            hasPreviousPage
                            hasNextPage
                        }
                        edges {
                            cursor
                            node {
                                author {
                                    login
                                }
                                databaseId
                                body
                                createdAt
                                updatedAt
                                pullRequest {
									author {
                                        login
                                    }
                                }
                                issue {
                                    author {
                                        login
                                    }
                                    databaseId
                                    number
                                    title
                                    createdAt
                                    updatedAt
                                }
                            }
                        }
                    }
                }
            }
        """

query_github_user_issue_comments_empty = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    issueComments(%s) {
                        totalCount
                        pageInfo {
                            endCursor
                            hasPreviousPage
                            hasNextPage
                        }
                    }
                }
            }
        """