Butcher Bot
===================================

Moderator bot that performs routine tasks on reddit.com/r/Diablo such as the removal of images/memes and bandwagon-esque titles.

#Setup

Clone and create a file named 'rules.ini' and place it right next to 'autoMod.py'. You will then need to provide moderator credentials, the subreddit, and the last submission's id inside the file like so: 

```
[DEFAULT]
user = reddit_name
pass = reddit_password
reddits = mysubreddit1 mysubreddit1
last_item = ronct

[images]
type = url
re = ((.*\.jpg)|(.*\.png)|(.*\.jpeg)|(.*\.gif)|(.*\.bmp)|(.*qkme\.me/.*)|(.*quickmeme\.com/.*)|(.*memegenerator\.net/.*)|(.*troll\.me/.*)|(.*memebase\.com/.*)|(.*knowyourmeme\.com/.*)|(.*9gag\.com/.*)|(.*funnyjunk\.com/.*)|(.*icanhascheezburger\.com/.*)|(.*cheezburger\.com/.*)|(.*imgur\.com/.*)|(.*min\.us/.*)|(.*imageshack\.us/.*)|(.*photobucket\.com/.*)|(.*tinypic\.com/.*)|(.*deviantart\.com/.*)|(.*flickr\.com/.*))
comment = Images and memes are automatically removed from [r/Diablo](http://www.reddit.com/r/Diablo) to ensure a high-quality experience for everyone.\n\n**Please link your image again in a text-only self-post with more information about it, so people can enjoy as well as discuss the image.** An example of a self image post would include a riveting title, a link to the image inside, and a description varying from when it was taken, what it is, why you like it, and similar things.\n\nIf your image is a meme, ragecomic or something similar, you should try to post it to [r/Diablofunny](http://www.reddit.com/r/Diablofunny), where content like this is accepted and wanted. **Not specifically funny, but in general less serious content is also definitely a go for [r/Diablofunny](http://www.reddit.com/r/Diablofunny)!**\n\nThank you for your understanding, and thanks for being a member of this subreddit!
distinguish = true

[acronym]
type = title
re = ((DAE)|(Does Everyone Else)|(PSA)|(Public Service Announcement)|(FYI)|(For Your Information)|(Am I The Only One)).*
comment = Titles containing DAE, PSA, FYI and their expansions are automatically removed from [r/Diablo](http://www.reddit.com/r/Diablo) to ensure a high-quality experience for everyone.\n\n**Please try to think another way to write down the title without using these acronyms and their expansions.** We are trying to cut down on the bandwagon effect and encourage a more healthy discussion.\n\nThank you for your understanding, and thanks for being a member of this subreddit!
distinguish = true
```

* It is highly reccomended that you use a bot account (dummy account)

#Module Requirements

* PRAW: https://github.com/praw-dev/praw
