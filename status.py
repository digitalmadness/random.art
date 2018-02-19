"""
|￣￣￣￣￣￣￣￣|
| хуяк-хуяк и  |
| v production |
|＿＿＿＿＿＿＿＿|
 ∧＿_∧  ||
(　´ω` )||  
/ 　　づ
"""

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

"""handles statuses from bot, reverse searches pics and
makes sure it doesn't post anything repeated (specify how much pics before repeat in config)"""


class Tweet():

    def media(self, folder):
        """pick random image from folder and reverse search it w/ saucenao api"""
        api_key="replacewithapikey"
        minsim='80!'
        media_list = glob(folder + "*")
        media = random.choice(media_list)
        extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        thumbSize = (150,150)
        picid = 0;

        #left them in case u want to integrate that services too
        index_hmags='0'
        index_hanime='0'
        index_hcg='0'
        index_ddbobjects='0'
        index_ddbsamples='0'
        index_pixiv='1'
        index_pixivhistorical='1'
        index_anime='0'
        index_seigaillust='0'
        index_danbooru='1'
        index_drawr='0'
        index_nijie='0'
        index_yandere='0'

        #generating bitmask
        db_bitmask = int(index_yandere+index_nijie+index_drawr+index_danbooru+index_seigaillust+index_anime+index_pixivhistorical+index_pixiv+index_ddbsamples+index_ddbobjects+index_hcg+index_hanime+index_hmags,2)

        image = Image.open(media)
        image.thumbnail(thumbSize, Image.ANTIALIAS)
        imageData = io.BytesIO()
        image.save(imageData,format='PNG')
            
        url = 'http://saucenao.com/search.php?output_type=2&numres=1&minsim='+minsim+'&dbmask='+str(db_bitmask)+'&api_key='+api_key
        print(url)
        files = {'file': ("image.png", imageData.getvalue())}
        imageData.close()
                        
        processResults = True
        while True:
            r = requests.post(url, files=files)
            if r.status_code != 200: #generally non 200 statuses are due to either overloaded servers, the user being out of searches 429, or bad api key 403
                if r.status_code == 403:
                    print('api key error! setup proper api key from https://saucenao.com/ to continue')
                    sys.exit(1)
                elif r.status_code == 429:
                    print('request limit exceeded')
                    break
                else:
                    print("status code: "+str(r.status_code))
            else:
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
            #print(results)
                            
            if int(results['header']['results_returned']) > 0:
                #one or more results were returned
                if float(results['results'][0]['header']['similarity']) > float(results['header']['minimum_similarity']):
                    print('hit! '+str(results['results'][0]['header']['similarity']))

                    #get vars to use
                    service_name = ''
                    illust_id = 0
                    try:
                        member_id = results['results'][0]['data']['member_id']
                    except KeyError:
                        print('pixiv id not found')
                    finally:
                        index_id = results['results'][0]['header']['index_id']
                        page_string = ''
                        page_match = re.search('(_p[\d]+)\.', results['results'][0]['header']['thumbnail'])
                            
                    if page_match:
                        page_string = page_match.group(1)
                        
                    if index_id == 5 or index_id == 6:
                        #5->pixiv 6->pixiv historical
                        service_name='pixiv'
                        illust_id=results['results'][0]['data']['pixiv_id']
                    elif index_id == 8: 
                        #8->danbooru
                        service_name='danbooru'
                        try:
                            illust_id=results['results'][0]['data']['danbooru_id']
                        except KeyError:
                            print('pixiv id not found on danbooru')
                    
                    else:
                        #unknown error
                        print('something happened')
                    picid = illust_id
                    print('pixiv id: ', picid)
                
                else:
                    print('miss... '+str(results['results'][0]['header']['similarity']))
                
            else:
                print('no results... ;_;')

            if int(results['header']['long_remaining'])<1: #could potentially be negative
                print('Out of searches for today. Sleeping for 1 hour...')
                time.sleep(1*60*60)
            if int(results['header']['short_remaining'])<1:
                print('out of searches for this 30 second period. sleeping for 25 seconds...')
                time.sleep(25)
                        
        print('tweeting file:', media)
        f = open('last.kartinko.id', 'w')
        if picid != 0:
            f.write('http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(picid))
        else:
            picname = os.path.splitext(os.path.basename(media))[0]
            if len(picname) == 32: #trying to guess by checking if filename is md5, because i have many pics downloaded from danbooru
                f.write('https://danbooru.donmai.us/posts?tags=md5%3A' + picname)
                print('pic probably from danbooru')
            else:
                f.write('')
        f.close()
        return media

    def text(self, text):
        """left it in case u want to customuze text"""
        f = open('last.kartinko.id', 'r')
        text = f.read()
        f.close()
        return text


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
