import tweepy
import random # +146% to sneaking from twatter bot policy
from time import sleep # +1000% to sneaking
from sys import argv
from pyfiglet import Figlet
import argparse
import config
from requests_oauthlib import OAuth1Session
import webbrowser

''' this script searches tweets with desired phrase(configure is settings), likes them(optional) and follows author if all checks passed '''


def main():
    '''run autofollow addon'''
    unfollow_arg = argument_parser(argv[1:]).u
    print(Figlet(font='slant').renderText('''autofollow'''),'\n\nlogging in..') #print welcome message
    token,secret = get_tokens()
    global api
    api = temp_auth(token, secret)
    myid = api.me().id
    followers_array = []
    for page in tweepy.Cursor(api.followers_ids, id=myid).pages():
        followers_array.extend(page)
    following_array = []
    for page in tweepy.Cursor(api.friends_ids, id=myid).pages():
        following_array.extend(page)
    following_counter = len(following_array)
    print('\nwelcome, @' + api.me().screen_name + '!\n\nfollowers:',len(followers_array),'\nfollowing:',len(following_array),'\n\nsearching for tweets with',config.search_phrase,'and following authors with > ',config.min_followers,'followers')
    if config.like_opt:
        print('\nlike every found tweet option enabled!')
    if config.followback_opt:
        print('\nfollow those who already follows you option enabled!')
    stop_code = 'null'
    following_now_counter = 0
    while True:
        if unfollow_arg or stop_code == 'following_hardlimit_hit':
            if not bool(config.unfollow_opt):
                print('unfollowing option disabled in settings! this script cant follow more people, exiting now')
                break
            else:
                unfollow_subroutine(following_array,followers_array,int(config.custom_unfollowing_limit),following_now_counter)
                following_now_counter = 0
        stop_code,following_now_counter = follow_subroutine(followers_array, following_counter, config.search_phrase, int(config.custom_following_limit), bool(config.followback_opt), bool(config.like_opt), following_now_counter)
        if stop_code == 'custom_following_limit_hit':
            print('mission completion! script will exit now')
            break


def follow_subroutine(followers_array, following_counter, search_phrase, custom_following_limit, followback_opt, like_opt, following_now_counter):
    '''find tweets and follow author if all checks passed (and like tweet if set)'''
    print('\nstarting following subroutine..\nwill stop after',custom_following_limit,'people followed')
    already_followed_array = []
    sleep_time_long = 6*60*60+60*random.random()
    with open(config.autofollow_log_file, 'r') as log_file: #get array of users who we followed from log
        for line in log_file:
            if not int(line) in already_followed_array:
                already_followed_array.append(int(line))
    for twit in tweepy.Cursor(api.search, q=search_phrase).items():
        if following_counter >= custom_following_limit:
                return 'custom_following_limit_hit', following_now_counter
        sleep_time = 1+random.random()
        if following_counter >= random.randint(4988,5000):
            if following_counter >= len(followers_array)+500 - random.randint(10,20):
                print('\nfollowing subroutine stopped, you are too close to twitter following hardlimit:',len(followers_array),'\nsleeping',sleep_time,'sec before next step to avoid detection..\n')
                sleep(sleep_time)
                return 'following_hardlimit_hit',following_now_counter
            if len(followers_array) <= 5000:
                print('\nfollowing subroutine stopped, you are too close to twitter following hardlimit: 5000\nsleeping',sleep_time,'sec before next step to avoid detection..\n')
                sleep(sleep_time)
                return 'following_hardlimit_hit',following_now_counter
        try:
            userid = twit.user.id
            print('\nfound tweet by user id',userid)
            if userid in followers_array and not followback_opt:
                print('this user already follows us..')
            else:
                if userid in already_followed_array:
                    print('already tried to follow this user..')
                else:
                    if twit.user.following:
                        print('already following this user(not by script)..')
                        already_followed_array.append(userid)
                        with open(config.autofollow_log_file, 'a') as log_file:
                            log_file.write(str(userid) + '\n')
                    else:
                        dood_followers_count = twit.user.followers_count
                        dood_following_count = twit.user.friends_count
                        if dood_following_count > dood_followers_count - dood_followers_count*0.1 and dood_following_count < 2*dood_followers_count and dood_followers_count > config.min_followers:
                            twit.user.follow()
                            following_now_counter += 1
                            following_counter += 1  # real following counter
                            print('followed this user | total following:',following_counter,'| followed now:',following_now_counter,'\nsleeping',sleep_time,'sec to avoid detection..')
                            if like_opt:
                                twit.favorite()
                                print('liked this tweet')
                            sleep(sleep_time)
                        else:
                            if dood_following_count < dood_followers_count - dood_followers_count*0.1:
                                print('.doesnt seems like mutual')
                            if dood_following_count > 2*dood_followers_count:
                                print('.follows more than 2x his followers, obviously bot')
                            if dood_followers_count < config.min_followers:
                                print('.doesnt have enough followers')
                        already_followed_array.append(userid)
                        with open(config.autofollow_log_file, 'a') as log_file:
                            log_file.write(str(userid) + '\n')
        except tweepy.TweepError as e:
            print('\ntweepy error!\n' + e.reason)
            if '161' in str(e.reason):
                print('\ncode 161 detected! you probably ran out of daily following limit\n\ndo not try to follow more people now or u might get banned!\n\nwaiting',sleep_time_long,'sec before next try..')
                sleep(sleep_time_long)
                return 'restart', following_now_counter
        except StopIteration:
            print('\nwe searched all tweets, sleeping 5 minutes before next try..')
            sleep(300)
            return 'restart', following_now_counter
    print('following subroutine crashed for some reason, restarting in',sleep_time,'sec')
    sleep(sleep_time)
    return 'restart', following_now_counter


def unfollow_subroutine(following_array,followers_array,custom_unfollowing_limit,following_now_counter):
    '''unfollow non mutuals'''
    print('\nstarting unfollowing subroutine, lets clean some space for new people..\nno worries, it will unfollow only non mutuals followed by this script from oldest to newest\nwill stop after',custom_unfollowing_limit,'users unfollowed')
    already_followed_array = []
    unfollowing_candidates = []
    with open(config.autofollow_log_file, 'r') as log_file: #get array of users who we followed from log
        for line in log_file:
            if not int(line) in already_followed_array:
                already_followed_array.append(int(line))
    for dood in reversed(following_array):
        if not dood in reversed(followers_array) and dood in already_followed_array:
            unfollowing_candidates.append(dood)
    print(len(unfollowing_candidates),'candidates for unfollow\n')
    for unfollowed_count,dood in enumerate(unfollowing_candidates):
        sleep_time = random.random()
        print('user id ',dood, '(followed by this script) didnt followed you back')
        api.destroy_friendship(id=dood)
        unfollowed_count += 1
        print('unfollowed him.. total:',unfollowed_count,'\nsleeping',sleep_time,'sec to avoid detection..\n')
        sleep(sleep_time)
        if unfollowed_count > random.randint(custom_unfollowing_limit - 10, custom_unfollowing_limit) or unfollowed_count >= len(unfollowing_candidates) - following_now_counter:
            sleep_time_long = 60*60+60*random.random()
            print('\nunfollowing subroutine stopped',unfollowed_count,'users was unfollowed\nsleeping',sleep_time_long,' sec before another following cycle to avoid detection..\n')
            sleep(sleep_time_long)
            break


def get_tokens():
    '''get temp oauth tokens using totally legit api keys'''
    consumer_key = 'Fpl5UUVwvaczUzzpVJ8Rlw'
    consumer_secret = 'z73HF21zCz5CaxzDM6M0OPeaCBYGfHUG3FYBgcMB2Y'
    REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
    SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri='oob')
    print('\nRequesting temp token from Twitter...\n')
    try:
        resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
    except ValueError as e:
        raise 'Invalid response from Twitter requesting temp token: {0}'.format(e)
    url = oauth_client.authorization_url(AUTHORIZATION_URL)
    print('trying to start a browser to visit the following Twitter page.. '
          'if a browser will not start, copy the URL to your browser '
          'and retrieve the pincode to be used '
          'in the next step to obtaining an Authentication Token: \n'
          '\n\t{0}'.format(url))
    webbrowser.open(url)
    pincode = input('\nenter your pincode? ')
    print('\ngenerating and signing request for an access token...\n')
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret,
                                 resource_owner_key=resp.get('oauth_token'),
                                 resource_owner_secret=resp.get('oauth_token_secret'),
                                 verifier=pincode)
    try:
        resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
    except ValueError as e:
        raise 'invalid response from Twitter requesting temp token: {0}'.format(e)
    return resp.get('oauth_token'),resp.get('oauth_token_secret')


def temp_auth(token,token_secret):
    '''set api with temp oauth tokens'''
    auth = tweepy.OAuthHandler('Fpl5UUVwvaczUzzpVJ8Rlw', 'z73HF21zCz5CaxzDM6M0OPeaCBYGfHUG3FYBgcMB2Y')
    auth.set_access_token(token,token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
    return api


def argument_parser(args):
    '''parsing CLI arguments'''
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', help='start unfollow subroutine first',
                        action='store_true')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
