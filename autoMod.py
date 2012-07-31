import praw
import urllib
import re
import time

class butcherBot:
	imageRules = [re.compile('((.*\.jpg)|(.*\.png)|(.*\.jpeg)|(.*\.gif)|(.*\.bmp)|(.*qkme\.me/.*)|(.*quickmeme\.com/.*)|(.*memegenerator\.net/.*)|(.*troll\.me/.*)|(.*memebase\.com/.*)|(.*knowyourmeme\.com/.*)|(.*9gag\.com/.*)|(.*funnyjunk\.com/.*)|(.*icanhascheezburger\.com/.*)|(.*cheezburger\.com/.*)|(.*imgur\.com/.*)|(.*min\.us/.*)|(.*imageshack\.us/.*)|(.*photobucket\.com/.*)|(.*tinypic\.com/.*)|(.*deviantart\.com/.*)|(.*flickr\.com/.*))'), \
							'Images and memes are automatically removed from [r/Diablo](http://www.reddit.com/r/Diablo) to ensure a high-quality experience for everyone.\n\n**Please link your image again in a text-only self-post with more information about it, so people can enjoy as well as discuss the image.** An example of a self image post would include a riveting title, a link to the image inside, and a description varying from when it was taken, what it is, why you like it, and similar things.\n\nIf your image is a meme, ragecomic or something similar, you should try to post it to [r/Diablofunny](http://www.reddit.com/r/Diablofunny), where content like this is accepted and wanted. **Not specifically funny, but in general less serious content is also definitely a go for [r/Diablofunny](http://www.reddit.com/r/Diablofunny)!**\n\nThank you for your understanding, and thanks for being a member of this subreddit!']
	acronymRules = [re.compile('((DAE)|(Does Everyone Else)|(PSA)|(Public Service Announcement)|(FYI)|(For Your Information)|(Am I The Only One)).*'), \
							'Titles containing DAE, PSA, FYI and their expansions are automatically removed from [r/Diablo](http://www.reddit.com/r/Diablo) to ensure a high-quality experience for everyone.\n\n**Please try to think another way to write down the title without using these acronyms and their expansions.** We are trying to cut down on the bandwagon effect and encourage a more healthy discussion.\n\nThank you for your understanding, and thanks for being a member of this subreddit!']
	def __init__(self):
		self.r = praw.Reddit(user_agent='r/Diablo Automated moderation bot')

		# Load configuration
		config = open('config.cfg', 'r')
		self.modUser = config.readline().rstrip('\n')
		self.modPassword = config.readline().rstrip('\n')
		self.subreddit = config.readline().rstrip('\n')
		self.lastTimestamp = config.readline().rstrip('\n')
		config.close()

		# Login to moderator account
		print 'Logging in as ' + self.modUser + '...'
		self.r.login(self.modUser, self.modPassword)

	def saveConfig(self):
		config = open('config.cfg', 'w')
		config.write(self.modUser + '\n')
		config.write(self.modPassword + '\n')
		config.write(self.subreddit + '\n')
		config.write(self.thisTimestamp)
		config.close()

	def isImage(self, submission):
		if self.imageRules[0].match(submission.url):
			return 1
		else:
			img = urllib.urlopen(submission.url)
			type = img.info()['Content-Type']
			if type.startswith('image/'):
				return 1
		else:
			return 0

	def hasAcronym(self, submission):
		if self.acronymRules[0].match(submission.title):
			return 1
		else:
			return 0

	def removeAndComment(self, submission, reply):
		modReply = submission.add_comment(reply)
		modReply.distinguish()
		time.sleep(0.5)
		submission.remove()

	def autoMod(self):
		# Grab the newest submissions...
		submissions = self.r.get_subreddit(self.subreddit).get_new(limit=None, place_holder=self.lastTimestamp)
		count = 0
		for x in submissions:
			if not x.approved_by:
				if x.domain.lower() != 'self.' + self.subreddit.lower():
					if self.isImage(x):
						print "Image detected, " + x.title
						self.removeAndComment(x, self.imageRules[1])
						time.sleep(2) # Dont submit comments to quickly...
				elif self.hasAcronym(x):
					print "Acronym detected, " + x.title
					self.removeAndComment(x, self.acronymRules[1])
					time.sleep(2) # Dont submit comments to quickly...
				elif count == 0:
					self.thisTimestamp = x.id
			else:
				if count == 0:
					self.thisTimestamp = x.id
			count += 1
		self.saveConfig()

if __name__ == '__main__':
	rdiablo = butcherBot()
	rdiablo.autoMod()