import time

from bs4 import BeautifulSoup, SoupStrainer
from user_agent import generate_user_agent
from random import randint, choice
from colorama import Fore, init
from functools import partial
from threading import Thread
import threading
import requests
import urllib3
import logging
import string
import names
import queue
import json
import re

init(autoreset=True)
logging.basicConfig(filename='errors.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(name)s %(message)s')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# globals
logger = logging.getLogger(__name__)
lock = threading.Lock()
colors = [vars(Fore)[color] for color in vars(Fore) if color in ['BLUE', 'CYAN', 'GREEN', 'MAGENTA', 'WHITE', 'YELLOW']]
strainer = SoupStrainer('div', class_='freebirdFormviewerViewResponseConfirmationMessage')
url = "https://docs.google.com/forms/d/e/1FAIpQLSdhFkAfM1VGDvbp0f3ETi-DaNRTswB7IgIC9uoWbECCd7sI6g/viewform"
post_url = "https://docs.google.com/forms/d/e/1FAIpQLSdhFkAfM1VGDvbp0f3ETi-DaNRTswB7IgIC9uoWbECCd7sI6g/formResponse"


def rand_chars(num=4):
    return ''.join(choice(string.ascii_uppercase) for _ in range(num))


def handle_post(email, r, *args, **kwargs):
    # parse request for success
    if r.status_code == 200:
        bs = BeautifulSoup(r.text, 'lxml', parse_only=strainer)
        if bs.find('div').text == "Thank you for subscribing / Grazie per esserti iscritto":
            with lock:
                Presto.entry_success.add(email)
                msg = ''.join([colors[(idx+len(Presto.entry_success)) % len(colors)] + char for idx, char in enumerate("success")])
                print(f'{colors[len(Presto.entry_success) % len(colors)]}{email.split("@")[0]}\t{msg}'.expandtabs(tabsize=30))
        else:
            logger.error(f'{self.name} - error parsing raffle post response')
    else:
        logger.error(f'{self.name} - error sending post request ({r.status_code})\n')


class Presto(Thread):
    entry_success = set()
    proxy_queue = queue.Queue()
    sessions = {}

    def __init__(self):
        super().__init__()
        self.sess = None if config['use_proxies'] else requests.session()
        self.curr_proxy = None

    def run(self):
        for i in range(config['max_entries_per_thread']):
            if config['use_proxies']:
                self.curr_proxy = Presto.proxy_queue.get()
                self.sess = Presto.sessions[self.curr_proxy]
            self.sess.headers.update({
                'User-Agent': generate_user_agent(device_type='desktop')
            })
            try:
                # get form
                resp = self.sess.get(url)
                if resp.status_code != 200:
                    logging.error(f'{self.name} - error retrieving raffle page ({resp.status_code})')
                    continue
                # find unique id
                resid = re.search('name="fbzx" value="(.*?)">', resp.text).group(1)
                # create randomized data
                first = names.get_first_name()
                last = names.get_last_name()
                email = f'{first}.{last}@{config["catchall"]}'

                data = {
                    "emailAddress": email,
                    "entry.1884265043": first,
                    "entry.1938400468": last,
                    "entry.1450673532_year": str(randint(1975, 1995)),
                    "entry.1450673532_month": '{:02}'.format(randint(1, 12)),
                    "entry.1450673532_day": '{:02}'.format(randint(1, 27)),
                    "entry.71493440": profile['address'] % rand_chars() + choice(profile.get('endings')) if profile.get('endings') else '',
                    "entry.1981412943": profile['zip'],
                    "entry.950259558": profile['city'],
                    "entry.1622497152": choice(
                        ['United States', 'US', 'USA', 'United States of America', 'U.S.A', 'U.S']),
                    "entry.1850033056": "",
                    "entry.769447175": profile['ig_username'],
                    "entry.256744251_sentinel": "",
                    "entry.256744251": "Autorizzo il trattamento dei miei dati personali, ai sensi del D.lgs. 196 del 30 giugno 2003",
                    "entry.715796591": str(randint(4, 12)),
                    "fvv": "1",
                    "draftResponse": f'[null,null,"{resid}"]',
                    "pageHistory": "0",
                    "fbzx": f'{resid}'
                }
                headers = {
                    "Upgrade-Insecure-Requests": "1",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "X-Client-Data": "CJG2yQEIorbJAQjEtskBCKmdygEI153KAQioo8oB",
                    "X-Chrome-Connected": "id=113292259032357480973,mode=0,enable_account_consistency=false",
                    "Referer": f'{url}?fbzx={resid}',
                    "Accept-Encoding": "gzip, deflate, br1",
                    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
                }
                # submit post request
                self.sess.post(post_url, headers=headers, data=data, hooks={'response': partial(handle_post, email)})
            except Exception as e:
                logging.error(f'{self.name} - exception caught:\n{e}')
                time.sleep(config['exception_timeout'])
            finally:
                self.sess.cookies.clear()
                if self.curr_proxy:
                    Presto.proxy_queue.put_nowait(self.curr_proxy)
                    self.curr_proxy = None


if __name__ == "__main__":
    with open('config.json', 'r') as file:
        config = json.load(file)

    profile = config['profiles']['jonathan']

    if config['use_proxies']:
        with open('proxies.txt', 'r+') as file:
            for line in file:
                proxy_str = line.strip()
                new_sess = requests.session()
                new_sess.verify = False
                new_sess.proxies.update(https='https://'+proxy_str)
                Presto.sessions[proxy_str] = new_sess
                for i in range(config['max_connections_per_proxy']):
                    Presto.proxy_queue.put_nowait(proxy_str)

    print(Fore.YELLOW + f' ** Starting {config["num_threads"]} threads **')
    print(Fore.YELLOW + f' ** Attempting {config["num_threads"] * config["max_entries_per_thread"]} entries')

    try:
        threads = []
        for i in range(config['num_threads']):
            thread = Presto()
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print('cancelling')
    finally:
        [value.close() for key, value in Presto.sessions.items()]
        with open(f'enteredaccounts_{profile["ig_username"]}.txt', 'a+') as file:
            for item in Presto.entry_success:
                file.write(item + '\n')

    print(Fore.CYAN + f'\n ** {threading.current_thread().name} FINISHED **')
    print(Fore.GREEN + f'\n ** {len(Presto.entry_success)} SUCCESSFUL RAFFLE ENTRIES **')