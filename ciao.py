import praw
import spacy
from collections import Counter
from googletrans import Translator
import csv
import yagmail
import json

def tokenize_and_process_text(input_text):
    # spacy has max length of 1 MM characters due to memory use
    if len(input_text) > 1000000:
        print("WARNING: Too many characters in comments, trimming to 1 million")
        input_text = input_text[0:999999]

    nlp = spacy.load("it_core_news_sm")
    input_doc = nlp(input_text)

    preprocessed = [
        preprocess_token(token) for token in input_doc if is_valid_token(token)
    ]
    return preprocessed


def translate_tokens(tokens):
    translations = []
    translator = Translator()
    for token in tokens:
        translation = translator.translate(token, dest="en", src="it")
        translations.append([token, translation.text])
    return translations


def get_unique_tokens(already_seen, current_input, limit=10):
    unique = []
    for token in current_input:
        if token not in already_seen:
            unique.append(token)
        if len(unique) == limit:
            break
    return unique


def compose_message(translations):
    message_lines = []
    for translation in translations:
        orig = translation[0]
        trans = translation[1]
        line = f"{orig} --> {trans}"
        message_lines.append(line)
    message = "\n".join(message_lines)
    return message


def send_text(message):
    with open("email_config.json") as config_file:
        config = json.load(config_file)
        to_email =  config["to_email"]
        from_email = config["from_email"]

        yag = yagmail.SMTP(from_email)
        yag.send(
            to=to_email,
            subject="r/italy vocab",
            contents=message,
        )


def get_subreddit_comments(reddit, subreddit, submission_limit=15):
    """Fetch comments from a specified subreddit and concatenate
       them into one string.

    Args:
        reddit (Reddit): The Reddit instance from praw
        subreddit (String): Subreddit to fetch content from
        submission_limit (int): Max number of submissions to process

    Returns:
        String: All comments from all submissions processed
    """
    all_comments = []
    for submission in reddit.subreddit(subreddit).hot(limit=submission_limit):
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


def main():
    reddit = praw.Reddit("r-italy-bot")
    comments = get_subreddit_comments(reddit, "italy")
    preprocessed = tokenize_and_process_text(comments)
    word_freq = Counter(preprocessed)
    common_words = word_freq.most_common(100)
    words = [word[0] for word in common_words]
    seen_words = set()
    with open("seen_words.csv", "r") as seen:
        seen_reader = csv.reader(seen)
        for row in seen_reader:
            seen_words.add(row[0])

    new_tokens = get_unique_tokens(seen_words, words)
    translations = translate_tokens(new_tokens)

    message = compose_message(translations)
    send_text(message)

    with open("seen_words.csv", "a") as output:
        outwriter = csv.writer(output)
        outwriter.writerows(translations)


if __name__ == "__main__":
    main()
