import praw
import spacy


def main():
    reddit = praw.Reddit("r-italy-bot")

    all_comments = []

    for submission in reddit.subreddit("italy").hot(limit=10):
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            all_comments.append(comment.body)


def is_valid_token(token):
    if not token or not token.string.strip() or token.is_stop or token.is_punct:
        return False
    return True


def preprocess_token(token):
    return token.lemma_.strip().lower()


if __name__ == "__main__":
    main()
