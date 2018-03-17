import os
import configparser
import tweepy
"""Reads configuration file and holds all settings for the bot to function."""

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
# read configs from file
config = configparser.ConfigParser()
config.read(dname + '/settings.txt')
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

auth = tweepy.OAuthHandler(api_key, secret_key)
auth.set_access_token(token, secret_token)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
