'''
this script searches tweets with desired hashtag, likes them(optional) and follows author '''

import tweepy
import random
from pyfiglet import Figlet
from time import sleep
import config

def main():
    '''runs autofollow addon'''
    search_phrase = config.search_phrase
    followback_opt = config.followback_opt
    like_opt = config.like_opt

    y = Figlet(font='slant')
    print(y.renderText("""autofollow.py"""),'\n\nlogging in..') #print welcome message
    global api
    api = config.api
    me = api.me()
    me = me.screen_name
    followers_array = []
    for page in tweepy.Cursor(api.followers_ids, screen_name=me).pages():
        followers_array.extend(page)
    following_array = []
    for page in tweepy.Cursor(api.friends_ids, screen_name=me).pages():
        following_array.extend(page)
    with open('autofollow_log.txt', 'r') as followed_log_file: #get array of users who we followed from log
            already_followed_array = [line.rstrip('\n') for line in followed_log_file]
    following_counter = len(following_array)

    print('\nwelcome, @' + me + '!\n\nfollowers:',len(followers_array),'\nfollowing:',len(following_array),'\n\nsearching for tweets with',search_phrase,'and following author, will stop after',config.custom_following_limit,'people followed')
    if like_opt != '':
        print('\nlike every found tweet option enabled!')
    if followback_opt != '':
        print('\nfollow those who already follows you option enabled!')

    while following_counter < int(config.custom_following_limit): #respecc user set limit
        following_counter = follow(followers_array, following_counter, search_phrase, followback_opt, like_opt)
        print('\nmission completion! this window will close in 5 sec')
        sleep(5)
        break


def follow(followers_array, following_counter, search_phrase, followback_opt, like_opt):
    '''finds tweets and follows author (and likes tweet if set)'''
    print('\nstarting following cycle..')
    following_counter_updated = following_counter
    for twit in tweepy.Cursor(api.search, q=search_phrase).items():
        sleep_time = random.randint(1,5)
        sleep_time_long = random.randint(10,15)
        if following_counter_updated >= random.randint(4400,4500):
            if following_counter_updated >= len(followers_array) - random.randint(300,600):
                print('\nfollowing cycle stopped, you are too close to twitter following hardlimit:',len(followers_array),'\nsleeping',sleep_time_long,'seconds between cycles to avoid detection..')
                sleep(sleep_time_long)
                break
            if len(followers_array) <= 5000:
                print('\nfollowing cycle stopped, you are too close to twitter following hardlimit: 5000\nsleeping',sleep_time_long,'seconds between cycles to avoid detection..')
                sleep(sleep_time_long)
                break
        try:
            is_following_us_state = False
            already_followed_state = False
            username = twit.user.screen_name
            userid = twit.user.id
            print('\nfound tweet by @' + username)
            with open('autofollow_log.txt', 'r') as followed_log_file: #check users whom we followed every time
                already_followed_array = [line.rstrip('\n') for line in followed_log_file]
            for element in already_followed_array:
                if element == username:
                    already_followed_state = True #user was already followed once by script
            for element in followers_array:
                if element == userid:
                    is_following_us_state = True #user is already following us, no need to waste daily limit
            if is_following_us_state == True and followback_opt == '':
                print('this user already follows us, skipping..')
            else:
                if twit.user.following:
                    print('already following this user..')
                else:
                    if already_followed_state:
                        print('already followed once, skipping..')
                    else:
                        twit.user.follow()
                        following_counter_updated = following_counter_updated + 1
                        print('followed this user, now following:',following_counter_updated,'\nsleeping',sleep_time,'sec to avoid detection..') # global following count
                        if like_opt != '':
                            twit.favorite()
                            print('liked this tweet')
                        with open('autofollow_log.txt', 'a') as followed_log_file_edit:
                            followed_log_file_edit.write(twit.user.screen_name + '\n') #log usernames for future checks
                        sleep(sleep_time)
    
        except tweepy.TweepError as e:
            print('\ntweepy error!\n' + e.reason)
            if '161' in str(e.reason):
                print('\ncode 161 detected! you probably ran out of daily following limit\n\nTWITTER REJECTED FOLLOW\n\ndo not try to follow more people now or u might get banned!\n\nwaiting 10 hours before next try..')
                sleep(10*60*60)

        except StopIteration:
            print('\nwe searched all tweets, sleeping for 10 minutes before next try..')
            sleep(600)
            break
    return following_counter_updated


main()
