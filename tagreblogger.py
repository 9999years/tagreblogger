import pytumblr
import json

client = None
pp = None

def get_pp():
    global pp
    if pp is None:
        pprint.PrettyPrinter(indent=4).pprint
    return pp

def get_client():
    global client
    if client is None:
        with open('keys.json') as keys_file:
            keys = json.load(keys_file)
            client = pytumblr.TumblrRestClient(
                keys['consumer_key'],
                keys['consumer_secret'],
                keys['token'],
                keys['token_secret'],
            )
    return client

def get_posts(source, tag, offset=0, **kwargs):
    return get_client().posts(source, tag=tag, reblog_info='true',
            notes_info='true', offset=offset,
            limit=20, **kwargs)

def try_post(blog_uuid, post_id):
    post = get_client().posts(blog_uuid, id=post_id)
    if ('meta' in post
        and 'status' in post['meta']
        and post['meta']['status'] == 404):
        return None
    else:
        return post

def reblog_one(target, post):
    def reblog(blog_uuid, post_id, reblog_key=None):
        nonlocal target
        nonlocal post
        nonlocal num_requests

        if reblog_key is None:
            num_requests += 1
            try_post_response = try_post(blog_uuid, post_id)
            if post_response is None:
                return False
            try_post = try_post_response['posts'][0]
            reblog_key = try_post['reblog_key']

        num_requests += 1
        client.reblog(
            id=post_id,
            reblog_key=reblog_key,
            blogname=target,
            tags=post['tags'])

        return True
    num_requests = 0
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
    if reblog(post['reblogged_root_uuid'], post['reblogged_root_id']):
        pass
    elif reblog(post['reblogged_from_uuid'], post['reblogged_from_id']):
        pass
    else:
        for note in post['notes']:
            # TODO have this request more notes
            if note['type'] == 'reblog':
                if reblog(post['blog_uuid'], post['post_id']):
                    break
        if not reblog(post['blog_name'], post['id'], reblog_key=post['reblog_key']):
            raise OSError('reblogging my own post failed???')
    return num_requests


def reblog_all(source, target, tag, offset=0, max_posts=1000):
    i = 0
    total = -1
    iteration = 0
    while i < max_posts:
        posts = get_posts(source, tag, offset + i)
        total = posts['total_posts']
        remaining = total - i - offset
        percent = 100.0 * remaining / total
        print(f'{total} total posts, '
            f'{remaining} remaining, iteration {iteration} \t\t\t('
            f'{percent: > 8.3f}%).'
        for post in posts['posts']:
            reblog_one(target, post)
            i += 1
        iteration += 1

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

    argparser.add_argument('--offset', type=int,
        help='post offset (useful if rate-limited)')

    argparser.add_argument('--max-posts', type=int,
        help='max posts to make; useful for rate-limiting')

    args = argparser.parse_args()

    offset = 0
    posts = get_posts()
    while posts is not None:
        posts = get_posts(args.source, args.tag)
