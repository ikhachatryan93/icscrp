import logging
import pycountry
from datetime import datetime
import re
from typing import Union

from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import ICO_STATUS
from utilities.country_keys import iso_name_from_unofficial

logger = logging
date_format = '%d-%m-%Y'


def process_time_period_status(sdate, edate, n_a):
    try:
        start_date = datetime.strptime(sdate, date_format)
        end_date = datetime.strptime(edate, date_format)
    except ValueError:
        logger.CRITICAL('Bad date format, while parsing date : {} - {}'.format(sdate, edate))
        return n_a

    if start_date <= datetime.today() <= end_date:
        return ICO_STATUS.ACTIVE
    elif datetime.today() < start_date:
        return ICO_STATUS.UPCOMING
    elif datetime.today() > end_date:
        return ICO_STATUS.ENDED

    return n_a


def process_date_type_without_year(date, n_a):
    """
    Converts a date string from  '02 August 1993' to '27-12-2015'

    Args:
    :param date: date in %d %m
    :param n_a: not available sign

    Returns:
    :return: %d-%m-%y formatted date, default if conversion failed.
    """
    date = date.strip()

    input_formats = ['%d %b']
    fdate = n_a
    for in_fmt in input_formats:
        try:
            fdate = datetime.strptime(date, in_fmt).strftime('%d-%m')
        except ValueError:
            pass

    # debugging
    if fdate == n_a and re.match('.*\d.*', date):
        logging.warning('Could not convert date format: {}'.format(date))

    return fdate


def process_date_type(date, n_a):
    """
    Converts a date string from '02.08.1993', 'Dec. 27, 2015' or 'December 27, 2015', '02 August 1993' to '27-12-2015'

    Args:
    :param date: date in  %d.%m.%y or %d %B %Y or %B %d, %Y or %b. %d, %Y format
    :param n_a: not available sign

    Returns:
    :return: %d-%m-%y formatted date, default if conversion failed.
    """

    date = date.strip()

    # special cases
    date = date.replace('Sept', 'Sep')
    date = date.replace('Sepember', 'September')

    input_formats = ['%B %d, %Y', '%b. %d, %Y', '%d %B %Y', '%d.%m.%Y', '%d %b %Y', '%Y-%m-%d', date_format]
    fdate = n_a
    for in_fmt in input_formats:
        try:
            fdate = datetime.strptime(date, in_fmt).strftime(date_format)
        except ValueError:
            pass

    # debugging
    if fdate == n_a and re.match('.*\d.*', date):
        logging.warning('Could not convert date format: {}'.format(date))

    return fdate


def process_country_names(data, country_keys, keep_unconverted=True, default_value=None, words_unspecified=None):
    """
    Format the country names to alfa_3 format of ISO 3166 standard

    Args:
    :param data: list of dict data
    :param keep_unconverted: keep long string country name if conversion failed
    :param country_keys: list of keys in data referring to country fields
    :param default_value: default_value will be used in case of conversion fail if keep_unconverted is false, and in case of n/a words
    :param words_unspecified: list of the words identifying that country field is not valid (e.g unspecified, unknown, etc)

    Returns:
    :return: data with alfa_3 formatted counties
    """

    special_cases = iso_name_from_unofficial

    for w in words_unspecified:
        special_cases[w] = default_value

    special_cases[default_value] = default_value

    for country_key in country_keys:
        for d in data:
            alpha_3_names = ''
            countries = d[country_key]
            for cntr in countries.split(','):
                if alpha_3_names:
                    alpha_3_names += ', '

                country = cntr.strip()
                if country in special_cases:
                    alpha_3_names += special_cases[country]
                    continue

                if country != BOOL_VALUES.NOT_AVAILABLE:
                    if len(country) == 3:
                        alpha_3_names += country
                        continue

                    # not in iso standard
                    if country == 'UK':
                        country = 'United Kingdom'

                    try:
                        alpha_3_names += pycountry.countries.get(name=country).alpha_3
                    except KeyError:
                        try:
                            alpha_3_names += pycountry.countries.get(official_name=country).alpha_3
                        except KeyError:
                            try:
                                alpha_3_names += pycountry.countries.get(alpha_2=country).alpha_3
                            except KeyError:
                                if not keep_unconverted:
                                    alpha_3_names += default_value
                                logging.error('Could not find alfa_3 format for country name: {}'.format(country))
                                continue

            d[country_key] = alpha_3_names

    return data


def __data_len(dct, n_a):
    """ Get number of true* data in dict """
    i = 0
    for _, val in dct.items():
        if val != n_a:
            i += 1

    return i


def __is_valid(d, n_a):
    """ TODO: make more parametric """
    return __data_len(d, n_a) >= 5


def __pop_similar_subdata(d1, data, eq_keys):
    idxs = []
    for idx, d2 in enumerate(data):
        eq = True
        for eq_key in eq_keys:
            if d1[eq_key] != d2[eq_key]:
                eq = False
                break
        if eq:
            idxs.append(idx)

    sub_eq_data = []
    for idx in idxs:
        sub_eq_data.append(data.pop(idx))

    return sub_eq_data if len(sub_eq_data) > 0 else None


def __merge(d, sub_data, priority_key, priority_table, n_a):
    for d2 in sub_data:
        for key, value in d.items():
            value2 = d2[key]
            if value != value2:
                if value == n_a:
                    d[key] = value2
                elif value2 != n_a:
                    if priority_table[d2[priority_key]] < priority_table[d[priority_key]]:
                        d[key] = value


def __is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def convert_scale(score: str,
                  current_A: Union[int, float],
                  current_B: Union[int, float],
                  desired_A: Union[int, float],
                  desired_B: Union[int, float],
                  decimal: bool,
                  default: str) -> str:
    """
    Normalizing Ranges of Numbers,  y = desired_A + (score-current_A)*(desired_B-desired_A)/(current_B-current_A)

    Example: 4.5 (scale of 0-5) is 9 (scale of 0-10)

    Note: see the original article http://mathforum.org/library/drmath/view/60433.html

    Args:
    :param score: the score to be converted
    :param current_A: current scale start number
    :param current_B: current scale end number
    :param desired_A: desired scale start number
    :param desired_B: desired scale end number
    :param decimal: flag which decides whether decimal(float) or integer(int) value will be returned.
                    The output score will be rounded to nearest whole number if decimal is false.
    :param default: return this value if conversion failed

    Returns:
    :return integer or decimal score in scale of desired_A - desired_B
    """

    if not __is_number(score):
        return default

    y = desired_A + (float(score) - current_A) * (desired_B - desired_A) / (current_B - current_A)

    if not decimal:
        return format(y, '.0f')

    return format(y, '.1f')


def merge_conflicts(data: list, eq_keys: list, priority_key: str, priority_table: dict, n_a: str) -> []:
    """
    Merge data from different sources. Priority table should be specified, since in case of conflicts the privilege will
    be given to the element with higher priority

    Args:
    :param data: list of dict
    :param eq_keys: list of str, the keys from dict which identify the equality of data buckets(dicts)
    :param priority_key: name of the priority field (e.g. DataDypes.WEBSITE)
    :param priority_table: dict priority table identifying which data should be kept if merge conflict occurred
                           give a value for each source, (e.g. {source3: 1, source1: 2, source3:2})
    :param n_a: the object identifier for not available fields, (e.g. None, DataKeys.NOT_AVAILABLE)

    Returns
    :return None:
    """
    good_data = [d for d in data if __is_valid(d, n_a)]

    # TODO:Sort somehow
    # sort(good_data)

    merged_data = []
    while len(good_data) > 0:
        d = good_data.pop()
        similar_subdata = __pop_similar_subdata(d, good_data, eq_keys)

        if similar_subdata:
            __merge(d, similar_subdata, priority_key, priority_table, n_a)

        merged_data.append(d)

    return merged_data
