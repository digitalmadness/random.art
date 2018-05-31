from bot import config,logger,status
from argparse import ArgumentParser
from sys import argv,exit
from time import sleep
from re import sub
import tweepy
import random

'''uses all other modules to post tweets if chance is met'''


def main():
    '''runs the whole program'''
    args = parse_args(argv[1:])
    restart = False
    global api
    if args.a:
        auth1 = tweepy.OAuthHandler(config.api_key, config.secret_key)
        auth1.set_access_token(config.token, config.secret_token)
        auth2 = tweepy.OAuthHandler(config.api_key_alt, config.secret_key_alt)
        auth2.set_access_token(config.token_alt, config.secret_token_alt)
    else:
        auth1 = tweepy.OAuthHandler(config.api_key, config.secret_key)
        auth1.set_access_token(config.token, config.secret_token)
    status.welcome()
    alt = args.a
    while True:
        try:
            if args.a and not restart:
                alt = not alt #switch accounts
            if alt:
                api = tweepy.API(auth2, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
            else:
                api = tweepy.API(auth1, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
            restart = post_tweet(args.g, alt)
        except Exception as eeee:
            restart = True
            print(eeee,'\n\nsomething fucked up, restarting bot in 60 sec..\n\nif it happens after start check if you filled settings.txt correctly')
            sleep(60)
            status.welcome()


def post_tweet(gif, alt):
    '''check media state and send tweet'''
    media_state = ''
    proxify = False
    characters = []
    copyright = []
    while media_state != 'art':
        media,tweetxt,media_state,predictions,faces_detected,danbooru_id,temp_img_folder,media_bak = status.media(gif, alt, proxify)
        if media_state == 'not_art':
            logger.add_post(media_bak)
        elif media_state == 'api_exceeded':
            proxify = True
    if danbooru_id != 0:
        post = status.danbooru(danbooru_id)
        if post != '':
            if (alt and post['rating'] == 's') or (not alt and post['rating'] == 'e'):
                print('rating is unacceptable:',post['rating'],'trying another pic..')
                logger.add_post(media_bak)
                return True
            if post['tag_string_character'].split() != []:
                copyright = ['{0}'.format(sub(r'\([^)]*\)', '', tag)) for tag in post['tag_string_copyright'].split()] #removes stuff in brackets
            else:
                copyright = post['tag_string_copyright'].split()
            if copyright != []:
                if copyright[0] != 'original':
                    characters = ['{0}'.format(sub(r'\([^)]*\)', '', tag)) for tag in post['tag_string_character'].split()]
                else:
                    characters = post['tag_string_character'].split()
                copyright = ['{0}'.format(tag.replace('_', ' ')) for tag in copyright] #format source
                copyright = ['{0}'.format(tag.strip()) for tag in copyright]
            if characters != []:
                characters = ['{0}'.format(tag.replace('_', ' ')) for tag in characters] #format characters
                characters = set(['{0}'.format(tag.strip()) for tag in characters])
    if len(characters) > 0:
        duplicate_characters = []
        for tag in characters:
            if next((True for tag2 in characters if tag in tag2 and tag != tag2), False):
                duplicate_characters.append(tag)
        characters = characters - set(duplicate_characters)
        if len(characters) < 5:
            tweetxt += '\n' + ', '.join(characters)
            if copyright != [] and copyright[0] != 'original':
                tweetxt += ' from ' + copyright[0]
        elif copyright != []:
            tweetxt += '\n' + copyright[0]
    elif copyright != [] and copyright[0] != 'original':
        tweetxt += '\n' + copyright[0]
    elif config.neural_opt and faces_detected:
        waifus = ''
        for waifu in predictions:
            if waifu[1] >= 0.9:
                waifus += waifu[0] + ' (' + str(int(waifu[1]*100)) + '%) '
        if waifus != '':
            tweetxt += '\n' + waifus
    status.tweet(media, tweetxt, api, api.me())
    status.cleanup(temp_img_folder)
    logger.add_post(media_bak)
    print('sleeping for',config.interval,'s..')
    sleep(config.interval)


def parse_args(args):
    '''parsing arguments from command line'''
    parser = ArgumentParser()
    parser.add_argument('-a', help='multiaccount', action='store_true')
    parser.add_argument('-g', help='tweet gifs only', action='store_true')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
