import os
import configparser
import tweepy
import codecs
from sys import exit

"""reads configuration file and holds all settings for the bot to function. get out of here stalker, edit settings.txt"""

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
# read configs from file
config = configparser.ConfigParser()
config.readfp(codecs.open('settings.txt','r',encoding='utf8'))
twitter_config = config['Twitter']
saucenao_config = config['Saucenao']
app_config = config['App']
autofollow_config = config['Autofollow']
try:
	api_key = twitter_config['api_key']
	secret_key = twitter_config['secret_key']
	token = twitter_config['token']
	secret_token = twitter_config['secret_token']
except:
	exit('error reading twitter api keys from settings.txt! make sure you filled it corrrectly')
source_folder = app_config['image_folder']
if source_folder == '/replace/with/path_to_pics_folder/':
	exit('you forgot to replace default pictures folder in settings.txt!')
discard_size = app_config['discard_pic_if_less_than_x_kilobytes']
log_file = app_config['log_file']
try:
	tolerance = int(app_config['allow_repeat_after'])
	chance = int(app_config['execution_chance'])
	interval = int(app_config['time_between_tweets'])
	min_followers = int(autofollow_config['minimum_followers_to_consider'])
except:
	print('only numbers are supported in tolerance, chance, interval, min_followers fields in settings.txt!\nusing default..')
	tolerance = 999
	chance = 5
	interval = 60
	min_followers = 500
api_key_saucenao = saucenao_config['api_key_saucenao']
search_phrase = autofollow_config['search_phrase']
try:
	custom_following_limit = autofollow_config['custom_following_limit']	
	custom_unfollowing_limit = autofollow_config['custom_unfollowing_limit']
except:
	print('only numbers are supported in custom_following_limit, custom_unfollowing_limit fields in settings.txt!\nusing 999999 as both..')
	custom_following_limit = 999999
	custom_unfollowing_limit = 999999
try:
	neural_opt = int(app_config['enable_neural_network'])
	unfollow_opt = int(autofollow_config['enable_unfollow'])
	followback_opt = int(autofollow_config['follow_those_who_already_follow_you'])
	like_opt = int(autofollow_config['like_all_found_tweets'])
except:
	neural_opt = app_config['enable_neural_network']
	unfollow_opt = autofollow_config['enable_unfollow']
	followback_opt = autofollow_config['follow_those_who_already_follow_you']
	like_opt = autofollow_config['like_all_found_tweets']
autofollow_log_file = autofollow_config['autofollow_log_file']

auth = tweepy.OAuthHandler(api_key, secret_key)
auth.set_access_token(token, secret_token)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
