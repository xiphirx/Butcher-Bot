#!/usr/bin/python3

import lightreddit
import urllib.error
import urllib.parse
import urllib.request
import http.client
import re
import configparser
import time


dryrun = True
loglevel = 1 #0 error, 1 normal activity, 2 verbose activity, 3 debug

def log(lvl, s):
	"""Wrapper for writing to logfile"""
	if lvl <= loglevel:
		logfile.write(s.encode("utf-8"))

class Rule:
	def __init__(self, s):
		self.rname = s["name"]
		self.comment_type = False
		self.re = re.compile(s["re"], re.IGNORECASE)
		self.comment = s["comment"].replace("\\n", "\n")
		self.distinguish = s["distinguish"].lower() in ["true", "1", "t", "y", "yes", "on"]
		self.reddits = s["reddits"].split()
		self.actions = s["actions"].split()

	def __str__(self):
		return "<Rule(%s, %s, %s)>" % (self.rname, self.reddits, self.actions)

	def _match(self, submission):
		"""Return true if submission matches a rule. This method is abstract in Rule."""
		raise RuntimeError("%s's rule type does not have a _match() function\n" % (self.rname))

	def apply(self, submission):
		"""Determine if this rule bears on submission, and if yes, execute the rule's actions."""
		if submission.subreddit not in self.reddits:
			#log(3, "SKIPPING %s %s (this rule doesn't apply)\n" % (self.rname, submission.permalink))
			return
		if self._match(submission):
			log(1, "MATCH %s: %s (%s)\n" % (self.rname, submission.permalink, submission.title))
			self._do_actions(submission)
		#else:
		#	log(3, "NO MATCH %s: %s (%s)\n" % (self.rname, submission.permalink, submission.title))

	def _do_actions(self, submission):
		"""Execute this rule's actions on submission. This method executes blindly, without checking for a match."""
		#if dryrun:
		#	log(1, "Dry run. Not acting. %s, %s\n" % (self.actions, submission))
		#	return
		# Use "none" in the config file if you just want to log the match without acting.
		#for a in self.actions:
		#	Rule.action_fns[a](submission)
		if "comment" in self.actions:
			self._action_comment(submission)
		if "remove" in self.actions:
			self._action_remove(submission)
		if "report" in self.actions:
			self._action_report(submission)

	def _action_comment(self, submission):
		log(2, "COMMENT %s\n" % (submission.permalink))
		submission.reply(self.comment, distinguish=True)
	def _action_remove(self, submission):
		log(1, "REMOVE %s\n" % (submission.id))
		submission.remove()
	def _action_report(self, submission):
		log(2, "REPORT %s\n" % (submission))
		submission.report()

	action_fns = {  "none":	 lambda x: x,		#that's a noop()
					"comment":  _action_comment,
					"remove":   _action_remove,
					"report":   _action_report}

class CommentRule(Rule):
	def __init__(self, name):
		super().__init__(name)
		self.comment_type = True

	def make_url(self, c):
		return "http://www.reddit.com/r/%s/comments/%s/_/%s" % (c.subreddit, c.link_id[3:], c.id)

	def apply(self, comment):
		if comment.subreddit not in self.reddits:
			#log(3, "SKIPPING %s %s: (%s) is not in %s\n" % (self.rname, self.make_url(comment), comment.subreddit, self.reddits))
			return # Not all rules apply to all subreddits
		if self._match(comment):
			log(1, "MATCH %s: %s (%s)\n" % (self.rname, self.make_url(comment), comment.author))
			self._do_actions(comment)
		#else:
		#	log(3, "NO MATCH %s %s\n" % (self.rname, self.make_url(comment)))

class ImageRule(Rule):
	class HeadRequest(urllib.request.Request):
		def get_method(self):
			return "HEAD"

	def _match(self, submission):
		if submission.domain[:5] == "self." or submission.url[:4] != "http":
			return False  # self-posts can't be images
		if self.re.search(submission.url):
			return True
		#TODO multithread this
		try:
			img = urllib.request.urlopen(self.HeadRequest(submission.url))
			contenttype = img.info()["Content-Type"]
			if contenttype != None and contenttype.startswith("image/"):
				return True
		except urllib.error.HTTPError:
			pass #If HTTP error, assume it's not an image. FIXME?
		except urllib.error.URLError:
			pass
		except http.client.BadStatusLine:
			pass
		return False

class TitleRule(Rule):
	def _match(self, submission):
		return self.re.search(submission.title)

class URLRule(Rule):
	def _match(self, submission):
		return self.re.search(submission.url)

class UserRule(Rule):
	def _match(self, submission):
		return self.re.search(submission.author.name)

class CommentUserRule(CommentRule):
	def _match(self, comment):
		return self.re.search(comment.author.name)

class CommentBodyRule(CommentRule):
	def _match(self, comment):
		return self.re.search(comment.body)

class ButcherBot:
	#TODO config file should specify "re" and "field" in each rule, instead of having field implied by type.

	def __init__(self):
		self.config = configparser.ConfigParser()
		self.config.read("/home/xiphirx/bots/Butcher-Bot/rules.ini")

		self.r = lightreddit.RedditSession(self.config.get("DEFAULT", "user"), self.config.get("DEFAULT", "pass"), self.config.get("DEFAULT", "user_agent"))

		self.reddits = set()
		self.rules = []
		for s in self.config.sections():
			#rule = self._rule_factory(self.config[s])   #FIXME python3.2+ has a dict-like interface for these
			d = {"name":s}
			for k in self.config.options(s):
				d[k] = self.config.get(s, k)
			rule = self._rule_factory(d)
			self.rules.append(rule)
			for sr in self.config.get(s, "reddits").split():
				self.reddits.add(sr)
		#log(3, "rules: %s\n" % ([str(x) for x in self.rules]))
		#log(3, "reddits: %s\n" % (self.reddits))

		# Split comment and submission rules into separate lists for later efficiency
		self.rules_submissions = []
		self.rules_comments = []
		for rule in self.rules:
			if rule.comment_type == True:
				self.rules_comments.append(rule)
			else:
				self.rules_submissions.append(rule)

	@classmethod
	def _rule_factory(cls, s):
		"""Create and return an object of the proper type"""
		if s["type"] == "image":
			return ImageRule(s)
		elif s["type"] == "title":
			return TitleRule(s)
		elif s["type"] == "url":
			return URLRule(s)
		elif s["type"] == "user":
			return UserRule(s)
		elif s["type"] == "comment_user":
			return CommentUserRule(s)
		elif s["type"] == "comment_body":
			return CommentBodyRule(s)
		else:
			raise RuntimeError("unknown rule type '%s'" % (s["type"]))

	def _save_config(self):
		"""Write state information to the config file"""
		with open("/home/xiphirx/bots/Butcher-Bot/rules.ini", "w") as fname:
			self.config.write(fname)

	def auto_mod(self):
		"""The main loop function"""
		for rname in self.reddits:
			last_item = self.config.get("DEFAULT", "last_item")
			submissions = self.r.get_submissions(rname, start=last_item)
			for submission in submissions:
				if not submission.approved_by.null_user:
					log(2, "Post is already approved: (%s) (%s)\n" % (submission.permalink, submission.approved_by))
					continue
				for rule in self.rules_submissions:
					rule.apply(submission)

			self.num_submissions = len(submissions)
			#log(2, "old last_item == %s; new last_item == %s\n" % (last_item, submissions[-1].name))
			if self.num_submissions > 0:
				self.config.set("DEFAULT", "last_item", submissions[-1].name)

			if len(self.rules_comments) > 0:
				last_comment = self.config.get("DEFAULT", "last_comment")
				coms = self.r.get_comments(rname, start=last_comment)
				self.num_comments = len(coms)
				for c in coms:
					for rule in self.rules_comments:
						rule.apply(c)

			#log(2, "old last_comment == %s; new last_comment == %s\n" % (last_comment, coms[-1].name))
			if self.num_comments > 0:
				self.config.set("DEFAULT", "last_comment", coms[-1].name)

		self._save_config()


def main():
	"""entry point for standalone bot"""
	global logfile
	logfile = open("/home/xiphirx/bots/log/butcher.log", "ab")
	start_time = time.time()
	butcher = ButcherBot()
	butcher.auto_mod()
	log(1, "%d - %f seconds - %d submissions - %d comments\n" % (start_time, time.time() - start_time, butcher.num_submissions, butcher.num_comments))
	logfile.close()

if __name__ == "__main__":
	main()
