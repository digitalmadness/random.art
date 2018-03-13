"""
searches tweets with desired hashtag, likes them(optional) and follows author
to enable auto likes remove # before tweet.favorite() in line 39
"""
import tweepy
from pyfiglet import Figlet
from time import sleep
import config

y = Figlet(font='slant')
print(y.renderText("""autofollow.py"""))

auth = tweepy.OAuthHandler(config.api_key, config.secret_key)
auth.set_access_token(config.token, config.secret_token)
api = tweepy.API(auth)
print('logging in..\n')
api = config.api
myid = api.me()
print('welcome, @' + myid.screen_name + '!')

for tweet in tweepy.Cursor(api.search, q='#相互フォロー').items(): # <== SET HASHTAG HERE
    try:
        already_followed_state = False
        username = tweet.user.screen_name
        print('\nTweet by: @' + username)
        with open('autofollow_log.txt', 'r') as f:
            already_followed = [line.rstrip('\n') for line in f]
        for x in already_followed:
            if x == username:
                already_followed_state = True
        if not tweet.user.following:
            if not already_followed_state:
                if len(already_followed) >= 3100: # <== SET FOLLOW LIMIT HERE (increase this daily by no more than 999 so u dont get banned)
                    print('\nmission completion, this window will close in 5 sec')
                    sleep(5)
                    break
                tweet.user.follow()
                print('followed the user, total so far: ' + str(len(already_followed)))
                #tweet.favorite(); print('liked the tweet')                                                          # optionally like tweet
                with open('autofollow_log.txt', 'a') as log:
                    log.write(tweet.user.screen_name + '\n')
                sleep(3)

    except tweepy.TweepError as e:
        print('\ntweepy error!\n' + e.reason)
        if '161' in str(e.reason):
            print('\ncode 161 detected! you probably ran out of daily following limit\n\nTWITTER REJECTED FOLLOW\n\ndo not try to follow more people now or u might get banned!\n\nwaiting 2 hours before next try..')
            sleep(2*60*60)

    except StopIteration:
        break