class BOOL_VALUES:
    YES = 'yes'
    NO = 'no'
    AVAILABLE = '+'
    NOT_AVAILABLE = '-'


class DataKeys:
    @staticmethod
    def initialize():
        # get all members
        data = dict()
        members = [attr for attr in dir(DataKeys) if
                   not callable(getattr(DataKeys, attr)) and not attr.startswith("__")]
        for key in members:
            data[eval('DataKeys.' + key)] = BOOL_VALUES.NOT_AVAILABLE

        return data

    NAME = 'name'
    TOKEN_NAME = 'token_name'
    PROFILE_URL = 'ico_url'
    DESCRIPTION = 'description'
    TOKEN_STANDARD = 'standard'
    PLATFORM = 'platform'
    PRE_ICO_START = 'pre_ico_start'
    PRE_ICO_END = 'pre_ico_end'
    ICO_START = 'ico_start'
    ICO_END = 'ico_end'
    STATUS = 'status'
    RAISE_GOAL = 'raise_goal'
    RAISED = 'raised'
    SOFT_CAP = 'soft_cap'
    HARD_CAP = 'hard_cap'

    # TODO: define format
    COUNTRY = 'country'
    # should be 2 letter country ISO code
    COUNTRIES_RESTRICTED = 'countries_restricted'

    ACCEPTED_CURRENCIES = 'accepted_currencies'
    # TOKEN_PRICE_BTC = 'token_price_bitcoin'
    # TOKEN_PRICE_ETH = 'token_price_etherum'
    # TOKEN_PRICE_LIT = 'token_price_litecoin'
    # TOKEN_PRICE_USD = 'token_price_usd'
    # yes or no

    # token price
    PRE_ICO_PRICE = 'pre_ico_price'
    ICO_PRICE = 'ico_price'
    KYC = 'kyc'
    WHITELIST = 'whitelist'

    # social pages
    GITHUB_URL = 'github_page'
    TELEGRAM_URL = 'telegram_page'
    BITCOINTALK_URL = 'bitcointalk_page'
    MEDIUM_URL = 'medium_page'
    LINKEDIN_URL = 'linkedin_page'
    TWITTER_URL = 'twitter_page'
    INSTAGRAM_URL = 'instagram_url'
    REDDIT_URL = 'reddit_page'
    FACEBOOK_URL = 'facebook_page'
    ICOWEBSITE = 'webpage'
    LOGO_URL = 'logo_url'

    # scores
    OVERALL_SCORES = 'website_overall_rating'

    # scores and ratings
    INVESTMENT_RATING = 'investment_score'
    HYPE_SCORE = 'hype_score'
    RISK_SCORE = 'risk_score'

    # icobench ratings
    ICO_PROFILE_SCORE = 'ico_profile_score'
    VISION_SCORE = 'vision_score'
    TEAM_SCORE = 'team_score'
    PRODUCT_SCORE = 'product_score'
