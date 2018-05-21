from bot import config,logger,status
from argparse import ArgumentParser
from sys import argv
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
    if args.g:
        gif_arg = args.g
    else:
        gif_arg = False
    while True:
        if random.random() < config.chance or args.t or gif_arg:
            try:
                post_tweet(gif_arg)
            except Exception as eeee:
                print(eeee,'\n\nsomething fucked up, restarting bot in 60 sec..\n\nif it happens after start check if you filled settings.txt correctly')
                sleep(60)
                main()
            if args.t or gif_arg:
                break
        print('sleeping for',config.interval,'s..')
        sleep(config.interval)


def post_tweet(gif_arg):
    '''check media state and send tweet'''
    characters = []
    copyright = []
    api = config.api
    media,tweetxt,media_state,predictions,faces_detected,danbooru_id = status.media(config.source_folder, gif_arg)
    tolerance = config.tolerance
    if media_state == 'retry' or media_state == 'not_art':
        if media_state == 'not_art':
            logger.add_post(media, media_state)
        return post_tweet(gif_arg)  # just try again
    if danbooru_id != 0:
        post = status.danbooru(danbooru_id)
        characters = ['{0}'.format(sub(r'\([^)]*\)', '', tag)) for tag in post['tag_string_character'].split()] #regex to remove everything in brackets
        characters = ['{0}'.format(tag.replace('_', ' ')) for tag in characters] #format characters
        characters = ['{0}'.format(tag.strip()) for tag in characters]
        characters = set(characters)
        copyright = ['{0}'.format(tag.replace('_', ' ')) for tag in post['tag_string_copyright'].split()] #format source
    if len(characters) != 0:
        tweetxt += '\n' + ', '.join(characters)
    elif config.neural_opt and faces_detected:
        waifus = ''
        for waifu in predictions:
            if waifu[1] >= 0.9:
                waifus += waifu[0] + ' (' + str(int(waifu[1]*100)) + '%) '
        if waifus != '':
            tweetxt += '\n' + waifus
    if copyright != [] and copyright[0] != 'original':
        tweetxt += ' from ' + copyright[0]
    status.tweet(media, tweetxt, api)
    logger.add_post(media, media_state)


def parse_args(args):
    '''parsing arguments from command line'''
    parser = ArgumentParser()
    parser.add_argument('-t', help='force tweet and exit', action='store_true')
    parser.add_argument('-g', help='force tweet GIF and exit', action='store_true')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
