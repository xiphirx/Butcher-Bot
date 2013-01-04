import praw
import urllib.error
import urllib.parse
import urllib.request
import re
import configparser
import json
import time


dryrun = True
loglevel = 3 #0 error, 1 normal activity, 2 verbose activity, 3 debug

def log(lvl, s):
    if lvl <= loglevel:
        logfile.write(s.encode("utf-8"))

class Rule:
    def __init__(self, name):
        self.rname = name
        self.comment_type = False

    def __str__(self):
        return "<Rule(%s)>" % (self.rname)

    def match(self, submission):
        log(0, "INTERNAL ERROR: %s's rule type does not have a match() function\n" % (self.rname))
        return False

    def apply(self, submission):
        if submission.subreddit.display_name not in self.reddits:
            log(3, "SKIPPING %s %s\n" % (self.rname, submission.permalink))
            return # Not all rules apply to all subreddits
        if self.match(submission):
            log(1, "MATCH %s: %s (%s)\n" % (self.rname, submission.permalink, submission.title))
            self.do_actions(submission)
        else:
            log(3, "NO MATCH %s: %s (%s)\n" % (self.rname, submission.permalink, submission.title))

    def do_actions(self, submission):
        if dryrun:
            log(1, "Dry run. Not acting. %s\n" % (self.actions))
            return
        # Use "none" in the config file if you just want to log the match without acting.
        #for a in self.actions:
            #self.action_fns[a](submission)
        if "comment" in self.actions:
            self._action_comment(submission)
        if "remove" in self.actions:
            self._action_remove(submission)
        if "report" in self.actions:
            self._action_report(submission)

    def _action_comment(self, submission):
        log(2, "COMMENT %s\n" % (submission.permalink))
        modReply = submission.add_comment(self.comment)
        modReply.distinguish()
    def _action_remove(self, submission):
        log(1, "REMOVE %s\n" % (submission.permalink))
        submission.remove()
    def _action_report(self, submission):
        log(2, "REPORT %s\n" % (submission.permalink))
        submission.report()

    action_fns = {"comment": _action_comment,
            "remove": _action_remove,
            "report": _action_report}

class CommentRule(Rule):
    def __init__(self, name):
        super().__init__(name)
        self.comment_type = True

    def make_url(self, c):
        return "http://www.reddit.com/r/%s/comments/%s/_/%s" % (c["subreddit"], c["link_id"][3:], c["id"])

    def apply(self, comment):
        if comment["subreddit"] not in self.reddits:
            log(3, "SKIPPING %s %s\n" % (self.rname, self.make_url(comment)))
            return # Not all rules apply to all subreddits
        if self.match(comment):
            log(1, "MATCH %s: %s (%s)\n" % (self.rname, self.make_url(comment), comment["author"]))
            self.do_actions(praw.objects.Comment(self.r, comment))
        else:
            log(3, "NO MATCH %s %s\n" % (self.rname, self.make_url(comment)))

class ImageRule(Rule):
    class HeadRequest(urllib.request.Request):
        def get_method(self):
            return "HEAD"

    def match(self, submission):
        if submission.domain[:5] == "self.":
            return False  # self-posts can't be images
        if self.re.search(submission.url):
            return True
        #TODO multithread this
        try:
            img = urllib.request.urlopen(self.HeadRequest(submission.url))
            contenttype = img.info()['Content-Type']
            if contenttype != None and contenttype.startswith('image/'):
                return True
        except urllib.error.HTTPError:
            pass #If HTTP error, assume it's not an image. FIXME?
        except urllib.error.URLError:
            pass
        return False

class TitleRule(Rule):
    def match(self, submission):
        return self.re.search(submission.title)

class UserRule(Rule):
    def match(self, submission):
        return self.re.search(submission.author.name)

class CommentUserRule(CommentRule):
    def match(self, comment):
        return self.re.search(comment["author"])

class CommentBodyRule(CommentRule):
    def match(self, comment):
        return self.re.search(comment["body"])

class ButcherBot:
    class rule:
        def __init__(self):
            pass

    def __init__(self):
        # Load configuration
        self.config = configparser.SafeConfigParser()
        self.config.read("/srv/bots/Butcher-Bot/rules.ini")

        self.r = praw.Reddit(user_agent=self.config.get("DEFAULT", "user_agent"))

        self.reddits = set()
        self.rules = []
        for s in self.config.sections():
            rtype = self.config.get(s, "type")
            if rtype == "image":
                rule = ImageRule(s)
            elif rtype == "title":
                rule = TitleRule(s)
            elif rtype == "user":
                rule = UserRule(s)
            elif rtype == "comment_user":
                rule = CommentUserRule(s)
                rule.r = self.r	#FIXME do this more elegantly
            elif rtype == "comment_body":
                rule = CommentBodyRule(s)
                rule.r = self.r	#FIXME do this more elegantly
            else:
                rule = Rule(s) # This will probably cause a runtime error. Good.
            rule.re = re.compile(self.config.get(s, "re"), re.IGNORECASE)
            rule.comment = self.config.get(s, "comment").replace("\\n", "\n")
            rule.distinguish = self.config.get(s, "distinguish").lower() in ["true", "1", "t", "y", "yes", "on"]
            rule.reddits = self.config.get(s, "reddits").split()
            rule.actions = self.config.get(s, "actions").split()
            self.rules.append(rule)
            for sr in self.config.get(s, "reddits").split():
                self.reddits.add(sr)
        log(3, "rules: %s\n" % (self.rules))
        log(3, "reddits: %s\n" % (self.reddits))

        # Log in
        log(3, 'Logging in as %s...\n' % (self.config.get("DEFAULT", "user")))
        self.r.login(self.config.get("DEFAULT", "user"), self.config.get("DEFAULT", "pass"))

        # Split comment and submission rules into separate lists for later efficiency
        self.rules_submissions = []
        self.rules_comments = []
        for rule in self.rules:
            if rule.comment_type == True:
                self.rules_comments.append(rule)
            else:
                self.rules_submissions.append(rule)


    def save_config(self):
        with open('/srv/bots/Butcher-Bot/rules.ini', 'w') as fname:
            self.config.write(fname)

    def get_comments(self, rname, last_comment):
        items = []
        count = 0
        n = last_comment
        done = False
        while True:
            log(3, "looping %s\n" % (n))
            j = self.r._request(page_url="http://www.reddit.com/r/%s/comments.json" % (rname), url_data={"limit":100, "before":n, "uh":self.r.modhash})
            data = json.loads(j.decode("UTF-8"))

            n = data["data"]["after"]
            if data["data"]["before"] == None:
                done = True		# reddit.com won't give us any more records

            items += data["data"]["children"]
            count += 1

            if done:
                break
            if count > 4:
                break

        if len(items) == 0:
            j = self.r._request(page_url="http://www.reddit.com/r/%s/comments.json" % (rname), url_data={"limit":100, "uh":self.r.modhash})
            data = json.loads(j.decode("UTF-8"))
				i = 0
				for c in data["data"]["children"]:
					if c["data"]["id"] >= last_comment:
						break
					i++
				items += data["data"]["children"][i:]

        self.num_comments = len(items)
        return items


    def auto_mod(self):
        # main loop
        for rname in self.reddits:
            sub = self.r.get_subreddit(rname)
            last_item = self.config.get("DEFAULT", "last_item")
            submissions = list(sub.get_new_by_date(limit=100, place_holder=last_item))
				for i in range(0, len(submissions)):
					if submissions[i].id < last_item:
						del submissions[i]
					else:
						break
            for submission in submissions:
                if submission.approved_by:
                    log(2, "Post is already approved: (%s) (%s)\n" % (submission.permalink, submission.approved_by))
                    continue
                for rule in self.rules_submissions:
                    rule.apply(submission)

            self.num_submissions = len(submissions)
            if self.num_submissions > 0:
                #self.config.set("DEFAULT", "last_item", "t3_"+submissions[0]["data"]["id"])
                self.config.set("DEFAULT", "last_item", submissions[0].id)

            if len(self.rules_comments) > 0:
                coms = self.get_comments(rname, self.config.get("DEFAULT", "last_comment"))
                for c in coms:
                    for rule in self.rules_comments:
                        rule.apply(c["data"])

            if len(coms) > 0:
                self.config.set("DEFAULT", "last_comment", coms[0]["data"]["name"])

        self.save_config()


def main():
    global logfile
    logfile = open("/srv/bots/log/butcher.log", "ab")
    start_time = time.time()
    butcher = ButcherBot()
    butcher.auto_mod()
    log(1, "%d - %d seconds - %d submissions - %d comments\n" % (start_time, time.time() - start_time, butcher.num_submissions, butcher.num_comments))
    logfile.close()


if __name__ == '__main__':
    main()
