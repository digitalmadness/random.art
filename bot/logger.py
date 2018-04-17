from json import dumps
import time
import datetime
import os
import wget

"""who needs standart libs anyway"""

date = str(datetime.datetime.now())
logs_folder = str(os.path.dirname(os.path.abspath(__file__))).replace('/bot','/logs')
if not os.path.exists(logs_folder):
    os.makedirs(logs_folder)


def add_post(img_path, media_state):
    with open(logs_folder + '/randomart_log.txt', 'a') as log:
        log.write(date + '\t' + str(img_path) + '\t' + str(media_state) + '\n')


def check_posts(tolerance):
    if os.path.isfile(logs_folder + '/randomart_log.txt'):
        already_tweeted = open(logs_folder + '/randomart_log.txt', 'r').readlines()[tolerance:]
    else:
        already_tweeted = []
        with open(logs_folder + '/randomart_log.txt', 'a') as log:
            log.write('')
    return already_tweeted


def add_follow(userid):
    with open(logs_folder + '/autofollow_log.txt', 'a') as log:
        log.write(str(userid) + '\n')


def check_follow():
    already_followed_array = []
    if os.path.isfile(logs_folder + '/autofollow_log.txt'):
        with open(logs_folder + '/autofollow_log.txt', 'r') as log: #get array of users who we followed from log
            for line in log:
                if not int(line) in already_followed_array:
                    already_followed_array.append(int(line))
    else:
        with open(logs_folder + '/autofollow_log.txt', 'a') as log:
            log.write('')
    return already_followed_array


def save(text,file):
    with open(logs_folder + '/' + file, 'w') as f:
        f.write(str(text))


def dump(text,file):
    with open(logs_folder + '/' + file, 'w') as f:
        f.write(dumps(text))


def save_profile_pic(url):
    return wget.download(url, out=logs_folder+'/')


def read(file):
    if os.path.isfile(logs_folder + '/' + file):
        with open(logs_folder + '/' + file, 'r') as f:
            return f.read()
    else:
        with open(logs_folder + '/' + file, 'a') as f:
            f.write('1')
            return '1'


def fmtime(file):
    return time.time(),os.path.getmtime(logs_folder + '/' + file)
