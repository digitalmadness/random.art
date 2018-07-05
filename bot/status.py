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


def media(gif,alt,proxify):
    faces_detected = False
    media = ''
    service_name = ''
    part = 0
    pixiv_id = 0
    danbooru_id = 0
    member_name = ''
    title = ''
    ext_urls = []
    est_time = ''
    minsim = 70
    predictions = []

    '''pick random image from folder'''
    if alt:
        media_list = glob(config.source_folder_alt + '*')
    else:
        media_list = glob(config.source_folder + '*')
    if gif:
        while not media.lower().endswith(('gif')):
            media = choice(media_list)
    else:
        while not media.lower().endswith(('.png', '.jpg', '.jpeg','gif')):
            media = choice(media_list)
    print('\nopened',media)

    '''check if it was tweeted and size'''
    if media in set(logger.read_posts()):
        print('pic was already tweeted, trying another file..')
        return '','','','',10,'',False,0,''
    if path.getsize(media) < config.discard_size * 1000:
        print(int(path.getsize(media) / 1000),'KB <',config.discard_size,'KB, trying another file..')
        return '','','','',10,'',False,0,''
    media_log = media

    '''run neural network if enabled and installed'''
    neural_opt = config.neural_opt
    if neural_opt:
        try:
            import moeflow
            if not media.lower().endswith(('.gif')):
                predictions,faces_detected = moeflow.neuralnetwork(media)
        except Exception as e:
            print(e,'\nneural network not avaliable! some functions are limited :<')
            neural_opt = False

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
        if proxify:
            r = post('http://saucenao.com/search.php?output_type=2&numres=10&minsim=' + str(minsim) + '!&db=999&api_key=' + config.alt_key_saucenao, files=files, timeout=60, proxies={'http': config.proxy,  'https': config.proxy})
        else:
            r = post('http://saucenao.com/search.php?output_type=2&numres=10&minsim=' + str(minsim) + '!&db=999&api_key=' + config.api_key_saucenao, files=files, timeout=60)
    except Exception as e:
        print(e)
        return media,'','','','api_na','',faces_detected,0,media_log
    if r.status_code != 200:
        if r.status_code == 403:
            exit('\napi key error! enter proper saucenao api key in settings.txt\n\nget it here https://saucenao.com/user.php?page=search-api')
        elif r.status_code == 429:
            if config.proxy != 'socks5://user:password@hostname:port' and config.alt_key_saucenao != '':
                print('\nswitching to another saucenao api key..')
            else:
                print('\nsaucenao.com api rate limit exceeded! pls fill api_key_saucenao_alt and proxy in settings or wait')
            return '','','','',11,'',False,0,''
        else:
            print('saucenao.com api unknown error! status code: '+str(r.status_code))
    else:
        logger.save(r.text,'last_saucenao_response.txt') #debug
        results = JSONDecoder(object_pairs_hook=OrderedDict).decode(r.text) #convert json response to dict
        print('remaining searches 30s|24h: '+str(results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))

    '''check pic metainfo in saucenao.com response'''
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
            while danbooru_id == 0 and result < 10:
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
            while result < 10:
                try:
                    if float(results['results'][result]['header']['similarity']) > minsim:
                        ext_urls = results['results'][result]['data']['ext_urls']
                except Exception:
                    pass
                result += 1
        if ext_urls != []:
            for url in ext_urls:
                if not 'pixiv' in url:
                    cleanup()
                    try:
                        call(['image-scraper',url],timeout=60) #trying to download better quality pic
                    except Exception as e:
                        print(e)
                    if find_biggest() == '':
                        pass
                    elif biggest[1] >= 5242880:
                        unlink(biggest[0])
                        find_biggest()
                        if biggest[1] >= path.getsize(media):
                            media = biggest[0]
                            break
                    elif biggest[1] >= path.getsize(media):
                        print('found better quality pic:',int(biggest[1] / 1000),'KB >',int(path.getsize(media) / 1000),'KB')
                        media = biggest[0]
                        break
    else:
        print('miss... '+str(results['results'][0]['header']['similarity']), '\n\ntrying another pic..')
        return media,'','','',0,'',False,0,media_log
    if path.getsize(media) <= 250000:
        print('low quality, trying another pic..')
        return media,'','','',0,'',False,0,media_log
    if pixiv_id != 0:
        return media,str(title),str(member_name),'https://www.pixiv.net/member_illust.php?mode=medium&illust_id='+str(pixiv_id),1,predictions,faces_detected,danbooru_id,media_log
    elif part != 0:
        return media,str(source) + ' ep. ' + str(part) + ' | timecode: ' + str(est_time),ext_urls[0],2,predictions,faces_detected,danbooru_id,media_log
    else:
        return media,'',ext_urls[0],1,predictions,faces_detected,danbooru_id,media_log


def find_biggest():
    '''filters real pic from all trash on webpage'''
    temp_img_folder = find_temp_media_folder()
    if temp_img_folder == '':
        return ''
    global biggest
    biggest = ('', -1)
    imglist = listdir(temp_img_folder)
    if imglist == []:
        return ''
    for item in imglist:
        item = temp_img_folder + '/' + item
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


def cleanup():
    temp_img_folder = find_temp_media_folder()
    if temp_img_folder != '':
        for file in listdir(temp_img_folder):
            try:
                file_path = path.join(temp_img_folder, file)
                if path.isfile(file_path):
                    unlink(file_path)
            except Exception as e:
                print(e)
        try:
            rmdir(temp_img_folder)
        except Exception as e:
            print(e)


def danbooru(danbooru_id):
    '''returns danbooru post using id'''
    if danbooru_id != 0:
        print('checking details on danbooru.donmai.us')
        try:
            client = Danbooru('danbooru')
            post = client.post_show(danbooru_id)
            logger.dump(post,'last_danbooru_response.txt') #debug
            return post
        except Exception as e:
            print(e)
            return ''


def tweet(tweet_media, tweet_text, api, myname):
    '''sends tweet command to Tweepy'''
    print('uploading pic to twitter..')
    upload_result = api.media_upload(tweet_media)
    print('sending tweet as @'+myname+'..')
    api.update_status(
        media_ids=[upload_result.media_id_string],
        status=tweet_text)


def welcome():
    print(Figlet(font='slant').renderText('''randomart'''),'\nv6.3 | logging in..')
    if config.source_folder == '/replace/with/path_to_pics_folder/':
        exit('\nbaka! edit settings.txt first')
