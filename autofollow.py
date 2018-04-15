from bot import config,logger 
import tweepy
from random import randint,uniform # +146% to sneaking from twatter bot policy
from time import sleep # +1000% to sneaking
from sys import argv,exit
from pyfiglet import Figlet
from argparse import ArgumentParser
from requests_oauthlib import OAuth1Session
import webbrowser

''' this script searches tweets with desired phrase(configure is settings), likes them(optional) and follows author if all checks passed '''


def main():
    '''run autofollow addon'''
    stream_arg = argument_parser(argv[1:]).s
    unfollow_arg = argument_parser(argv[1:]).u
    print(Figlet(font='slant').renderText('''autofollow'''),'\n\nlogging in..') #welcome message
    token,secret = get_tokens()
    global api
    api = temp_auth(token, secret)
    myid = api.me().id
    global myname
    myname = api.me().screen_name 
    followers_array = []
    for page in tweepy.Cursor(api.followers_ids, id=myid).pages():
        followers_array.extend(page)
    logger.save(followers_array,'followers_backup.txt')
    global following_array
    following_array = []
    global liked_tweets_array
    liked_tweets_array = []
    for page in tweepy.Cursor(api.friends_ids, id=myid).pages():
        following_array.extend(page)
    print('\nwelcome, @' + myname + '!\n\nfollowers:',len(followers_array),'\nfollowing:',len(following_array))
    if stream_arg:
        while True:
            try:
                myStream = tweepy.Stream(auth = api.auth, listener=MyStreamListener())
                print('\nconnected to stream! listening for events..')
                myStream.userstream()
            except Exception as eeee:
                print(eeee,'\n\nsomething fucked up, restarting..')
    else:
        print('\nsearching for tweets with',config.search_phrase,'and following authors with > ',config.min_followers,'followers')
        if config.like_opt:
            print('\nlike every found tweet option enabled!')
        if config.followback_opt:
            print('\nfollow those who already follows you option enabled!')
        stop_code = 'null'
        following_counter = len(following_array)
        following_now_counter = 0
        while True:
            if unfollow_arg or stop_code == 'following_hardlimit_hit':
                if not config.unfollow_opt:
                    print('unfollowing option disabled in settings! this script cant follow more people, exiting now')
                    break
                else:
                    unfollow_subroutine(following_array,followers_array,int(config.custom_unfollowing_limit),following_now_counter)
                    following_now_counter = 0
            nowtime,modtime = logger.fmtime('follow_allowed_state.txt')
            if nowtime - modtime > 14400:
                logger.save('1','follow_allowed_state.txt')
            if logger.read('follow_allowed_state.txt') == '1':
                stop_code,following_now_counter = follow_subroutine(followers_array, following_counter, config.search_phrase, int(config.custom_following_limit), config.followback_opt, config.like_opt, following_now_counter)
            else:
                print('following temporarily disabled! sleeping 5 min to check again..')
                sleep(300)
            if stop_code == 'custom_following_limit_hit':
                print('mission completion! script will exit now')
                break


class MyStreamListener(tweepy.StreamListener):
    def on_event(self, status):
        nowtime,modtime = logger.fmtime('like_allowed_state.txt')
        if nowtime - modtime > 3600:
            logger.save('1','like_allowed_state.txt')
        nowtime,modtime = logger.fmtime('follow_allowed_state.txt')
        if nowtime - modtime > 14400:
            logger.save('1','follow_allowed_state.txt')
        already_followed_array = logger.check_follow()
        source = status._json.get('source')
        userid = int(source.get('id'))
        screenname = str(source.get('screen_name'))
        username = '@'+screenname
        if status.event == 'follow' and userid in already_followed_array and screenname != myname:
            print('\nincoming followback by',username)
        elif screenname != myname:
            print('\nincoming',status.event,'by',username)
        if status.event == 'favorite' or status.event == 'favorited_retweet' and screenname != myname:
            if userid in following_array:
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
                                        liked_tweets_array.append(status2.id)
                                        print('success')
                                        break
                                    except tweepy.TweepError as eeee:
                                        if '429' in str(eeee.reason):
                                            print('\ncode 429 detected! you probably ran out of daily like limit\n\ndisabling likes for now..')
                                            logger.save('0','like_allowed_state.txt')
                                        if '139' in str(eeee.reason):
                                            liked_tweets_array.append(status2.id)
                                        else:
                                            print(eeee.reason)
                                            break
                            if status2_count > 17:
                                print('only retweets so no like for them')
                                break
                except tweepy.TweepError as eeee:
                    print('error while trying to get',username,'tweets!\n',eeee.reason)
            elif logger.read('follow_allowed_state.txt') == '1' and not userid in already_followed_array and screenname != myname:
                try:
                    api.create_friendship(userid)
                    print('followed',username)
                    following_array.append(userid)
                    logger.add_follow(userid)
                except tweepy.TweepError as eeee:
                    print('\ntweepy error!\n' + eeee.reason)
                    if '161' in str(eeee.reason):
                        print('\ncode 161 detected! you probably ran out of daily following limit\n\ndo not try to follow more people now or u might get banned!\n\ndisabling followback for now..')
                        logger.save('0','follow_allowed_state.txt')
        if config.instafollowback_opt and status.event == 'follow':
            if not userid in following_array and not userid in already_followed_array and screenname != myname:
                api.create_friendship(userid)
                print('followback',username)
        logger.dump(status._json, 'last_streaming_event.txt') #debug


def follow_subroutine(followers_array, following_counter, search_phrase, custom_following_limit, followback_opt, like_opt, following_now_counter):
    '''find tweets and follow author if all checks passed (and like tweet if set)'''
    print('\nstarting following subroutine..\nwill stop after',custom_following_limit,'people followed')
    sleep_time_long = randint(18000,36000)
    already_followed_array = logger.check_follow()
    for status in tweepy.Cursor(api.search, q=search_phrase).items():
        if following_counter >= custom_following_limit:
                return 'custom_following_limit_hit', following_now_counter
        sleep_time = uniform(1,2.5)
        if following_counter > 5000:
            if following_counter >= len(followers_array) + randint(980,1000):
                print('\nfollowing subroutine stopped, you are too close to twitter following hardlimit:',len(followers_array),'\nsleeping',sleep_time,'sec before next step to avoid detection..\n')
                sleep(sleep_time)
                return 'following_hardlimit_hit',following_now_counter
            elif len(followers_array) <= 5000:
                print('\nfollowing subroutine stopped, you are too close to twitter following hardlimit: 5000\nsleeping',sleep_time,'sec before next step to avoid detection..\n')
                sleep(sleep_time)
                return 'following_hardlimit_hit',following_now_counter
        try:
            userid = status.user.id
            username = '@'+str(status.user.screen_name)
            print('\nfound tweet by',status.user.name)
            if userid in followers_array and not followback_opt:
                print(username,'already follows us..')
            else:
                if userid in already_followed_array:
                    print('already tried to follow',username,'in the past..')
                else:
                    if status.user.following:
                        print('already following',username,'(not by script)..')
                    else:
                        dood_followers_count = status.user.followers_count
                        dood_following_count = status.user.friends_count
                        if dood_following_count > dood_followers_count - dood_followers_count*0.1 and dood_following_count < 2*dood_followers_count and dood_followers_count > config.min_followers:
                            if logger.read('follow_allowed_state.txt') == '1':
                                status.user.follow()
                                following_now_counter += 1
                                following_counter += 1  # real following counter
                                print('followed',username,'| total following:',following_counter,'| followed now:',following_now_counter,'\nsleeping',sleep_time,'sec to avoid detection..')
                            else:
                                print('following temporarily disabled!')
                            if like_opt:
                                status.favorite()
                                print('liked this tweet')
                            sleep(sleep_time)
                        else:
                            if dood_following_count < dood_followers_count - dood_followers_count*0.1:
                                print(username,'doesnt seems like mutual')
                            if dood_following_count > 2*dood_followers_count:
                                print(username,'follows more than 2x his followers, obviously bot')
                            if dood_followers_count < config.min_followers:
                                print(username,'doesnt have enough followers')
                        already_followed_array.append(userid)
                        logger.add_follow(userid)
        except tweepy.TweepError as eeee:
            print('\ntweepy error!\n' + eeee.reason)
            if '161' in str(eeee.reason):
                print('\ncode 161 detected! you probably ran out of daily following limit\n\ndo not try to follow more people now or u might get banned!\n\nwaiting',sleep_time_long,'sec before next try..')
                logger.save('0','follow_allowed_state.txt')
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
    if len(following_array) < 1000:
        exit('wtf')
    print('\nstarting unfollowing subroutine, lets clean some space for new people..\nno worries, it will unfollow only non mutuals followed by this script from oldest to newest\nwill stop after',custom_unfollowing_limit,'users unfollowed')
    already_followed_array = logger.check_follow()
    unfollowing_candidates = []
    for dood in reversed(following_array):
        if not dood in followers_array:
            if dood in already_followed_array or config.unfollow_filter_opt:
                unfollowing_candidates.append(dood)
    print(len(unfollowing_candidates),'candidates for unfollow\n')
    for unfollowed_count,dood in enumerate(unfollowing_candidates):
        sleep_time = uniform(0.2,1)
        if dood in already_followed_array:
            print('user id ',dood, '(followed by this script) didnt followed you back')
        else:
            print('user id',dood, 'doesnt follow you back')
            logger.add_follow(dood)
        api.destroy_friendship(id=dood)
        print('unfollowed him.. total:',unfollowed_count,'\nsleeping',sleep_time,'sec to avoid detection..\n')
        sleep(sleep_time)
        if unfollowed_count > len(following_array) - len(followers_array) or unfollowed_count >= custom_unfollowing_limit:
            sleep_time_long = randint(3600,7200)
            print('\nunfollowing subroutine stopped',unfollowed_count,'users was unfollowed\nsleeping',sleep_time_long,'sec before another following cycle to avoid detection..\n')
            sleep(sleep_time_long)
            break


def get_tokens():
    '''get temp oauth tokens using twicca api keys'''
    consumer_key = '7S2l5rQTuFCj4YJpF7xuTQ'
    consumer_secret = 'L9VHCXMKBPb2eWjvRvQTOEmOyGlH4W50getaQJPya4'
    REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
    SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri='oob')
    print('\nrequesting temp token from Twitter...\n')
    try:
        resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
    except ValueError as e:
        raise 'Invalid response from Twitter requesting temp token: {0}'.format(e)
    url = oauth_client.authorization_url(AUTHORIZATION_URL)
    print('trying to start a browser to visit the following Twitter page.. if nothing happened, copy the URL to your browser and retrieve PIN to authenticate the bot: \n\n',url)
    webbrowser.open(url)
    pincode = input('\nplease enter your pin code here: ')
    print('\ngenerating and signing request for an access token..')
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret,resource_owner_key=resp.get('oauth_token'),resource_owner_secret=resp.get('oauth_token_secret'),verifier=pincode)
    try:
        resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
    except ValueError as e:
        raise 'invalid response from Twitter requesting temp token: {0}'.format(e)
    return resp.get('oauth_token'),resp.get('oauth_token_secret')


def temp_auth(token,token_secret):
    '''set api with temp oauth tokens'''
    auth = tweepy.OAuthHandler('7S2l5rQTuFCj4YJpF7xuTQ', 'L9VHCXMKBPb2eWjvRvQTOEmOyGlH4W50getaQJPya4')
    auth.set_access_token(token,token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
    return api


def argument_parser(args):
    '''parse CLI arguments'''
    parser = ArgumentParser()
    parser.add_argument('-s', help='streaming mode which enables instant likefollowback!',action='store_true')
    parser.add_argument('-u', help='clear some space before following',action='store_true')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
