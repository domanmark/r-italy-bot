import praw
import spacy
from collections import Counter
from googletrans import Translator
import csv


def main():
    reddit = praw.Reddit("r-italy-bot")
    comments = get_subreddit_comments(reddit, "italy")
    # spacy has max length of 1 MM characters due to memory use
    if len(comments) > 1000000:
        print("WARNING: Too many characters in comments, trimming to 1 million")
        comments = comments[0:999999]
    nlp = spacy.load("it_core_news_sm")
    comment_doc = nlp(comments)

    preprocessed = [
        preprocess_token(token) for token in comment_doc if is_valid_token(token)
    ]

    word_freq = Counter(preprocessed)
    common_words = word_freq.most_common(100)

    translator = Translator()

    seen_words = []

    for count, word in enumerate(common_words):
        ita_text = word[0]
        word_count = word[1]
        translation = translator.translate(ita_text, dest="en", src="it")
        eng_text = translation.text
        print(f"{count}. {ita_text} --> {eng_text}")
        seen_words.append([ita_text, eng_text])

    with open("translated_words.csv", "a") as output:
        outwriter = csv.writer(output)
        outwriter.writerows(seen_words)


def get_subreddit_comments(reddit, subreddit):
    all_comments = []
    for submission in reddit.subreddit(subreddit).hot(limit=15):
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            all_comments.append(comment.body)
    return " ".join(all_comments)


def is_valid_token(token):
    if (
        not token
        or not token.string.strip()
        or token.is_stop
        or token.is_punct
        or str(token).isdigit()
    ):
        return False
    return True


def preprocess_token(token):
    return token.lemma_.strip().lower()


if __name__ == "__main__":
    main()
