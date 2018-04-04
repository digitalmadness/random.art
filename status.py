try:
    import moeflow
except Exception as eeee:
    print(eeee)
import config
from os import path,walk
from requests import post
from json import JSONDecoder,dumps
from io import BytesIO
from random import choice
from glob import glob
from PIL import Image
from time import sleep
from collections import OrderedDict
from pyfiglet import Figlet
from pybooru import Danbooru,Moebooru


'''handles statuses from bot, neural network, reverse searches pics and makes sure it doesn't post anything repeated or not found on saucenao'''


def media(folder,gif_arg):
    '''set vars and pick random image from folder'''
    faces_detected = False
    media = ''
    service_name = ''
    part = 0
    creator = ''
    pixiv_id = 0
    danbooru_id = 0
    member_name = ''
    title = ''
    tweetxt = ''
    ext_urls = []
    est_time = ''
    minsim=77
    predictions = []
    tolerance = -1 * (config.tolerance)
    media_list = glob(folder + '*')
    if gif_arg:
        while not media.lower().endswith(('gif')):
            media = choice(media_list)
    else:
        while not media.lower().endswith(('.png', '.jpg', '.jpeg','gif')):
            media = choice(media_list)
    print('\nopened',media)

    '''run some checks'''
    try:
        already_tweeted = open(config.log_file, 'r').readlines()[tolerance:]
    except IndexError:
        already_tweeted = open(config.log_file, 'r').readlines()
    for element in already_tweeted:
        if element.split('\t')[1] == media:
            print('pic was already tweeted, trying another file..')
            return '','','retry','',False,0
    if int(path.getsize(media)) < int(config.discard_size) * 1000:
        print('pic is less than',config.discard_size,'KB, trying another file..')
        return '','','retry','',False,0

    '''run neural network'''
    if bool(config.neural_opt) and not media.lower().endswith(('.gif')): #check if neural net enabled and discard gifs
        predictions,faces_detected = moeflow.neuralnetwork(media)
        #if not faces_detected: #debug
        #    return '','','retry','',False,0 #debug
        #if len(predictions) <= 1: #debug
        #    return '','','retry','',False,0 #debug
        #for waifu in predictions: #debug
        #    if waifu[1] < 0.77: #debug
        #        return '','','retry','',False,0 #debug

    '''compress pic and upload it to saucenao.com'''
    thumbSize = (150,150)
    image = Image.open(media)
    image.thumbnail(thumbSize, Image.ANTIALIAS)
    imageData = BytesIO()
    image.save(imageData,format='PNG')
    files = {'file': ('image.png', imageData.getvalue())}
    imageData.close()
    print('\nsending pic to saucenao.com')
    try:
        r = post('http://saucenao.com/search.php?output_type=2&numres=10&minsim=' + str(minsim) + '!&db=999&api_key=' + config.api_key_saucenao, files=files, timeout=60)
    except Exception as eeee:
        print(eeee)
        return media,'','api_na','',faces_detected,0
    if r.status_code != 200: #generally non 200 statuses are due to either overloaded servers, the user being out of searches 429, or bad api key 403
        if r.status_code == 403:
            print('api key error! enter proper saucenao api key in settings.txt\n\nget it here https://saucenao.com/user.php?page=search-api')
            sleep(60*60*24)
        elif r.status_code == 429:
            print('saucenao.com api requests limit exceeded!')
            return media,'','api_key_error','',faces_detected,0
        else:
            print('saucenao.com api unknown error! status code: '+str(r.status_code))
    else:
        #with open('last_saucenao_response.txt', 'w') as f: #debug
        #    f.write(r.text) #debug

        '''analyze saucenao.com response'''
        results = JSONDecoder(object_pairs_hook=OrderedDict).decode(r.text)
        if int(results['header']['user_id'])>0:
            #api responded
            print('\nremaining saucenao.com api searches 30s|24h: '+str(results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))
        else:
            #General issue, api did not respond. Normal site took over for this error state.
            return '','','retry','',False,0

    '''check pic parameters in saucenao.com response'''
    if float(results['results'][0]['header']['similarity']) > minsim:
        print('hit! '+str(results['results'][0]['header']['similarity']+' analyzing response..'))
        index_id = results['results'][0]['header']['index_id']
        if index_id == 21: 
            part=results['results'][0]['data']['part']
            est_time=results['results'][0]['data']['est_time']
            source=results['results'][0]['data']['source']
            ext_urls=results['results'][0]['data']['ext_urls']
        else:
            result = 0
            while danbooru_id == 0 and  result < 10:
                try:
                    if float(results['results'][result]['header']['similarity']) > minsim:
                        danbooru_id=results['results'][result]['data']['danbooru_id']
                except Exception:
                    pass
                result += 1
            if index_id == 5 or index_id == 6:
                pixiv_id=results['results'][0]['data']['pixiv_id']
                member_name=results['results'][0]['data']['member_name']
                title=results['results'][0]['data']['title']
            else:
                result = 0
                while pixiv_id == 0 and result < 10:
                    try:
                        if float(results['results'][result]['header']['similarity']) > minsim:
                            pixiv_id=results['results'][result]['data']['pixiv_id']
                    except Exception:
                        pass
                    result += 1
                result = 0
                while ext_urls == [] and result < 10:
                    try:
                        if float(results['results'][result]['header']['similarity']) > minsim:
                            ext_urls=results['results'][result]['data']['ext_urls']
                            try:
                                creator = results['results'][result]['data']['creator']
                            except Exception:
                                pass
                    except Exception:
                        pass
                    result += 1
    else:
        print('miss... '+str(results['results'][0]['header']['similarity']), '\n\ntrying another pic..')
        return '','','retry','',False,0
    if int(results['header']['long_remaining'])<1: #could potentially be negative
            print('[saucenao searches limit exceeded]')
            return media,tweetxt,'api_exceeded',predictions,faces_detected,0
    if int(results['header']['short_remaining'])<1:
            print('out of searches for this 30 second period. sleeping for 25 seconds...')
            sleep(25)
            return '','','retry','',False,0

    '''generate tweet text based on that parameters'''
    if pixiv_id != 0:
         tweetxt = str(title) + ' by ' + str(member_name) + '\n[http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(pixiv_id) + ']'
    elif part != 0:
        tweetxt = str(source) + '\nep. ' + str(part) + '| timecode: ' + str(est_time) + '\n[' + ext_urls[0] + ']'
    elif ext_urls != []:
        if creator != '':
            tweetxt = 'by ' + str(creator) + '\n[' + ext_urls[0] + ']'
        else:
            tweetxt = '[' + ext_urls[0] + ']'
    return media,tweetxt,'art',predictions,faces_detected,danbooru_id


def danbooru(danbooru_id):
    if danbooru_id != 0:
        client = Danbooru('danbooru')
        print('\nchecking details on danbooru.donmai.us')
        try:
            #with open('last_danbooru_response.txt', 'w') as f: #debug
            #    f.write(dumps(client.post_show(danbooru_id)))  #debug
            return client.post_show(danbooru_id)
        except Exception as eeee:
            print(eeee)


def tweet(tweet_media, tweet_text, api):
    '''sends tweet command to Tweepy'''
    api.update_with_media(
        filename=tweet_media,
        status=tweet_text)
    print('\ntweet sent!')


def welcome():
    '''startup message'''
    fi = Figlet(font='slant')
    print(fi.renderText('''randomartv5'''),'\nlogging in..\n')
    api = config.api
    myid = api.me()
    print('welcome, @'+myid.screen_name+'!\ntweeting pictures from', config.source_folder, 'every', config.interval, 'seconds with', config.chance, '% chance..')
