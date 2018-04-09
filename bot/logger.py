from json import dumps
import datetime
import os

"""who needs standart libs anyway"""

date = str(datetime.datetime.now())
current_folder = str(os.path.dirname(os.path.abspath(__file__))).replace('/bot','')

def add_post(img_path, media_state):
    with open(current_folder + '/logs/randomart_log.txt', 'a') as log:
        log.write(date + '\t' + str(img_path) + '\t' + str(media_state) + '\n')


def check_posts(tolerance):
    try:
        already_tweeted = open(current_folder + '/logs/randomart_log.txt', 'r').readlines()[tolerance:]
    except IndexError:
        already_tweeted = open(current_folder + '/logs/randomart_log.txt', 'r').readlines()
    except Exception:
        already_tweeted = []
        with open(current_folder + '/logs/randomart_log.txt', 'a') as log:
            log.write('\n')
    return already_tweeted


def add_follow(userid):
    with open(current_folder + '/logs/autofollow_log.txt', 'a') as log:
        log.write(str(userid) + '\n')


def check_follow():
    already_followed_array = []
    try:
        with open(current_folder + '/logs/autofollow_log.txt', 'r') as log: #get array of users who we followed from log
            for line in log:
                if not int(line) in already_followed_array:
                    already_followed_array.append(int(line))
    except Exception:
        with open(current_folder + '/logs/autofollow_log.txt', 'a') as log:
            log.write('\n')
    return already_followed_array


def save(text,file):
    with open(current_folder + '/logs/' + file, 'w') as f:
        f.write(str(text))


def dump(text,file):
    with open(current_folder + '/logs/' + file, 'w') as f:
        f.write(dumps(text))


def read(file):
    with open(current_folder + '/logs/' + file, 'r') as f:
        return f.read()
