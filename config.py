import os
import configparser
import tweepy
import codecs

"""reads configuration file and holds all settings for the bot to function. get out of here stalker, edit settings.txt"""

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
# read configs from file
config = configparser.ConfigParser()
config.readfp(codecs.open('settings.txt','r',encoding='utf8'))
twitter_config = config['Twitter']
api_key = twitter_config['api_key']
secret_key = twitter_config['secret_key']
token = twitter_config['token']
secret_token = twitter_config['secret_token']
app_config = config['App']
source_folder = app_config['image_folder']
log_file = app_config['log_file']
tolerance = int(app_config['allow_repeat_after'])
chance = int(app_config['execution_chance'])
interval = int(app_config['time_between_tweets'])
saucenao_config = config['Saucenao']
api_key_saucenao = saucenao_config['api_key_saucenao']
autofollow_config = config['Autofollow']
search_phrase = autofollow_config['search_phrase']
custom_following_limit = autofollow_config['custom_following_limit']
followback_opt = autofollow_config['follow_those_who_already_follow_you']
like_opt = autofollow_config['like_all_found_tweets']

auth = tweepy.OAuthHandler(api_key, secret_key)
auth.set_access_token(token, secret_token)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
