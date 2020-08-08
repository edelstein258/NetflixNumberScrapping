"""
Netflix Phone Number Scraper
Takes phone number input from txt files, tests them, and puts unused phone numbers into text file.
"""

import collections
import os
import random
from time import sleep
import re
import socket
import sys
from multiprocessing import Pool, freeze_support, cpu_count

try:
    import mechanize
    import socks
    from tqdm import tqdm
except ImportError:
    raise Exception('Error: Install the following dependencies: mechanize, PySocks, fake-useragent, tqdm')

try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections

if sys.version_info[0] < 3:
    raise Exception('Must be using Python 3.')


def write_out(name, ar):
    """
Write to file. Then remove any duplicates.
    :param name: Name of txt file to write to.
    :param ar: The array that is being written.
    """
    with open(name, 'a+') as file:
        if type(ar) == list:
            for i in ar:
                file.write(str(i) + '\n')
        else:
            file.write(ar + '\n')

    lines = open(name).readlines()
    lines_set = sorted(list(set(lines)))

    out = open(name, 'w')
    for line in lines_set:
        out.write(line)


def get_phone_numbers(name):
    """
    Opens file with phone numbers in it, finds everything that matches the pattern of a phone number, and returns a list of
    the numbers found.
    :param name: The name of the txt file containing the phone numbers.
    :return: A list of phone numbers found.
    """
    phone_numbers = []
    with open(name) as file:
        phone_numbers = file.read().split('\n')
    return phone_numbers


def get_proxies(name):
    """
    Finds all occurences of strings in a text file matching proxy pattern 000.000.000.000:00000 and returns them.
    :param name: Name of proxy file to read from.
    :return: List of proxies found in file.
    """
    with open(name) as file:
        s = file.read()
    proxy_list = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{,5}', s)
    return proxy_list


def divide_list(big_list, n):
    return [big_list[i:i + n] for i in range(0, len(big_list), n)]  


def parent(func, args):
    """
    Parent function to inherit phone_number_check()'s attributes for multiprocessing.
    :param func: Function to run.
    :param args: Args for function to run.
    :return: Result of function.
    """
    try:
        result = func(*args)
        return result
    except KeyboardInterrupt:
        pass


def phone_number_check(phone_num, prox, loginurl):
    """
    Function to check if a phone number has been used on Netflix. Takes SOCKS5 proxies.
    Visits Netflix, attempts to login, and reads the error message Netflix gives.
    It returns a tuple with a string saying if an account is associated with that number and the phone number itself.
    :param phone_num: Phone number to check.
    :param prox: SOCKS5 proxy to use.
    :param loginurl: URL of Netflix's login page. Here to accomodate multiple countries.
    :param user_a: User agent to use.
    :return: A tuple with a string saying if an account is associated with that number and the phone number itself.
    """
    proxy = list(prox)

    try:
        # temp_proxy = proxy[random.randint(0, len(proxy) - 1)]
        # temp_proxy = temp_proxy.split(':')
        # ip = temp_proxy[0]
        # port = int(temp_proxy[1])
        # socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, ip, port)
        # socket.socket = socks.socksocket

        br = mechanize.Browser()
        br.set_handle_equiv(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        br.addheaders = [("User-agent", "Mozilla/5.0")]

        br.open(loginurl, timeout=2)
        br.select_form(nr=0)
        br.form['userLoginId'] = phone_num
        br.form['password'] = 'passwordpasswordpassword'
        response = br.submit()

        if response.code == 200:
            page = response.read().decode().replace('<b>', '').replace('</b>', '')
            if page.find('Something went wrong') != -1:
                    return 'Something went wrong', phone_num
            elif page.find(
                'find an account with this number') != -1:  # Find out if no account exists with the number being tested.
                return 'No account with number', phone_num  # Success!
                # return 'No account with number', phone_num  # Success!
            elif page.find('Incorrect password') != -1:
                return 'Existing account', phone_num  # No success; account already exists with this number.
                # return 'Existing account', phone_num  # No success; account already exists with this number.
    except Exception as e:
        print(f'Exception occured [{e}], thread going for sleep', phone_num)
        sleep(random.randint(10, 20))
    br.close()

    return 'Error', phone_num


if __name__ == '__main__':
    freeze_support()

    print('Netflix Phone Number Scraper\n')
    NUMBER_OF_PROCESSES = cpu_count() * 2

    default_or_no = input(
        'To run with default settings, press Enter. To run with different settings, please type "change"\n')
    while default_or_no != '' and default_or_no.lower() != 'change':
        default_or_no = input(
            'Error. Bad input. To run with default settings, press Enter. \nTo run with different settings, please type "change"\n')

    if default_or_no:
        country = input(
            'Please enter one of the following countries: us, ca, de, gb, fr, it, jp, au, nl, es, in\n').lower()
        while country not in ['us', 'ca', 'de', 'gb', 'fr', 'it', 'jp', 'au', 'nl', 'es', 'in']:
            country = input(
                'Error. Bad country input. Please enter one of the following countries: us, ca, de, gb, fr, it, jp, au, nl, es, in\n').lower()

        country_file_list = [country + '-numbers.txt', country + '-results.txt', country + '-errors.txt', 'proxies.txt', country + '-processed.txt']
        for i in country_file_list:
            if not os.path.exists(i):
                open(i, 'w').close()

        loginURL = 'https://www.netflix.com/' + country + '-en/login'
        number_file_name = country + '-numbers.txt'
        proxy_file_name = 'proxies.txt'
        results_file_name = country + '-results.txt'
        errors_file_name = country + '-errors.txt'
        processed_file_name = country + '-processed.txt'
    else:
        country = 'us'
        country_file_list = [country + '-numbers.txt', country + '-results.txt', country + '-errors.txt', 'proxies.txt', country + '-processed.txt']
        for i in country_file_list:
            if not os.path.exists(i):
                open(i, 'w').close()
        loginURL = 'https://www.netflix.com/login'
        number_file_name = 'us-numbers.txt'
        proxy_file_name = 'proxies.txt'
        results_file_name = 'us-results.txt'
        errors_file_name = 'us-errors.txt'
        processed_file_name = 'us-processed.txt'

    input(
        'Please fill %s-numbers.txt with phone numbers you\'d like to test and proxies.txt with proxies.\nPress Enter when ready.\n' % (
            number_file_name))

    phone_numbers = get_phone_numbers(number_file_name)
    while len(phone_numbers) < 1:
        input(
            'No phone numbers have been found.\nPlease put numbers in ' + number_file_name + '.\nPress Enter when ready.\n')
        phone_numbers = get_phone_numbers(number_file_name)
    processed_numbers = get_phone_numbers(processed_file_name)
    if len(processed_numbers) > 0:
        phone_numbers = list(set(phone_numbers) - set(processed_numbers))
    if len(phone_numbers) < 1:
        input('All numbers are processed \nPress Enter to EXIT!!')
    proxy_list = get_proxies(proxy_file_name)
    processed_results = []
    errors = []

    phone_numbers_list = divide_list(phone_numbers,40)
    max_index = len(phone_numbers_list) * 10
        
    for index in range(len(phone_numbers_list)):
        processed_results = []
        bad_results = []
        errors = []

        with Pool(NUMBER_OF_PROCESSES, maxtasksperchild=5) as pool:
            try:
                TASKS = [(phone_number_check, (x, proxy_list, loginURL)) for x in phone_numbers_list[index]]

                results = [pool.apply_async(parent, t) for t in TASKS]
                for r in results:
                    res = r.get()
                    if res[0] == 'No account with number':
                        processed_results.append(res[1])
                        write_out(processed_file_name, res[1])
                        print(res)
                    elif res[0] == 'Existing account':
                        processed_results.append(res[1])
                        write_out(processed_file_name, res[1])
                        write_out(results_file_name, res[1])
                        print(res)        
                    else:
                        errors.append(res[1])
                        write_out(errors_file_name, res[1])
            except Exception as e:
                print('\nException occured for the batch, main thread going for next batch after 1 min of sleep')
                print(e)
        phone_numbers_list[index] = processed_results
        phone_numbers_list.append(errors)
    print('\nDone!')
    