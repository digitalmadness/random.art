
# this script searches tweets with desired hashtag, likes them(optional) and follows author

import tweepy
from pyfiglet import Figlet
from time import sleep
import config

# SETTINGS

search_phrase = '#相互フォロ' #will search tweets containing this word, i recommend using hashtag

following_limit = 9999

follow_those_who_already_follows_you = False

also_like_the_tweet = False

""""""

y = Figlet(font='slant')
print(y.renderText("""autofollow.py"""))

print('logging in..\n')
api = config.api
me = api.me()
myname = me.screen_name
print('welcome, @' + myname + '!\n\nsearching for tweets with',search_phrase,'and following author, will stop after',following_limit,'people followed')
if also_like_the_tweet == True:
    print('like every found tweet option enabled!')
if follow_those_who_already_follows_you == True:
    print('follow those who already follows you option enabled!')
followers_array = api.followers_ids(myname) #fetch array of users who follows us

for tweet in tweepy.Cursor(api.search, q=search_phrase).items(): # <== SET HASHTAG HERE
    try:
        is_following_us_state = False
        already_followed_state = False
        username = tweet.user.screen_name
        print('\nfound tweet by @' + username)
        with open('autofollow_log.txt', 'r') as f:
            already_followed = [line.rstrip('\n') for line in f] #check users who we followed so far from autofollow_log.txt
        for x in already_followed:
            if x == username:
                already_followed_state = True #user was already followed once by script
        for z in followers_array:
            if z == username:
                is_following_us_state = True #user is already following us, no need to waste daily limit
        if is_following_us_state == True and follow_those_who_already_follows_you == False:
            print('user already follows us, skipping..')
        else:
            if tweet.user.following:
                print('already following this user..')
            else:
                if already_followed_state:
                    print('already followed once, skipping..')
                else:
                    if len(already_followed) >= following_limit:
                        print('\nmission completion, this window will close in 5 sec')
                        sleep(5)
                        break
                    tweet.user.follow()
                    print('followed the user, total so far: ' + str(len(already_followed)))
                    if also_like_the_tweet == True:
                        tweet.favorite()
                        print('liked the tweet')
                    with open('autofollow_log.txt', 'a') as log:
                        log.write(tweet.user.screen_name + '\n') #log usernames for future checks
                    sleep(3)
        sleep(0.1)
            

    except tweepy.TweepError as e:
        print('\ntweepy error!\n' + e.reason)
        if '161' in str(e.reason):
            print('\ncode 161 detected! you probably ran out of daily following limit\n\nTWITTER REJECTED FOLLOW\n\ndo not try to follow more people now or u might get banned!\n\nwaiting 10 hours before next try..')
            sleep(10*60*60)

    except StopIteration:
        break