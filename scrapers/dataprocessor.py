import logging
import pycountry
from datetime import datetime

from scrapers.data_keys import BOOL_VALUES

logger = logging


def process_date_type1(date, default, n_a):
    """
    Converts a date string from '02.08.1993' to '02-08-1993'

    Args:
    :param n_a: not available sign
    :param date: %d.%m.%y formatted date
    :param default: retrun this value ins case of conversion is failed

    Returns:
    :return: %d-%m-%y formatted date, default if conversion failed.
    """
    if date in n_a:
        return default

    try:
        rdate = datetime.strptime(date, '%d.%m.%Y').strftime('%d-%m-%Y')
    except ValueError:
        logging.warning('Could not format date from {} string'.format(date))
        return default

    return rdate


def process_date_type2(date, default, n_a):
    """
    Converts a date string from 'Dec. 27, 2015' or 'December 27, 2015' to '27-12-2015'

    Args:
    :param date: %B %d, %Y or %b. %d, %Y format (e.g. March 24, 2018)
    :param default: retrun this value ins case of conversion is failed
    :param n_a: not available sign

    Returns:
    :return: %d-%m-%y formated date, default if conversion failed.
    """

    if date in n_a:
        return default

    # special cases
    date = date.replace('Sept', 'Sep')

    try:
        rdate = datetime.strptime(date, '%B %d, %Y').strftime('%d-%m-%Y')
    except ValueError:
        try:
            rdate = datetime.strptime(date, '%b. %d, %Y').strftime('%d-%m-%Y')
        except ValueError:
            logging.warning('Could not format date from {} string'.format(date))
            return default

    return rdate


def process_date_type3(date, default, n_a):
    """
    Converts a date string from '02 August 1993'

    Args:
    :param date: %d %B %Y format
    :param default: return this value ins case of conversion is failed
    :param n_a: not available sign

    Returns:
    :return: %d-%m-%y formatted date, default if conversion failed.
    """

    if date in n_a:
        return default

    try:
        rdate = datetime.strptime(date, '%d %B %Y').strftime('%d-%m-%Y')
    except ValueError:
        logging.warning('Could not format date from {} string'.format(date))
        return default

    return rdate


def process_country_names(data, country_keys, keep_unconverted=True, default_value=None, words_unspecified=()):
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
    for country_key in country_keys:
        for d in data:
            alpha_3_names = ''
            countries = d[country_key]
            for cntr in countries.split(','):
                if alpha_3_names:
                    alpha_3_names += ', '

                country = cntr.strip()
                if country in words_unspecified or country == default_value:
                    alpha_3_names += default_value
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


def merge_conflicts(data: list, eq_keys: list, priority_key: str, priority_table: dict, n_a: str) -> None:
    """
    Merge data from different sources. Priority table should be specified, since in case of conflicts the privilege will
    be given to the element with higher priority

    Args:
    :param data: list of dict,
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
        if not similar_subdata:
            merged_data.append(d)
        else:
            __merge(d, similar_subdata, priority_key, priority_table, n_a)
