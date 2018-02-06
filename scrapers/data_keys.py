class DataKeys:
    NOT_AVAILABLE = 'N.A'

    class BOOL_VALUES:
        YES = 'yes'
        NO = 'no'

    PLATFORM = 'platform'
    NAME = 'name'
    DESCRIPTION = 'description'
    PROFILE_URL = 'ico_url'
    STATUS = 'status'
    RAISE_GOAL = 'raise_goal'
    RAISED = 'raised'
    ICO_START = 'ico_start'
    ICO_END = 'ico_end'
    TOKEN_NAME = 'token_name'
    WEBSITE_URL = 'webpage'

    #TODO: define format
    COUNTRY = 'country'
    # should be 2 letter country ISO code
    COUNTRIES_RESTRICTED = 'countries_restricted'

    ACCEPTED_CURRENCIES = 'accepted_currencies'
    TOKEN_PRICE_BTC = 'token_price_bitcoin'
    TOKEN_PRICE_ETH = 'token_price_etherum'
    TOKEN_PRICE_LIT = 'token_price_litecoin'
    TOKEN_PRICE_USD = 'token_price_usd'
    SOFT_CAP = 'soft_cap'
    HARD_CAP = 'hard_cap'
    # yes or no

    # token price
    PRE_ICO_PRICE = 'pre_ico_price'
    ICO_PRICE = 'ico_price'
    KYC = 'kyc'
    WHITELIST = 'whitelist'

    # scores
    OVERALL_SCORES = 'website_overall_rating'


    # social pages
    GITHUB_URL = 'github_page'
    TELEGRAM_URL = 'telegram_page'
    BITCOINTALK_URL = 'bitcointalk_page'
    MEDIUM_URL = 'medium_page'
    LINEDIN_URL = 'linkedin_page'
    TWITTER_URL = 'twitter_page'
    REDDIT_URL = 'reddit_page'
