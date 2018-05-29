from bot import config,logger,status
from argparse import ArgumentParser
from sys import argv,exit
from time import sleep
from re import sub
import random

'''uses all other modules to post tweets if chance is met'''


def main():
    '''runs the whole program'''
    global api  #it's used absolutely everywhere so might as well be global
    api = config.api
    status.welcome()
    args = parse_args(argv[1:])
    restart_code = False
    while True:
        if restart_code or random.random() < config.chance or args.t or args.g:
            try:
                restart_code = post_tweet(args.g)
            except Exception as eeee:
                restart_code = True
                print(eeee,'\n\nsomething fucked up, restarting bot in 60 sec..\n\nif it happens after start check if you filled settings.txt correctly')
                sleep(60)
            if not restart_code:
                if args.t or args.g:
                    exit()
                print('sleeping for',config.interval,'s..')
                sleep(config.interval)
        else:
            print('sleeping for',config.interval,'s..')
            sleep(config.interval)


def post_tweet(gif_arg):
    '''check media state and send tweet'''
    characters = []
    copyright = []
    api = config.api
    media,tweetxt,media_state,predictions,faces_detected,danbooru_id,temp_img_folder,media_bak = status.media(config.source_folder, gif_arg)
    if media_state == 'retry' or media_state == 'not_art':
        if media_state == 'not_art':
            logger.add_post(media_bak)
        return True
    if danbooru_id != 0:
        post = status.danbooru(danbooru_id)
        if post != '':
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
    status.tweet(media, tweetxt, api)
    status.cleanup(temp_img_folder)
    logger.add_post(media_bak)
    return False


def parse_args(args):
    '''parsing arguments from command line'''
    parser = ArgumentParser()
    parser.add_argument('-t', help='force tweet and exit', action='store_true')
    parser.add_argument('-g', help='force tweet GIF and exit', action='store_true')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
