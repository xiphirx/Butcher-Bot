Butcher Bot
===================================

Moderator bot that performs routine tasks on reddit.com/r/Diablo such as the removal of images/memes and bandwagon-esque titles.

#Setup

Clone and create a file named 'config.cfg' and place it right next to 'autoMod.py'. You will then need to provide moderator credentials, the subreddit, and the last submission's id inside the file like so: 

```
moderator's username
moderator's password
subreddit
last submission id (/comments/[id you need]/[Title of post]/)
```

* It is highly reccomended that you use a bot account (dummy account)

Example config file:

```
Xiphirx
mysupersecretpassword12345
diablo
ug2p2
```

#Module Requirements

* PRAW: https://github.com/praw-dev/praw