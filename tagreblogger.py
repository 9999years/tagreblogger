import pytumblr
import json

def getClient():
    keys = json.load('keys.json')
    return pytumblr.TumblrRestClient(
        keys['consumer_key'],
        keys['consumer_secret'],
        keys['token'],
        keys['token_secret'],
    )

def get_posts(client, offset, args):
    return client.posts(args.source, tag=args.tag, notes_info='true')

def main():
    import pprint
    import argparse

    argparser = argparse.ArgumentParser(
        description='reblogs all posts in a tag',
        prog='tagreblogger')

    argparser.add_argument('source',
        help='Blog to reblog from. (use "example" for example.tumblr.com)')

    argparser.add_argument('target',
        help='Blog to reblog to')

    argparser.add_argument('tag', nargs='?',
        help='Tag to reblog (# omitted)')

    args = argparser.parse_args()

    client = getClient()

    pp = pprint.PrettyPrinter(indent=4).pprint

    # priority:
    # 1. source
    #   1.blog ['reblogged_root_uuid']
    #   1.id   ['reblogged_root_id']
    # 2. person i reblogged from
    #   2.blog ['reblogged_from_uuid']
    #   2.id   ['reblogged_from_id']
    # 3. rando in the notes
    #   3.key  first item in ['notes'] where 'type' == 'reblog'
    #   3.blog key['blog_uuid']
    #   3.id   key['post_id']
    # 4. me
    #   4.blog ['blog_name']
    #   4.id   ['id']

    offset = 0
    posts = get_posts()
    while posts is not None:
        posts = get_posts(client, offset, args)
