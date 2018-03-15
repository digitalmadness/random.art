"""
|￣￣￣￣￣￣￣￣|
| хуяк-хуяк и  |
| v production |
|＿＿＿＿＿＿＿＿|
 ∧＿_∧  ||
(　´ω` )||  
/ 　　づ
"""

import config
import logger
import os
import random
from glob import glob
import sys
import io
import unicodedata
import requests
from PIL import Image
import json
import codecs
import re
import time
from collections import OrderedDict
from pyfiglet import Figlet

"""handles statuses from bot, reverse searches pics and
makes sure it doesn't post anything repeated or pics not found on saucenao (specify how much pics before repeat in config)"""


class Tweet():

    def media(self, folder):
        """pick random image from folder and reverse search it w/ saucenao api"""
        service_name = ''
        part = 0
        creator = ''
        source = ''
        pixiv_id = 0
        deviantart_id = 0
        creator = ''
        author_name = ''
        member_name = ''
        title = ''
        source = ''
        artornot = 'art'
        tweetxt = ''
        ext_urls = ''
        est_time = ''
        minsim='70!'
        api_key_saucenao = config.api_key_saucenao
        media_list = glob(folder + "*")
        media = random.choice(media_list)
        extensions = {".jpg", ".jpeg", ".png", ".gif"}
        thumbSize = (150,150)

        image = Image.open(media)
        image.thumbnail(thumbSize, Image.ANTIALIAS)
        imageData = io.BytesIO()
        image.save(imageData,format='PNG')
            
        url = 'http://saucenao.com/search.php?output_type=2&numres=1&minsim='+minsim+'&db=999&api_key='+api_key_saucenao
        print(url)
        files = {'file': ("image.png", imageData.getvalue())}
        imageData.close()
                        
        processResults = True
        while True:
            r = requests.post(url, files=files)
            if r.status_code != 200: #generally non 200 statuses are due to either overloaded servers, the user being out of searches 429, or bad api key 403
                if r.status_code == 403:
                    print('api key error! enter proper saucenao api key in settings.txt\n\nget it here https://saucenao.com/user.php?page=search-api\n\nexiting in 5sec..')
                    sleep(5)
                    sys.exit(1)
                elif r.status_code == 429:
                    print('request limit exceeded')
                    break
                else:
                    print("status code: "+str(r.status_code))
            else:
                '''f = open('last.saucenao.response.json', 'w') # DEBUG
                f.write(r.text)
                f.close()'''
                results = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(r.text)
                if int(results['header']['user_id'])>0:
                    #api responded
                    print('remaining searches 30s|24h: '+str(results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))
                    if int(results['header']['status'])==0:
                        #search succeeded for all indexes, results usable
                        break
                    else:
                        if int(results['header']['status'])>0:
                            #One or more indexes are having an issue.
                            #This search is considered partially successful, even if all indexes failed, so is still counted against your limit.
                            #The error may be transient, but because we don't want to waste searches, allow time for recovery.
                            print('search is failed, problem w/ saucenao indexes')
                            break
                        else:
                            #Problem with search as submitted, bad image, or impossible request.
                            #Issue is unclear, so don't flood requests.
                            print('search is failed, corrupted image or problem w/ saucenao api')
                            processResults = False
                            break
                else:
                    #General issue, api did not respond. Normal site took over for this error state.
                    #Issue is unclear, so don't flood requests.
                    print('search is failed, corrupted image or saucenao api did not respond')
                    processResults = False
                    break
                
        if processResults:
                            
            if int(results['header']['results_returned']) > 0:
                #one or more results were returned
                if float(results['results'][0]['header']['similarity']) > float(results['header']['minimum_similarity']):
                    print('hit! '+str(results['results'][0]['header']['similarity']))
                    
                    index_id = results['results'][0]['header']['index_id']
                            
                    if index_id == 5 or index_id == 6:
                        #5->pixiv 6->pixiv historical
                        pixiv_id=results['results'][0]['data']['pixiv_id']
                        member_name=results['results'][0]['data']['member_name']
                        title=results['results'][0]['data']['title']
                    elif index_id == 34:
                        deviantart_id=results['results'][0]['data']['da_id']
                        author_name=['results'][0]['data']['author_name']
                        title=results['results'][0]['data']['title']
                    elif index_id == 21: 
                        part=results['results'][0]['data']['part']
                        est_time=results['results'][0]['data']['est_time']
                        source=results['results'][0]['data']['source']
                        ext_urls=results['results'][0]['data']['ext_urls']
                    else:
                        try:
                            pixiv_id=results['results'][0]['data']['pixiv_id']
                        except Exception as eeee:
                            print(eeee)
                        try:
                            ext_urls=results['results'][0]['data']['ext_urls']
                        except Exception as eeee:
                            print(eeee)
                        try:
                            creator=results['results'][0]['data']['creator']
                        except Exception as eeee:
                            print(eeee)
                        try:
                            source=results['results'][0]['data']['source']
                        except Exception as eeee:
                            print(eeee)

                else:
                    print('miss... '+str(results['results'][0]['header']['similarity']))
                    artornot = 'not_art'
                    logger.addPost(media, artornot, config.log_file)
                    return media,tweetxt,artornot
                
            else:
                print('no results... ;_;')
                artornot = 'not_art'
                logger.addPost(media, artornot, config.log_file)
                return media,tweetxt,artornot

            if int(results['header']['long_remaining'])<1: #could potentially be negative
                print('Out of searches for today. Sleeping for 1 hour...')
                time.sleep(1*60*60)
            if int(results['header']['short_remaining'])<1:
                print('out of searches for this 30 second period. sleeping for 25 seconds...')
                time.sleep(25)
                        
        if pixiv_id != 0:
             tweetxt = str(title) + ' by ' + str(member_name) + ' [http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(pixiv_id) + ']'
             return media,tweetxt,artornot
        if deviantart_id != 0:
            tweetxt = str(title) + ' by '+ str(author_name) + ' [https://deviantart.com/view/' + str(deviantart_id) + ']'
            return media,tweetxt,artornot
        if part != 0:
            tweetxt = str(source) + ' ep ' + str(part) + ' ' + str(est_time) + ' ' + str(ext_urls)
            return media,tweetxt,artornot
        if ext_urls != '':
            tweetxt = str(source) + ' by ' + str(creator) + ' ' + str(ext_urls)
            return media,tweetxt,artornot


        return media,tweetxt,artornot


def tweet(tweet_media, tweet_text, reply_id, api):
    """sends tweet command to Tweepy"""
    api.update_with_media(
        filename=tweet_media,
        status=tweet_text,
        in_reply_to_status_id=reply_id)


def is_already_tweeted(log_file, image, tolerance):
    """checks if pic is already tweeted"""
    tolerance = -1 * (tolerance)
    if not os.path.isfile(log_file):
        # if the file doesn't exist just don't bother
        return False
    try:
        already_tweeted = open(log_file, 'r').readlines()[tolerance:]
    except IndexError:
        already_tweeted = open(log_file, 'r').readlines()
    for element in already_tweeted:
        if element.split('\t')[1] == image:
            return True


def welcome():
    y = Figlet(font='slant')
    print(y.renderText("""random art v2"""))
    print('logging in..\n')
    api = config.api
    myid = api.me()
    print('welcome, @' + myid.screen_name + '!\n')
    path, dirs, files = os.walk(config.source_folder).__next__()
    print('tweeting',str(len(files)),'pictures from', config.source_folder, 'every', str(config.interval), 'seconds with', str(config.chance), '% chance..\n')
