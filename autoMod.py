import praw
import urllib.request, urllib.parse, urllib.error
import re
import time
import configparser

class butcherBot:
	class rule:
		def __init__(self):
			pass

	def __init__(self):
		# Load configuration
		self.config = configparser.SafeConfigParser()
		self.config.read("rules.ini")

		# Login to moderator account
		self.r = praw.Reddit(user_agent='r/Diablo Automated moderation bot')
		print('Logging in as %s...' % (self.config.get("DEFAULT", "user")))
		self.r.login(self.config.get("DEFAULT", "user"), self.config.get("DEFAULT", "pass"))

		self.reddits = {}
		for s in self.config.get("DEFAULT", "reddits").split():
			self.reddits[s] = self.r.get_subreddit(s)

		self.rules = {}
		for s in self.config.sections():
			self.rules[s] = self.rule()
			self.rules[s].type = self.config.get(s, "type")
			self.rules[s].re = re.compile(self.config.get(s, "re"))
			self.rules[s].comment = self.config.get(s, "comment")
			self.rules[s].distinguish = self.config.get(s, "distinguish").lower() in ["true", "1", "t", "y", "yes", "on"]

	def saveConfig(self):
		with open('rules.ini', 'w') as fname:
			self.config.write(fname)

	def isImage(self, submission):
<<<<<<< HEAD
		if self.imageRules[0].match(submission.url):
			return 1
		else:
			img = urllib.urlopen(submission.url)
			type = img.info()['Content-Type']
			if type.startswith('image/'):
				return 1
		else:
			return 0
=======
		if self.rules["images"].re.match(submission.url):
			return True
		img = urllib.request.urlopen(submission.url)
		type = img.info()['Content-Type']
		return type.startswith('image/')
>>>>>>> def6da4ce22245ca5cfd440ce5b4cb913cc3ec66

	def hasAcronym(self, submission):
		return self.acronymRules[0].match(submission.title)

	def removeAndComment(self, submission, rule):
		modReply = submission.add_comment(self.rules[rule].comment)
		if self.rules[rule].distinguish:
			modReply.distinguish()
		submission.remove()

	def autoMod(self):
		# Grab the newest submissions...
		for rname, sub in self.reddits.items():
			submissions = sub.get_new(limit=None, place_holder=self.config.get("DEFAULT", "last_item"))
			first = True
			for x in submissions:
				if first:
					self.config.set("DEFAULT", "last_item", x.id)
					first = False
				if x.approved_by:
					print("already approved")
					continue
				for rule in self.rules:
					if self.rules[rule].type == "url":
						if x.domain.lower() == "self." + rname.lower():
							continue	#don't even check self-posts
						if self.isImage(x):
							print("Image detected, %s" % (x.title))
							self.removeAndComment(x, rule)
					elif self.rules[rule].type == "title":
						if self.hasAcronym(x):
							print("Acronym detected, %s" % (x.title))
							self.removeAndComment(x, rule)
		self.saveConfig()

if __name__ == '__main__':
	rdiablo = butcherBot()
	rdiablo.autoMod()
