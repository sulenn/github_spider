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
                }
            }
        """

query_github_user_sponsor_listing_info = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    sponsorsListing {
                        createdAt
                        fullDescription
                        name
                        shortDescription
                        slug
                        tiers {
                            totalCount
                        }
                    }
                }      
            }
        """

query_github_user_sponsor_listing_tiers_info = """
            query {
                user(login:"%s") {
                    login
                    databaseId
                    sponsorsListing {
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