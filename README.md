Butcher Bot
===================================

Moderator bot that performs routine tasks on reddit.com/r/Diablo such as the removal of images/memes and bandwagon-esque titles.

#Setup

Clone and create a file named 'rules.ini' and place it right next to 'auto_mod.py'. You will then need to provide moderator credentials, the subreddit, and the last submission's id inside the file like so: 

```
[DEFAULT]
user = reddit_name
pass = reddit_password
user_agent = Some /r/example modbot [Butcher-Bot, PRAW; contact /u/example]
last_item = 0
last_comment = 0

[images]
type = image		# "image" type does some additional checking deeper than a URL regexp
reddits = example example2
re = (?:\.jpg$|\.png$|\.jpeg$|\.gif$|\.bmp$|quickmeme\.com/|memegenerator\.net/)
comment = Images are prohibited here.
distinguish = true
actions = comment remove

[forbidden title words]
type = title
reddits = example
re = ^(?:badword1|badword2)
comment = Those words are too bad. They're not allowed here.
distinguish = true
actions = comment remove

[auto-report troublesome users for manual review]
type = comment_user
reddits = example
re = ^(?:baduser1|baduser2)
comment = unused
distinguish = unused
actions = report
```

#Dependencies

* PRAW: https://github.com/praw-dev/praw
