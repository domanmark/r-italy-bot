import praw

reddit = praw.Reddit("r-italy-bot")

for submission in reddit.subreddit("italy").hot(limit=10):
    print(submission.title)