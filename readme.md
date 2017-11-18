# Tagreblogger

Tagreblogger reblogs all the posts in a tag from one Tumblr blog to another,
**while obscuring the source blog.** Created to migrate the 4300+ post #art tag
on my personal blog to a new blog without worrying about people I give the new
blog to finding my personal blog.

It does this by reblogging posts in the following order. Given a post P on a
source blog, Tagreblogger will attempt to reblog the following posts, continuing
to the next post when one is successful.

1. The post the source blog reblogged P from
2. The original source of P
3. An ill-defined reblog trail (I forget what these keys do)
4. Anyone in the notes of P
5. Last resort: the source blog’s P

Usage: `./tagreblogger.py source_blog dest_blog tag [opts]`
