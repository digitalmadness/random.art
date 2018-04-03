import config
import status
import logger
import random
import argparse
import sys
from time import sleep

"""uses all other modules to post tweets if chance is met calls logger and parses arguments"""


def main():
    """runs the whole program"""
    global api  #it's used absolutely everywhere so might as well be global
    api = config.api
    status.welcome()
    args = parse_args(sys.argv[1:])
    if args.g:
        gif_arg = args.g
    else:
        gif_arg = False
    while True:
        if random.randint(0, 99) < config.chance or args.t or gif_arg:
            try:
                post_tweet(gif_arg)
            except Exception as eeee:
                print(eeee)
                print ('something fucked up, restarting bot in 60 seconds..\n\nif this happens right after start pls check if you filled settings.txt correctly\nor contact https://twitter.com/digitaImadness')
                sleep(60)
                main()
            if args.t or gif_arg:
                break
        else:
            print('sleeping for',config.interval,'s..')
        sleep(config.interval)


def post_tweet(gif_arg):
    """sending tweet"""
    api = config.api
    media,tweetxt,media_state,predictions = status.media(config.source_folder,gif_arg)
    log = config.log_file
    tolerance = config.tolerance
    if media_state == 'old' or media_state == 'not_art' or media_state == 'low_quality':
        if media_state == 'not_art':
            logger.addPost(media, media_state, config.log_file)
        return post_tweet(gif_arg)  # just try again
    if bool(config.neural_opt):
        if len(predictions) == 1:
            tweetxt = tweetxt + '\nface recognized'
        elif len(predictions) > 1:
            tweetxt = tweetxt + '\n' + str(len(predictions)) + ' faces recognized'
        for waifu in predictions:
            print(waifu[0],waifu[1])
            accuracy = waifu[1]
            if accuracy > 0.77:
                tweetxt = tweetxt + ': ' + waifu[0] + ' (' + str(int(accuracy*100)) + '%) '
        if tweetxt.endswith('%) '):
            tweetxt = tweetxt + 'via neural network'
        else:
            pass #placeholder for danbooru tags recognition
    status.tweet(media, tweetxt, api)
    logger.addPost(media, media_state, config.log_file)


def parse_args(args):
    """parsing arguments from command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", help="manual tweet",
                        action="store_true")
    parser.add_argument("-g", help="manual tweet GIF",
                        action="store_true")
    return parser.parse_args(args)


if __name__ == "__main__":
    main()
