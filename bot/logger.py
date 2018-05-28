from json import dumps
import os
import wget

"""who needs standart libs anyway"""

logs_folder = str(os.path.dirname(os.path.abspath(__file__))).replace('/bot','/logs')
if not os.path.exists(logs_folder):
    os.makedirs(logs_folder)


def add_post(img_path):
    with open(logs_folder + '/randomart_log.txt', 'a') as log:
        log.write(str(img_path) + '\n')


def read_posts():
    if os.path.isfile(logs_folder + '/randomart_log.txt'):
        with open(logs_folder + '/randomart_log.txt', 'r') as log:
            return [line.rstrip('\n') for line in log]
    else:
        with open(logs_folder + '/randomart_log.txt', 'a') as log:
            log.write('')
        return []



def add_followed(userid):
    with open(logs_folder + '/autofollow_log.txt', 'a') as log:
        log.write(str(userid) + '\n')


def read_followed():
    if os.path.isfile(logs_folder + '/autofollow_log.txt'):
        with open(logs_folder + '/autofollow_log.txt', 'r') as log: #get array of users who we followed from log
            return set(map(int, log))
    else:
        with open(logs_folder + '/autofollow_log.txt', 'a') as log:
            log.write('')
        return set([])


def add_checked(userid):
    with open(logs_folder + '/autofollow_checked_log.txt', 'a') as log:
        log.write(str(userid) + '\n')


def read_checked():
    if os.path.isfile(logs_folder + '/autofollow_checked_log.txt'):
        with open(logs_folder + '/autofollow_checked_log.txt', 'r') as log: #get array of users who we checked from log
            return set(map(int, log))
    else:
        with open(logs_folder + '/autofollow_checked_log.txt', 'a') as log:
            log.write('')
    return set([])


def save(text,file):
    with open(logs_folder + '/' + file, 'w') as f:
        f.write(str(text))


def dump(text,file):
    with open(logs_folder + '/' + file, 'w') as f:
        f.write(dumps(text))


def save_profile_pic(url):
    try:
        return wget.download(url, out=logs_folder+'/')
    except Exception:
        print('error downloading profile pic')


def read(file):
    if os.path.isfile(logs_folder + '/' + file):
        with open(logs_folder + '/' + file, 'r') as f:
            return f.read()
    else:
        with open(logs_folder + '/' + file, 'a') as f:
            f.write('1')
            return '1'


def fmtime(file):
    return os.path.getmtime(logs_folder + '/' + file)
