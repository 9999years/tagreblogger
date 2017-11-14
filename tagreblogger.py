import pytumblr
import json
import sys

client = None
POSTS_PER_PAGE = 20
_offset = 0

# def get_pp():
    # global pp
    # if pp is None:
        # pprint.PrettyPrinter(indent=4).pprint
    # return pp

def simple_pp(obj):
    pass

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

def percent(n):
    return '{: > 8.3f}%'.format(n * 100.0)

def get_status(response):
    if 'meta' in response and 'status' in response['meta']:
        return response['meta']['status']
    else:
        return 200

def try_post(blog_uuid, post_id):
    post = get_client().posts(blog_uuid, id=post_id)
    status = get_status(post)
    if status == 404:
        return None
    elif status == 200:
        return post
    else:
        try_status(status=status)

def try_continue(error=None, verbose=None):
    global _offset
    if error is not None:
        print(error)#, file=sys.stderr)
    while True:
        response = input('Continue? [y/n/v] ').strip().lower()
        if response == 'y':
            return
        elif response == 'v':
            if verbose is None:
                print('No verbose information available!')
            else:
                print(verbose)
        elif response == 'n':
            print(f'Exiting! continue with --offset {_offset}')
            exit()
        else:
            print('Invalid response; Try again!')

def try_status(response=None, status=None):
    if status is None:
        status = get_status(response)
    if status != 200:
        try_continue(f'Reblogging failed with status {status}!', response)

def get_posts(source, tag, offset=0, **kwargs):
    global POSTS_PER_PAGE
    posts = get_client().posts(source, tag=tag, reblog_info='true',
        notes_info='true', offset=offset,
        limit=POSTS_PER_PAGE, **kwargs)
    try_status(posts)
    return posts

def posts_in_tag(source, tag):
    global POSTS_PER_PAGE
    posts = get_client().posts(source, tag=tag)
    try_status(posts)
    return posts['total_posts']

def reblog_one(target, post):
    def reblog(blog_uuid, post_id, reblog_key=None):
        nonlocal target
        nonlocal post
        nonlocal num_requests

        if reblog_key is None:
            num_requests += 1
            try_post_response = try_post(blog_uuid, post_id)
            if try_post_response is None:
                # print(f'posts({blog_uuid}, id={post_id}) not found!')
                return False
            try_post_post = try_post_response['posts'][0]
            reblog_key = try_post_post['reblog_key']

        num_requests += 1
        print(f'reblogging https://{blog_uuid}/post/{post_id}')
        try_status(get_client().reblog(
            id=post_id,
            reblog_key=reblog_key,
            blogname=target,
            tags=post['tags']))

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
        return num_requests
    if reblog(post['reblogged_from_uuid'], post['reblogged_from_id']):
        return num_requests
    for note in post['notes']:
        # TODO have this request more notes
        if note['type'] == 'reblog':
            if reblog(note['blog_uuid'], note['post_id']):
                return num_requests
    print('reblogging my own post; last resort!')
    if not reblog(post['blog_name'], post['id'], reblog_key=post['reblog_key']):
        raise OSError('reblogging my own post failed???')
    return num_requests

def reblog_all(source, target, tag, offset=0, max_posts=1000):
    global POSTS_PER_PAGE
    global _offset
    _offset = offset
    i = 0
    total = -1
    iteration = 0

    total = posts_in_tag(source, tag)
    # move from total - offset to total - offset - max_posts
    while i < max_posts:
        posts = get_posts(source, tag, total - POSTS_PER_PAGE - offset - i)
        processed = i + offset
        percent_finished = processed / total
        print(f'{processed} / {total} posts, '
            f'requested set {iteration}'
            f'\t\t\t({percent(percent_finished)}).')
        for post in reversed(posts['posts']):
            reblog_one(target, post)
            i += 1
            _offset = offset + i
            if i >= max_posts:
                break
        iteration += 1
    print(f'finished! reached max posts; continue with --offset {offset + i}')

def main():
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

    argparser.add_argument('--offset', type=int, default=0,
        help='post offset (useful if rate-limited)')

    argparser.add_argument('--max-posts', type=int, default=1000,
        help='max posts to make; useful for rate-limiting')

    args = argparser.parse_args()

    reblog_all(args.source, args.target, args.tag,
        max_posts=args.max_posts,
        offset=args.offset)

if __name__ == '__main__':
    main()
