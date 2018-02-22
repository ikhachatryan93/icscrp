from datetime import datetime
import pycountry
import logging

from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys


class DataProcessor:
    def __init__(self, data, logger):
        self.data = data
        self.logger = logger

    @staticmethod
    def process_date_type1(date, keep_unconverted=True):
        """
        Converts a date string from '02.08.1993' to '02-08-1993'

        Args:
        :param date: %d.%m.%y formatted date
        :param keep_unconverted: whether return unconverted string or return BOOL_VALUE.NOT_AVALIABLE

        Returns:
        :return: %d-%m-%y formatted date
        """
        try:
            rdate = datetime.strptime(date, '%d.%m.%Y').strftime('%d-%m-%Y')
        except ValueError:
            logging.warning('Could not format date from {} string'.format(date))
            if keep_unconverted:
                return date
            return BOOL_VALUES.NOT_AVAILABLE

        return rdate

    @staticmethod
    def process_date_type2(date, keep_unconverted=True):
        """
        Converts a date string from 'Dec. 27, 2015' or 'December 27, 2015' to '27-12-2015'

        Args:
        :param date: %B %d, %Y or %b. %d, %Y format (e.g. March 24, 2018)
        :param keep_unconverted: whether return unconverted string or return BOOL_VALUE.NOT_AVALIABLE

        Returns:
        :return: %d-%m-%y format
        """

        try:
            rdate = datetime.strptime(date, '%B %d, %Y').strftime('%d-%m-%Y')
        except ValueError:
            try:
                rdate = datetime.strptime(date, '%b. %d, %Y').strftime('%d-%m-%Y')
            except ValueError:
                logging.warning('Could not format date from {} string'.format(date))
                if keep_unconverted:
                    return date
                return BOOL_VALUES.NOT_AVAILABLE

        return rdate

    def process_country(self, country_keys, words_unspecified=(), keep_unkowns=True):
        """
        Format the country names to alfa_3 format of ISO 3166 standard
        :type country_keys: list of keys in data refering to country fields
        :type words_unspecified: list of the specific words identifyning that country field is not valid (e.g unspecified, unknown, etc)
        :type keep_unkowns: bool value showing whether to keep unformated data or to remove
        :rtype: list: data with alfa_3 formated countires
        """
        if words_unspecified is None:
            words_unspecified = []
        for country_key in country_keys:
            for d in self.data:
                country = d[country_key]

                if country in words_unspecified:
                    d[country_key] = BOOL_VALUES.NOT_AVAILABLE
                    continue

                if country != BOOL_VALUES.NOT_AVAILABLE and len(country) != 3:
                    try:
                        alfa_3 = pycountry.countries.get(name=country)
                    except KeyError:
                        try:
                            alfa_3 = pycountry.countries.get(official_name=country)
                        except KeyError:
                            try:
                                alfa_3 = pycountry.countries.get(alfa_2=country)
                            except KeyError:
                                if not keep_unkowns:
                                    d[country_key] = BOOL_VALUES.NOT_AVAILABLE

                                self.logger.error('Could not find alfa_3 format for country name: {}'.format(country))
                                continue

                    d[country] = alfa_3

    def merge_conflicts(self, priority_key, priority_table):
        """

        :type priority_key: str name of the priority field (e.g. DataDypes.WEBSITE)
        :type priority_table: dict prority table identifying whichs data should be keept if merge conflict occured
        :
        """
