class BOOL_VALUES:
    YES = 'yes'
    NO = 'no'
    AVAILABLE = '+'
    NOT_AVAILABLE = '-'


class SOURCES:
    ICODROPS = 'icodrops'
    ICOBAZAAR = 'icobazaar'
    ICOBENCH = 'icobench'
    TRACKICO = 'trackico'
    TOKENTOPS = 'topentops'
    ICOMARKS = 'icomarks'
    ICORATING = 'icoratings'


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

    SOURCE = 'source'
    NAME = 'name'
    TOKEN_NAME = 'ticker'
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
    PRE_ICO_PRICE = 'pre_ico_token_price'
    ICO_PRICE = 'ico_token_price'
    KYC = 'kyc'
    WHITELIST = 'whitelist'

    # social pages
    GITHUB_URL = 'github_page'
    MEDIUM_URL = 'medium_page'
    LINKEDIN_URL = 'linkedin_page'
    TWITTER_URL = 'twitter_page'
    INSTAGRAM_URL = 'instagram_url'
    FACEBOOK_URL = 'facebook_page'
    WEBSITE = 'webpage'
    LOGO_URL = 'logo_url'
    SLACK_URL = 'slack_url'
    YOUTUBE_URL = 'youtube_url'

    # telefram
    TELEGRAM_URL = 'telegram_page'
    TELEGRAM_SUBSCRIBERS = 'teleg_subs_count'

    # bitcointalk
    BITCOINTALK_URL = 'btc_page'
    BITCOINTALK_AVERAGE_ACTIVITY = 'btc_avg_activ'
    BITCOINTALK_TOTAL_COMMENTS = 'btc_num_comments'

    # reddit
    REDDIT_URL = 'reddit_page'
    REDDIT_COMMENTS_COUNT = 'rdt_comment_count'
    REDDIT_POSTS_COUNT = 'rdt_post_count'
    REDDIT_AVG_KARMA = 'rdt_usr_avg_karma'

    # scores
    OVERALL_SCORES = 'website_overall_rating'

    # icodrops
    ROI_SCORE = 'roi_score'

    HYPE_SCORE = 'hype_score'
    RISK_SCORE = 'risk_score'
    USER_SCORE = 'users_rating'

    # icobench ratings
    ICO_PROFILE_SCORE = 'ico_profile_score'
    VISION_SCORE = 'vision_score'
    TEAM_SCORE = 'team_score'
    PRODUCT_SCORE = 'product_score'
