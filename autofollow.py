from bot import config,logger 
from neuralnet import face_detect
import tweepy
from random import randint,uniform
from sys import argv,exit
from pyfiglet import Figlet
from argparse import ArgumentParser
from requests_oauthlib import OAuth1Session
from os import remove
import webbrowser
import time
import datetime


def main():
    '''runs autofollow addon'''
    args = parse_args(argv[1:])
    if args.s:
        print(Figlet(font='slant').renderText('''autostream'''),'\n\nlogging in..')
    elif args.u:
        print(Figlet(font='slant').renderText('''autounfollow'''),'\n\nlogging in..')
    else:
        print(Figlet(font='slant').renderText('''autofollow'''),'\n\nlogging in..') #welcome message
    token,secret = get_tokens()
    global api
    api = temp_auth(token, secret)
    me = api.me()
    myid = me.id
    followers_array = []
    for page in tweepy.Cursor(api.followers_ids, id=myid).pages():
        followers_array.extend(page)
    #logger.save(followers_array,'followers_backup.txt')
    followers_array = set(followers_array)
    if args.s:
        global following_array
        global myname
        global liked_tweets_array
        global already_followed_array
    myname = me.screen_name 
    following_array = []
    for page in tweepy.Cursor(api.friends_ids, id=myid).pages():
        following_array.extend(page)
    print('\nwelcome, @' + myname + '!\n\nfollowers:',len(followers_array),'\nfollowing:',len(following_array))
    if args.s:
        following_array = set(following_array)
        liked_tweets_array = []
        already_followed_array = logger.read_followed()
        while True:
            try:
                myStream = tweepy.Stream(auth = api.auth, listener=MyStreamListener())
                print('\nconnected to stream! listening for events..')
                myStream.userstream()
            except Exception as e:
                print('\n\nsomething fucked up:',e,',\nrestarting..')
    else:
        if args.f:
            print('\nstealing followers with > ',config.min_followers)
        elif not args.u:
            print('\nsearching for tweets with',config.search_phrase,'and following authors with > ',config.min_followers,'followers')
        stop_code = 'null'
        following_counter = len(following_array)
        following_now_counter = 0
        while True:
            if args.u or stop_code == 'following_hardlimit_hit':
                if not config.unfollow_opt:
                    print('unfollowing option disabled in settings! this script cant follow more people, exiting now')
                    break
                else:
                    unfollow_non_mutuals(following_array,followers_array)
                    following_now_counter = 0
            if args.f:
                stop_code,following_now_counter = steal_followers(following_array, followers_array, myid, following_counter, following_now_counter)
            else:
                stop_code,following_now_counter = search_new_followers(followers_array, following_counter, config.search_phrase, following_now_counter)
                if stop_code == 'custom_following_limit_hit':
                    print('mission completion! script will exit now')
                    break


class MyStreamListener(tweepy.StreamListener):
    def on_event(self, status):
        '''launches on any streaming event and does auto(like)followback if criteria met'''
        update_states()
        source = status._json.get('source')
        userid = int(source.get('id'))
        screenname = source.get('screen_name')
        username = '@'+screenname
        if status.event == 'follow' and userid in already_followed_array and screenname != myname:
            print('\nincoming followback by',username)
        elif screenname != myname:
            print('\nincoming',status.event,'by',username)
        if config.likeback_opt and status.event == 'favorite' and screenname != myname:
            if userid in following_array or userid in already_followed_array:
                print(username,'is already followed, trying to likeback..')
                tweets = []
                try:
                    for status2_count,status2 in enumerate(tweepy.Cursor(api.user_timeline,id=username).items()):
                            if logger.read('like_allowed_state.txt') == '1' and not bool(status2.in_reply_to_screen_name) and status2.id not in liked_tweets_array:
                                try:
                                    status2.retweeted_status
                                except AttributeError:
                                    try:
                                        status2.favorite()
                                        liked_tweets_array.add(status2.id)
                                        print('success')
                                        break
                                    except tweepy.TweepError as e:
                                        if '429' in str(e.reason):
                                            print('\ncode 429 detected! you probably ran out of daily like limit\n\ndisabling likes for now..')
                                            logger.save('0','like_allowed_state.txt')
                                        if '139' in str(e.reason):
                                            liked_tweets_array.add(status2.id)
                                        else:
                                            print(e.reason)
                                            break
                            if status2_count > 18:
                                print('only retweets so no like for them')
                                break
                except tweepy.TweepError as e:
                    print(e.reason)
            elif logger.read('follow_allowed_state.txt') == '1' and not userid in already_followed_array and screenname != myname:
                try:
                    api.create_friendship(userid)
                    print('followed',username)
                    following_array.add(userid)
                    already_followed_array.add(userid)
                    logger.add_followed(userid)
                except tweepy.TweepError as e:
                    print(e.reason)
                    if '161' in str(e.reason):
                        print('\ncode 161 detected! you probably ran out of daily following limit\n\ndisabling followback for now..')
                        logger.save('0','follow_allowed_state.txt')
        if config.instafollowback_opt and status.event == 'follow':
            if not userid in following_array and not userid in already_followed_array and screenname != myname:
                api.create_friendship(userid)
                print('followback',username)
        #logger.dump(status._json, 'last_streaming_event.txt') #debug


def search_new_followers(followers_array, following_counter, search_phrase, following_now_counter):
    '''finds tweets and follows author if all checks passed (and likes tweet if set)'''
    update_states()
    if logger.read('follow_allowed_state.txt') == '0':
        print('\nfollowing temporarily not allowed! sleeping 5 min..')
        time.sleep(300)
        return 'restart', following_now_counter
    already_checked_array = logger.read_checked()
    already_followed_array = logger.read_followed()
    for status in tweepy.Cursor(api.search, q=search_phrase).items():
        if following_counter >= config.custom_following_limit:
                return 'custom_following_limit_hit', following_now_counter
        elif following_counter >= len(followers_array) + randint(4888,5000):
            sleep_time = randint(18000,36000)
            print('\nfollowing cycle stopped, following hardlimit hit:',len(followers_array),'\nsleeping',sleep_time,'sec..\n')
            time.sleep(sleep_time)
            return 'following_hardlimit_hit',following_now_counter
        elif following_counter >= 4999 and len(followers_array) < 4999:
            sleep_time = randint(18000,36000)
            print('\nfollowing cycle stopped, following hardlimit hit: 5000\nsleeping',sleep_time,'sec..\n')
            time.sleep(sleep_time)
            return 'following_hardlimit_hit',following_now_counter
        try:
            userid = status.user.id
            username = '@'+status.user.screen_name
            if userid in followers_array and not config.followback_opt:
                print('\n',username,'already follows us..')
            elif userid in already_followed_array:
                print('\nalready tried to follow',username,'in the past..')
            elif status.user.following:
                print('\nalready following',username,'(not by script)..')
            else:
                userid_followers_count = status.user.followers_count
                userid_following_count = status.user.friends_count
                if userid_following_count < userid_followers_count - userid_followers_count*0.1:
                    print('\n',username,'doesnt seems like mutual')
                elif userid_followers_count < config.min_followers:
                    print('\n',username,'doesnt have enough followers')
                elif userid_following_count > 200 and userid_following_count > 2*userid_followers_count:
                    print('\n',username,'follows more than 2x his followers')
                elif status.user.default_profile_image or status.user.default_profile:
                    print('\n',username,'not customized profile')
                else:
                    if config.anime_avi_opt:
                        profile_pic = logger.save_profile_pic(status.user.profile_image_url_https.replace('_normal',''))
                    if not config.anime_avi_opt or face_detect.run_face_detection(profile_pic): #detect anime avi
                        status.user.follow()
                        following_now_counter += 1
                        following_counter += 1
                        if not userid in already_followed_array:
                            already_followed_array.add(userid)
                            logger.add_followed(userid)
                        sleep_time = uniform(50,100)
                        print('\nfollowed',username,'| total following:',following_counter,'| followed now:',following_now_counter,'\nsleeping',sleep_time,'sec to avoid detection..')
                        time.sleep(sleep_time)
                    else:
                        print('\n',username,'avi doesnt seems like anime')
                    try:
                        remove(profile_pic)
                    except Exception:
                        pass
                    if config.like_opt and logger.read('like_allowed_state.txt') == '1':
                        status.favorite()
                        print('liked this tweet')
                    time.sleep(sleep_time)
        except tweepy.TweepError as e:
            print(e.reason)
            if '161' in str(e.reason):
                sleep_time = randint(18000,36000)
                print('\ncode 161 detected! you probably ran out of daily following limit\n\nsleeping',sleep_time,'sec before next try..')
                logger.save('0','follow_allowed_state.txt')
                time.sleep(sleep_time)
                return 'restart', following_now_counter
        except StopIteration:
            print('\nwe searched all tweets, sleeping 5 minutes before next try..')
            time.sleep(300)
            return 'restart', following_now_counter
        already_checked_array.add(userid)
    print('following cycle crashed for some reason, restarting in',sleep_time,'sec')
    time.sleep(sleep_time)
    return 'restart', following_now_counter


def steal_followers(following_array, followers_array, myid, following_counter, following_now_counter):
    '''follows people who follow your target'''
    if input('\nWARNING!!1! stealing followers may lead to PERMANENT BAN (tested 06/2k18) use normal following routine instead\n\nbut if youre feeling lucky press y to continue:') != 'y':
        exit()
    update_states()
    if logger.read('follow_allowed_state.txt') == '0':
        print('\nfollowing temporarily not allowed! sleeping 5 min..')
        time.sleep(300)
        return 'restart', following_now_counter
    following_array = set(following_array)
    already_checked_array = logger.read_checked()
    already_followed_array = logger.read_followed()
    target_followers_array = []
    for page in tweepy.Cursor(api.followers_ids, id=input('\nenter username whom followers you wanna steal (without @): ')).pages():
        target_followers_array.extend(page)
        if len(target_followers_array) > 18000:
            break
    for userid in target_followers_array:
        if following_counter >= config.custom_following_limit:
            return 'custom_following_limit_hit', following_now_counter
        elif following_counter >= len(followers_array) + randint(4888,5000):
            sleep_time = randint(18000,36000)
            print('\nfollowing cycle stopped, following hardlimit hit:',len(followers_array),'\nsleeping',sleep_time,'sec..\n')
            time.sleep(sleep_time)
            return 'following_hardlimit_hit',following_now_counter
        elif following_counter >= 4999 and len(followers_array) < 4999:
            sleep_time = randint(18000,36000)
            print('\nfollowing cycle stopped, following hardlimit hit: 5000\nsleeping',sleep_time,'sec..\n')
            time.sleep(sleep_time)
            return 'following_hardlimit_hit',following_now_counter
        followed_state = False
        if userid in already_checked_array:
            print('already checked userid:',userid,'\n')
        elif userid in already_followed_array:
            print('already tried to follow userid:',userid,'\n')
            followed_state = True
        elif userid in following_array:
            print('already following userid:',userid,'\n')
        elif not config.followback_opt and userid in followers_array:
            print('userid already follows us:',userid,'\n')
        else:
            try:
                user = api.get_user(userid)
                userid_followers_count = user.followers_count
                userid_following_count = user.friends_count
                if userid_following_count < userid_followers_count - userid_followers_count*0.1:
                        print(user.screen_name,'doesnt seems like mutual\n')
                elif userid_followers_count < config.min_followers:
                    print(user.screen_name,'doesnt have enough followers\n')
                elif userid_following_count > 200 and userid_following_count > 3*userid_followers_count:
                    print(user.screen_name,'follows more than 3x his followers\n')
                elif user.default_profile_image or user.default_profile:
                    print(user.screen_name,'not customized profile\n')
                elif user.protected:
                    print(user.screen_name,'locked his account\n')
                else:
                    try:
                        for status2 in tweepy.Cursor(api.user_timeline,id=userid).items():
                            if time.mktime(datetime.datetime.strptime(str(status2.created_at), '%Y-%m-%d %H:%M:%S').timetuple()) < time.time() - 24*60*60:
                                print(user.screen_name,'is inactive\n')
                            else:
                                try:
                                    user.follow()
                                    following_counter += 1
                                    following_now_counter += 1
                                    if not userid in already_followed_array:
                                        already_followed_array.add(userid)
                                        logger.add_followed(userid)
                                    followed_state = True
                                    sleep_time = uniform(50,100)
                                    print('followed',user.screen_name,'| total following:',following_counter,'| followed now:',following_now_counter,'\nsleeping',sleep_time,'sec to avoid detection..\n')
                                    time.sleep(sleep_time)
                                except tweepy.TweepError as e:
                                    print(e.reason)
                                    if '161' in str(e.reason):
                                        logger.save('0','follow_allowed_state.txt')
                                        sleep_time = randint(18000,36000)
                                        print('\ncode 161 detected! you probably ran out of daily following limit\n\nsleeping',sleep_time,'sec before next try..')
                                        time.sleep(sleep_time)
                            break
                    except tweepy.TweepError as e:
                        print(e.reason)
            except tweepy.TweepError as e:
                if '63' in str(e.reason):
                    print('user was banned')
        if not followed_state:
            already_checked_array.add(userid)
            logger.add_checked(userid)
    print('successfully checked',len(target_followers_array),'users and followed',following_now_counter,'of them')
    return 'restart', following_now_counter


def unfollow_non_mutuals(following_array,followers_array):
    '''cleans some space for new following'''
    if len(following_array) < 1:
        exit('wtf')
    print('\nstarting unfollowing cycle, lets clean some space for new people..\n')
    if not config.unfollow_nofilter_opt:
        print('no worries, it will unfollow only non mutuals followed by this script from oldest to newest\n')
    already_followed_array = logger.read_followed()
    unfollowing_candidates = []
    for userid in reversed(following_array):
        if not userid in followers_array:
            if config.unfollow_nofilter_opt or userid in already_followed_array:
                unfollowing_candidates.append(userid)
    print(len(unfollowing_candidates),'candidates for unfollow found\n')
    for unfollowed_count,userid in enumerate(unfollowing_candidates, 1):
        sleep_time = uniform(1,10)
        print('user id',userid, 'didnt follow back')
        try:
            api.destroy_friendship(id=userid)
        except tweepy.TweepError as e:
            print(e.reason)
        if config.unfollow_nofilter_opt and not userid in already_followed_array:
            logger.add_followed(userid)
        print('unfollowed him.. total:',unfollowed_count,'\nsleeping',sleep_time,'sec to avoid detection..\n')
        time.sleep(sleep_time)
        if unfollowed_count >= config.custom_unfollowing_limit: #or unfollowed_count > len(unfollowing_candidates)-1000
            sleep_time = randint(3600,7200)
            print('\nunfollowing cycle stopped',unfollowed_count,'users was unfollowed\nsleeping',sleep_time,'sec before another following cycle to avoid detection..\n')
            time.sleep(sleep_time)
            break


def get_tokens():
    '''get temp oauth tokens using ripped off api keys'''
    consumer_key = 'yqoymTNrS9ZDGsBnlFhIuw'
    consumer_secret = 'OMai1whT3sT3XMskI7DZ7xiju5i5rAYJnxSEHaKYvEs'
    REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
    SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri='oob')
    print('\nrequesting temp token from twitter...\n')
    try:
        resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
    except ValueError as e:
        raise 'invalid response from twitter requesting temp token: {0}'.format(e)
    url = oauth_client.authorization_url(AUTHORIZATION_URL)
    print('if nothing happened copy following link to your browser and copypaste PIN to authenticate the bot \n\n',url)
    webbrowser.open(url)
    pincode = input('\nplease enter PIN: ')
    print('\ngenerating and signing request for an access token..')
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret,resource_owner_key=resp.get('oauth_token'),resource_owner_secret=resp.get('oauth_token_secret'),verifier=pincode)
    try:
        resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
    except ValueError as e:
        raise 'invalid response from twitter requesting temp token: {0}'.format(e)
    return resp.get('oauth_token'),resp.get('oauth_token_secret')


def temp_auth(token,token_secret):
    '''set api with temp oauth tokens'''
    auth = tweepy.OAuthHandler('yqoymTNrS9ZDGsBnlFhIuw', 'OMai1whT3sT3XMskI7DZ7xiju5i5rAYJnxSEHaKYvEs')
    auth.set_access_token(token,token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
    return api


def update_states():
    '''check follow/like cooldown'''
    if time.time() - logger.fmtime('like_allowed_state.txt') > 3600:
        logger.save('1','like_allowed_state.txt')
    if time.time() - logger.fmtime('follow_allowed_state.txt') > 14400:
        logger.save('1','follow_allowed_state.txt')


def parse_args(args):
    '''parse CLI arguments'''
    parser = ArgumentParser()
    parser.add_argument('-f', help='steal followers from other accounts',action='store_true')
    parser.add_argument('-s', help='streaming mode which enables instant likefollowback!',action='store_true')
    parser.add_argument('-u', help='clear some space before following',action='store_true')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
