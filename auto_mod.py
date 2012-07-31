import praw
import urllib.error
import urllib.parse
import urllib.request
import re
import configparser


class ButcherBot:
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

    def save_config(self):
        with open('rules.ini', 'w') as fname:
            self.config.write(fname)

    def is_image(self, submission):
        if self.rules["images"].re.match(submission.url):
            return True
        img = urllib.request.urlopen(submission.url)
        type = img.info()['Content-Type']
        return type.startswith('image/')

    def has_acronym(self, submission):
        return self.acronymRules[0].match(submission.title)

    def remove_and_comment(self, submission, rule):
        modReply = submission.add_comment(self.rules[rule].comment)
        if self.rules[rule].distinguish:
            modReply.distinguish()
        submission.remove()

    def apply_rules(self, rname, submission):
        # TODO: flake still thinks this method is too complex
        for rule in self.rules:
            if self.rules[rule].type == "url":
                if submission.domain.lower() == "self." + rname.lower():
                    continue  # Don't even check self-posts
                if self.is_image(submission):
                    print("Image detected, %s" % (submission.title))
                    self.remove_and_comment(submission, rule)

            elif self.rules[rule].type == "title":
                if self.has_acronym(submission):
                    print("Acronym detected, %s" % (submission.title))
                    self.remove_and_comment(submission, rule)

    def auto_mod(self):
        # Grab the newest submissions...
        for rname, sub in self.reddits.items():
            submissions = sub.get_new(limit=None, place_holder=self.config.get("DEFAULT", "last_item"))
            first = True
            for submission in submissions:
                if first:
                    self.config.set("DEFAULT", "last_item", submission.id)
                    first = False

                if submission.approved_by:
                    print("Post is already approved")
                    continue

                self.apply_rules(rname, submission)

        self.save_config()


def main():
    butcher = ButcherBot()
    butcher.auto_mod()


if __name__ == '__main__':
    main()
