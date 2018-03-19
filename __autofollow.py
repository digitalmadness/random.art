'''
this script searches tweets with desired hashtag, likes them(optional) and follows author '''

import tweepy
from random import randint # +146% to sneaking from twatter bot policy
from pyfiglet import Figlet
from time import sleep # +1000% to sneaking
from sys import argv
import argparse
import config

def main():
    '''runs autofollow addon'''
    unfollow_arg = argument_parser(argv[1:]).u
    y = Figlet(font='slant')
    print(y.renderText("""autofollow.py"""),'\n\nlogging in..') #print welcome message
    global api
    api = config.api
    me = api.me()
    followers_array = []
    for page in tweepy.Cursor(api.followers_ids, id=me.id).pages():
        followers_array.extend(page)
    following_array = []
    for page in tweepy.Cursor(api.friends_ids, id=me.id).pages():
        following_array.extend(page)
    try:
        with open(config.autofollow_log_file, 'r') as log_file: #get array of users who we followed from log
            already_followed_array = [line.rstrip('\n') for line in log_file]
    except FileNotFoundError:
        with open(config.autofollow_log_file, 'w') as log_file: #create log if not found
            log_file.write('')
        already_followed_array = []
    following_counter = len(following_array)

    print('\nwelcome, @' + me.screen_name + '!\n\nfollowers:',len(followers_array),'\nfollowing:',len(following_array),'\n\nsearching for tweets with',config.search_phrase,'and following author')
    if config.like_opt:
        print('\nlike every found tweet option enabled!')
    if config.followback_opt:
        print('\nfollow those who already follows you option enabled!')

    while following_counter < int(config.custom_following_limit): #respecc user set limit
        stop_code = ''
        following_now_counter = 0
        if not unfollow_arg:
            stop_code,following_now_counter = follow_subroutine(followers_array, following_counter, config.search_phrase, int(config.custom_following_limit), bool(config.followback_opt), bool(config.like_opt))
        if stop_code == 'custom_following_limit_hit':
            break
        if unfollow_arg or stop_code == 'following_hardlimit_hit':
            if not bool(config.unfollow_opt):
                print('unfollowing subroutine disabled in settings! this script cant follow more people')
                break
            else:
                unfollow_subroutine(following_array,followers_array,int(config.custom_unfollowing_limit),following_now_counter)
        if stop_code == 'restart':
            stop_code,following_now_counter = follow_subroutine(followers_array, following_counter, config.search_phrase, int(config.custom_following_limit), bool(config.followback_opt), bool(config.like_opt))

    print('\nmission completion! this script will close in 5 sec..')
    sleep(5)


def follow_subroutine(followers_array, following_counter, search_phrase, custom_following_limit, followback_opt, like_opt):
    '''finds tweets and follows author (and likes tweet if set)'''
    print('\nstarting following subroutine..')
    following_now_counter = 0
    for twit in tweepy.Cursor(api.search, q=search_phrase).items():
        if following_counter >= custom_following_limit:
                print('\ncustom following limit hit! stopping following subroutine...')
                return 'custom_following_limit_hit',0
        sleep_time = randint(1,5)
        sleep_time_long = randint(10,15)
        if following_counter >= randint(4700,4990):
            if following_counter >= len(followers_array) - randint(10,300):
                print('\nfollowing subroutine stopped, you are too close to twitter following hardlimit:',len(followers_array),'\nsleeping',sleep_time_long,'seconds before next step to avoid detection..\n')
                sleep(sleep_time_long)
                return 'following_hardlimit_hit',following_now_counter
            if len(followers_array) <= 5000:
                print('\nfollowing subroutine stopped, you are too close to twitter following hardlimit: 5000\nsleeping',sleep_time_long,'seconds before next step to avoid detection..\n')
                sleep(sleep_time_long)
                return 'following_hardlimit_hit',following_now_counter
        try:
            is_following_us_state = False
            already_followed_state = False
            print('\nfound tweet by @' + twit.user.screen_name)
            with open(config.autofollow_log_file, 'r') as log_file: #check users whom we followed every time
                already_followed_array = [line.rstrip('\n') for line in log_file]
            for element in already_followed_array:
                if element == twit.user.id:
                    already_followed_state = True #user was already followed once by script
            for element in followers_array:
                if element == twit.user.id:
                    is_following_us_state = True #user is already following us, no need to waste daily limit
            if is_following_us_state and not followback_opt:
                print('this user already follows us, skipping..')
            else:
                if twit.user.following:
                    print('already following this user..')
                else:
                    if already_followed_state:
                        print('already followed once, skipping..')
                    else:
                        twit.user.follow()
                        following_now_counter = following_now_counter + 1
                        following_counter = following_counter + 1
                        print('followed this user, total following:',following_counter,'followed now:',following_now_counter,'\nsleeping',sleep_time,'sec to avoid detection..') # global following count
                        if like_opt:
                            twit.favorite()
                            print('liked this tweet')
                        with open(config.autofollow_log_file, 'a') as log_file:
                            log_file.write(str(twit.user.id) + '\n') #log ids for future checks
                        sleep(sleep_time)
    
        except tweepy.TweepError as e:
            print('\ntweepy error!\n' + e.reason)
            if '161' in str(e.reason):
                print('\ncode 161 detected! you probably ran out of daily following limit\n\nTWITTER REJECTED FOLLOW\n\ndo not try to follow more people now or u might get banned!\n\nwaiting 10 hours before next try..')
                sleep(10*60*60)
                return 'restart',0

        except StopIteration:
            print('\nwe searched all tweets, sleeping for 10 minutes before next try..')
            sleep(600)
            return 'restart',0


def unfollow_subroutine(following_array,followers_array,custom_unfollowing_limit,following_now_counter):
    '''unfollows non mutuals (followed by this script only!!) from oldest to newest'''
    print('\nstarting unfollowing subroutine..\nno worries, it will unfollow only non mutuals followed by this script\n')
    unfollowed_count = 0
    unfollowing_candidates = []
    with open(config.autofollow_log_file, 'r') as log_file: #get array of users who we followed from log
        already_followed_array = [line.rstrip('\n') for line in log_file]
    for dood in reversed(following_array):
        if not dood in reversed(followers_array) and dood in map(int, already_followed_array):
            unfollowing_candidates.append(dood)
    print(len(unfollowing_candidates),'candidates for unfollow\n')
    for dood in unfollowing_candidates:
        sleep_time = randint(2,10)
        print('user id',dood, 'was followed by this script but didnt followed you back')
        api.destroy_friendship(id=dood)
        unfollowed_count = unfollowed_count + 1
        print('unfollowed him.. total:',unfollowed_count,'\nsleeping',sleep_time,'sec to avoid detection..')
        sleep(sleep_time)
        if unfollowed_count > randint(custom_unfollowing_limit - 100, custom_unfollowing_limit) or unfollowed_count >= len(unfollowing_candidates) - following_now_counter:
            sleep_time_long = randint(60*60, 5*60*60)
            print('\nunfollowing subroutine stopped',unfollowing_count,'users was unfollowed\nsleeping',sleep_time_long,'before another following to avoid detection..\n')
            sleep(sleep_time_long)
            break


def argument_parser(args):
    """parsing arguments from command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", help="start unfollow subroutine first",
                        action="store_true")
    return parser.parse_args(args)


main()
