import datetime

"""who needs standart logger lib anyway"""

date = str(datetime.datetime.now())


def addPost(img_path, reply_id, log):
    with open(log, 'a') as log:
        log.write(date + '\t' + str(img_path) + '\t' + str(reply_id) + '\n')
