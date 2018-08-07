from bot import config,logger,status
from argparse import ArgumentParser
from sys import argv,exit
from time import sleep
from re import sub
import tweepy
import random


def main():
    '''runs the whole program'''
    args = parse_args(argv[1:])
    auth1 = tweepy.OAuthHandler(config.api_key, config.secret_key)
    auth1.set_access_token(config.token, config.secret_token)
    if args.a:
        auth2 = tweepy.OAuthHandler(config.api_key_alt, config.secret_key_alt)
        auth2.set_access_token(config.token_alt, config.secret_token_alt)
    status.welcome()
    alt = args.a
    e = False
    while True:
        try:
            if args.a and not e:
                alt = not alt #switch accounts
            auth = auth2 if alt else auth1
            api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
            e = post_tweet(api, args.g, alt)
        except Exception as e:
            print(e,'\n\nsomething fucked up, restarting bot in 60 sec..\n\nif it happens after start check if you filled settings.txt correctly')
            sleep(60)
            status.welcome()


def post_tweet(api, gif, alt):
    '''check media state and send tweet'''
    proxify = False
    media_state = 0
    myname = api.me().screen_name
    print('\nlogged in as @' + myname)
    while media_state != 1:
        media,tweetxt,artist,url,media_state,predictions,faces_detected,danbooru_id,media_log = status.media(gif, alt, proxify)
        if media_state == 0: #not_art
            logger.add_post(media_log)
        elif media_state == 11: #api_exceeded
            proxify = True
    if danbooru_id != 0 and media_state != 2:
        post = status.danbooru(danbooru_id) #check metainfo on danbooru.donmai.us
        if post != '':
            '''if (alt and post['rating'] == 's') or (not alt and post['rating'] == 'e'):
                print('rating is unacceptable:',post['rating'],'trying another pic..')
                logger.add_post(media_log)
                return True'''
            copyright = post['tag_string_copyright'].split()
            characters = post['tag_string_character'].split()
            #if artist == '':
            #    artist = post['tag_string_artist'].replace('_', ' ').strip()
            if copyright != '':
                copyright = sub(r'\([^)]*\)', '', copyright[0]) #remove (stuff) from anime_name
                if copyright != 'original' and characters != []:
                    characters = ['{0}'.format(sub(r'\([^)]*\)', '', tag)) for tag in characters] #remove (anime_name) from character_name
                copyright = copyright.replace('_', ' ').strip()
            if characters != []:
                characters = set(['{0}'.format(tag.replace('_', ' ').strip()) for tag in characters])
                duplicate_characters = set([])
                for tag in characters:
                    if next((True for tag2 in characters if tag in tag2 and tag != tag2), False): #search incomplete tags
                        duplicate_characters.add(tag)
                characters = set(characters) - duplicate_characters
                if len(characters) < 5:
                    tweetxt = ', '.join(characters)
                    if copyright != 'original':
                        tweetxt += ' (' + copyright + ')'
            elif copyright != 'original':
                tweetxt = copyright
    elif config.neural_opt and faces_detected:
        waifus = ''
        for waifu in predictions:
            if waifu[1] >= 0.9:
                waifus += waifu[0] + ' (' + str(int(waifu[1]*100)) + '%) '
        if waifus != '':
            tweetxt += ' ' + waifus
    print('uploading pic to twitter..')
    upload_result = api.media_upload(media)
    print('sending tweet as @'+myname+'..')
    api.update_status(
        media_ids=[upload_result.media_id_string],
        status=tweetxt+' '+url)
    logger.add_post(media_log)
    print('ok! sleeping for',config.interval,'s before next tweet..')
    sleep(config.interval)


def parse_args(args):
    '''parse CLI arguments'''
    parser = ArgumentParser()
    parser.add_argument('-a', help='switch between 2 accounts', action='store_true')
    parser.add_argument('-g', help='tweet gifs only', action='store_true')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
