from bot import config,logger
from sys import exit
from os import path,walk,listdir,unlink,rmdir
from requests import post
from json import JSONDecoder
from io import BytesIO
from random import choice
from glob import glob
from PIL import Image
from time import sleep
from collections import OrderedDict
from pyfiglet import Figlet
from pybooru import Danbooru,Moebooru
from subprocess import call


def media(folder,gif_arg):
    '''set vars and pick random image from folder'''
    faces_detected = False
    media = ''
    service_name = ''
    part = 0
    pixiv_id = 0
    danbooru_id = 0
    member_name = ''
    title = ''
    tweetxt = ''
    ext_urls = []
    est_time = ''
    minsim=77
    predictions = []
    media_list = glob(folder + '*')
    if gif_arg:
        while not media.lower().endswith(('gif')):
            media = choice(media_list)
    else:
        while not media.lower().endswith(('.png', '.jpg', '.jpeg','gif')):
            media = choice(media_list)
    print('\nopened',media)

    '''log and size checks'''
    if media in set(logger.read_posts()):
        print('pic was already tweeted, trying another file..')
        return '','','retry','',False,0,'',''
    media_size = int(path.getsize(media))
    if media_size < config.discard_size * 1000:
        print('pic is less than',config.discard_size,'KB, trying another file..')
        return '','','retry','',False,0,'',''
    media_bak = media

    '''run neural network'''
    try:
        import moeflow
        neural_opt = config.neural_opt
    except Exception as e:
        print(e,'\nneural network is not configured!')
        neural_opt = False
    if neural_opt and not media.lower().endswith(('.gif')): #check if neural net enabled and discard gifs
        predictions,faces_detected = moeflow.neuralnetwork(media)

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
    except Exception as e:
        print(e)
        return media,'','api_na','',faces_detected,0,'',media_bak
    if r.status_code != 200: #generally non 200 statuses are due to either overloaded servers, the user being out of searches 429, or bad api key 403
        if r.status_code == 403:
            print('api key error! enter proper saucenao api key in settings.txt\n\nget it here https://saucenao.com/user.php?page=search-api')
            sleep(60*60*24)
        elif r.status_code == 429:
            print('saucenao.com api requests limit exceeded!')
            return media,'','api_key_error','',faces_detected,0,'',media_bak
        else:
            print('saucenao.com api unknown error! status code: '+str(r.status_code))
    else:
        logger.save(r.text,'last_saucenao_response.txt') #debug
        '''analyze saucenao.com response'''
        results = JSONDecoder(object_pairs_hook=OrderedDict).decode(r.text)
        if int(results['header']['user_id'])>0:
            #api responded
            print('remaining searches 30s|24h: '+str(results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))
        else:
            #General issue, api did not respond. Normal site took over for this error state.
            return '','','retry','',False,0,'',''

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
            result = 0
            while pixiv_id == 0 and result < 10:
                try:
                    if float(results['results'][result]['header']['similarity']) > minsim:
                        pixiv_id=results['results'][result]['data']['pixiv_id']
                except Exception:
                    pass
                result += 1
            result = 0
            while result < 10:
                try:
                    if float(results['results'][result]['header']['similarity']) > minsim:
                        ext_urls = results['results'][result]['data']['ext_urls']
                except Exception:
                    pass
                result += 1
        if ext_urls != []:
            print('\ntrying to download better quality pic..')
            for url in ext_urls:
                if not 'pixiv' in url:
                    call(['image-scraper',url])
                    if find_temp_media_folder != '':
                        break
    else:
        print('miss... '+str(results['results'][0]['header']['similarity']), '\n\ntrying another pic..')
        return media,'','not_art','',False,0,'',media_bak
    if int(results['header']['long_remaining'])<1: #could potentially be negative
            print('[saucenao searches limit exceeded]')
            return media,tweetxt,'api_exceeded',predictions,faces_detected,0,'',media_bak
    if int(results['header']['short_remaining'])<1:
            print('out of searches for this 30 second period. sleeping for 25 seconds...')
            sleep(25)
            return '','','retry','',False,0,'',''

    '''check if downloaded pic quality is better'''
    temp_img_folder = find_temp_media_folder()
    find_biggest(temp_img_folder)
    if biggest[1] != -1 and biggest[1] > media_size:
        media = biggest[0]
        print('found better quality pic, using', media)
    elif media_size < 100000:
        print('low quality, trying another pic..')
        return '','','retry','',False,0,'',''


    '''generate tweet text based on that parameters'''
    if pixiv_id != 0:
         tweetxt = str(title) + ' by ' + str(member_name) + '\n[http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(pixiv_id) + ']'
    elif part != 0:
        tweetxt = str(source) + '\nep. ' + str(part) + ' | timecode: ' + str(est_time) + '\n[' + ext_urls[0] + ']'
    elif ext_urls != []:
        tweetxt = '[' + ext_urls[0] + ']'
    return media,tweetxt,'art',predictions,faces_detected,danbooru_id,temp_img_folder,media_bak


def find_biggest(dir):
    global biggest
    biggest = ('', -1)
    for item in listdir(dir):
        item = dir + '/' + item
        if path.isdir(item):
            find_biggest(item)
        else:
            itemsize = path.getsize(item)
            if itemsize > biggest[1]:
                biggest = (item, itemsize)


def find_temp_media_folder():
    work_dir = str(path.dirname(path.abspath(__file__)))
    for file in listdir(work_dir.replace('/bot','')):
        if 'images' in file:
            return work_dir.replace('/bot','/'+file)
    return ''


def cleanup(temp_img_folder):
    for file in listdir(temp_img_folder):
        file_path = path.join(temp_img_folder, file)
        try:
            if path.isfile(file_path):
                unlink(file_path)
        except Exception as e:
            print(e)
    rmdir(temp_img_folder)


def danbooru(danbooru_id):
    '''returns danbooru post using id'''
    if danbooru_id != 0:
        print('\nchecking details on danbooru.donmai.us')
        try:
            client = Danbooru('danbooru')
            #logger.dump(client.post_show(danbooru_id),'last_danbooru_response.txt') #debug
            return client.post_show(danbooru_id)
        except Exception as e:
            print(e)
            return ''


def tweet(tweet_media, tweet_text, api):
    '''sends tweet command to Tweepy'''
    print('uploading pic to twitter..')
    upload_result = api.media_upload(tweet_media)
    print('sending tweet..')
    api.update_status(
        media_ids=[upload_result.media_id_string],
        status=tweet_text)
    print('ok!')


def welcome():
    temp_img_folder = find_temp_media_folder()
    if temp_img_folder != '':
        cleanup(temp_img_folder)
    '''startup message'''
    print(Figlet(font='slant').renderText('''randomartv5'''),'\nlogging in..\n')
    if config.source_folder == '/replace/with/path_to_pics_folder/':
        exit('you forgot to replace default pictures folder in settings.txt!')
    api = config.api
    myid = api.me()
    print('welcome, @'+myid.screen_name+'!\ntweeting pictures from', config.source_folder, 'every', config.interval, 'seconds with', config.chance*100, '% chance..')
