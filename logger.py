from config import log_file,autofollow_log_file
from json import dumps
import datetime

"""who needs standart libs anyway"""

date = str(datetime.datetime.now())


def add_post(img_path, media_state):
    with open(log_file, 'a') as log:
        log.write(date + '\t' + str(img_path) + '\t' + str(media_state) + '\n')


def add_follow(userid):
    with open(autofollow_log_file, 'a') as log:
        log.write(str(userid) + '\n')


def check_follow():
    already_followed_array = []
    with open(autofollow_log_file, 'r') as log: #get array of users who we followed from log
            for line in log:
                if not int(line) in already_followed_array:
                    already_followed_array.append(int(line))
    return already_followed_array


def save(text,file):
    with open(file, 'w') as f:
        f.write(str(text))

def dump(text,file):
    with open(file, 'w') as f:
        f.write(dumps(text))