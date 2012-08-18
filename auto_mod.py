import praw
import urllib.error
import urllib.parse
import urllib.request
import re
import configparser


dryrun = True
loglevel = 3 #0 error, 1 normal activity, 2 verbose activity, 3 debug

def log(lvl, s):
    if lvl <= loglevel:
        print(s)

class Rule:
    def __init__(self, name):
        self.rname = name

    def __str__(self):
        return "<Rule(%s)>" % (self.rname)

    def match(self, submission):
        log(0, "INTERNAL ERROR: %s's rule type does not have a match() function" % (self.rname))
        return False

    def apply(self, submission):
        if submission.subreddit.display_name not in self.reddits:
            log(3, "SKIPPING %s %s" % (self.rname, submission.permalink))
            return # Not all rules apply to all subreddits
        if self.match(submission):
            log(1, "MATCH %s: %s (%s)" % (self.rname, submission.permalink, submission.title))
            self.do_actions(submission)

    def do_actions(self, submission):
        if dryrun:
            log(1, "Dry run. Not acting. %s" % (self.actions))
            return
        # Use "none" in the config file if you just want to log the match without acting.
        if "comment" in self.actions:
            log(2, "comment %s" % (submission.permalink))
            modReply = submission.add_comment(self.rules[rule].comment)
            modReply.distinguish()
        if "remove" in self.actions:
            log(1, "REMOVE %s" % (submission.permalink))
            submission.remove()
        if "report" in self.actions:
            log(2, "REPORT %s" % (submission.permalink))
            #TODO

class ImageRule(Rule):
    def match(self, submission):
        if submission.domain.lower() == "self." + self.rname.lower():
            return False  # self-posts can't be images
        if self.re.match(submission.url):
            return True
        img = urllib.request.urlopen(submission.url)
        type = img.info()['Content-Type']
        if type.startswith('image/'):
            return True
        return False

class TitleRule(Rule):
    def match(self, submission):
        return self.re.match(submission.title)

class UserRule(Rule):
    def match(self, submission):
        return self.re.match(submission.author.name)


class ButcherBot:
    class rule:
        def __init__(self):
            pass

    def __init__(self):
        # Load configuration
        self.config = configparser.SafeConfigParser()
        self.config.read("rules.ini")

        self.reddits = set()
        self.rules = []
        for s in self.config.sections():
            rtype = self.config.get(s, "type")
            if rtype == "image":
                rule = ImageRule(s)
            elif rtype == "title":
                rule = TitleRule(s)
            else:
                rule = Rule(s) # This will probably cause a runtime error. Good.
            rule.re = re.compile(self.config.get(s, "re"))
            rule.comment = self.config.get(s, "comment")
            rule.distinguish = self.config.get(s, "distinguish").lower() in ["true", "1", "t", "y", "yes", "on"]
            rule.reddits = self.config.get(s, "reddits").split()
            self.rules.append(rule)
            for sr in self.config.get(s, "reddits").split():
                self.reddits.add(sr)
        log(3, "rules: %s" % (self.rules))
        log(3, "reddits: %s" % (self.reddits))

        # Log in
        self.r = praw.Reddit(user_agent=self.config.get("DEFAULT", "user_agent"))
        log(2, 'Logging in as %s...' % (self.config.get("DEFAULT", "user")))
        self.r.login(self.config.get("DEFAULT", "user"), self.config.get("DEFAULT", "pass"))


    def save_config(self):
        with open('rules.ini', 'w') as fname:
            self.config.write(fname)


    def auto_mod(self):
        # main loop
        for rname in self.reddits:
            sub = self.r.get_subreddit(rname)
            submissions = sub.get_new(limit=None, place_holder=self.config.get("DEFAULT", "last_item"))
            first = True
            for submission in submissions:
                if first:
                    self.config.set("DEFAULT", "last_item", submission.id)
                    first = False

                if submission.approved_by:
                    log(2, "Post is already approved")
                    continue

                for rule in self.rules:
                    rule.apply(submission)

        self.save_config()


def main():
    butcher = ButcherBot()
    butcher.auto_mod()


if __name__ == '__main__':
    main()
