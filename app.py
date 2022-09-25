from matplotlib.pyplot import axis
import tweepy
import pandas as pd
import credentials
# Tweet Text cleaning
import re
# Plotting the wordcloud
# you can specify fonts, stopwords, background color and other options
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import nltk
from flask import Flask, render_template, request

from PIL import Image
import base64
import io

import warnings
warnings.filterwarnings("ignore")

# Initialize bearer token and client
client = tweepy.Client(bearer_token=credentials.bearer_token)

app = Flask(__name__)

tweet_df = None
Tweet_Texts_Cleaned = None

def extract_tweets(name, start, end):
    global tweet_df
    _username = []
    _username.append(name)
    for username in _username:

        query = 'from:' + username
        start_time = start
        end_time = end

        tweets = tweepy.Paginator(client.search_all_tweets, query=query,
                                  tweet_fields=['id', 'text', 'created_at', 'conversation_id', 'public_metrics',
                                                'entities',
                                                'in_reply_to_user_id', 'lang', 'possibly_sensitive'],
                                  max_results=500, start_time=start_time, end_time=end_time).flatten(limit=10000000)
        tweet_df = pd.DataFrame(
            columns=['id', 'created_at', 'conversation_id', 'tweet', 'retweet_count', 'like_count', 'reply_count',
                     'quote_count', 'expanded_url',
                     'language', 'possibly_sensitive', 'in_reply_to_user_id'])

        for tweet in tweets:
            if tweet.entities is not None:
                if tweet.entities.get('urls') is not None:
                    tweet_df = tweet_df.append(
                        {'id': tweet.id, 'created_at': tweet.created_at, 'conversation_id': tweet.conversation_id,
                         'tweet': tweet.text,
                         'retweet_count': tweet.public_metrics.get('retweet_count'),
                         'like_count': tweet.public_metrics.get('like_count'),
                         'reply_count': tweet.public_metrics.get('reply_count'),
                         'quote_count': tweet.public_metrics.get('quote_count'),
                         'expanded_url': tweet.entities.get('urls')[0].get('expanded_url'), 'language': tweet.lang,
                         'possibly_sensitive': tweet.possibly_sensitive,
                         'in_reply_to_user_id': tweet.in_reply_to_user_id}
                        , ignore_index=True)
                else:
                    tweet_df = tweet_df.append(
                        {'id': tweet.id, 'created_at': tweet.created_at, 'conversation_id': tweet.conversation_id,
                         'tweet': tweet.text,
                         'retweet_count': tweet.public_metrics.get('retweet_count'),
                         'like_count': tweet.public_metrics.get('like_count'),
                         'reply_count': tweet.public_metrics.get('reply_count'),
                         'quote_count': tweet.public_metrics.get('quote_count'),
                         'expanded_url': '', 'language': tweet.lang, 'possibly_sensitive': tweet.possibly_sensitive,
                         'in_reply_to_user_id': tweet.in_reply_to_user_id}, ignore_index=True)

        tweet_df['username'] = username
        tweet_df.to_csv(username + '.csv', index=False)
        return tweet_df

def clean_tweets():
    global Tweet_Texts_Cleaned
    Tweet_Texts = tweet_df['tweet'].values

    # Converting the text column as a single string for wordcloud
    Tweets_String = str(Tweet_Texts)

    # Converting the whole text to lowercase
    Tweet_Texts_Cleaned = Tweets_String.lower()

    # Removing the twitter usernames from tweet string
    Tweet_Texts_Cleaned = re.sub(r'@\w+', ' ', Tweet_Texts_Cleaned)

    # Removing the URLS from the tweet string
    Tweet_Texts_Cleaned = re.sub(r'http\S+', ' ', Tweet_Texts_Cleaned)

    # Deleting everything which is not characters
    Tweet_Texts_Cleaned = re.sub(r'[^a-z A-Z]', ' ', Tweet_Texts_Cleaned)

    # Deleting any word which is less than 3-characters mostly those are stopwords
    Tweet_Texts_Cleaned = re.sub(r'\b\w{1,2}\b', '', Tweet_Texts_Cleaned)

    # Stripping extra spaces in the text
    Tweet_Texts_Cleaned = re.sub(r' +', ' ', Tweet_Texts_Cleaned)
    return Tweet_Texts_Cleaned


# Creating the custom stopwords
def wordcloud():
    global Tweet_Texts_Cleaned
    stopwords_df = set(nltk.corpus.stopwords.words("english"));

    customStopwords = list(stopwords_df)

    wordcloudimage = WordCloud(
        max_words=100,
        max_font_size=500,
        font_step=2,
        stopwords=customStopwords,
        background_color='white',
        width=1000,
        height=720
    ).generate(Tweet_Texts_Cleaned)

    plt.figure(figsize=(15, 7))
    plt.axis("off")
    plt.imshow(wordcloudimage)
    
    plt.show()

@app.route('/handle_data', methods=['POST'])
def handle_data():
    global Tweet_Texts_Cleaned
    projectpath = request.form['projectFilepath']
    # startDate = request.form['start_date']
    # endDate = request.form['end_date']

    tweet_df = extract_tweets(projectpath, '2020-01-01T00:00:00Z', '2020-01-10T00:00:00Z')
    # print(tweet_df)

    Tweet_Texts_Cleaned = clean_tweets()
    # print(Tweet_Texts_Cleaned)

    stopwords_df = set(nltk.corpus.stopwords.words("english"));

    customStopwords = list(stopwords_df)

    wordcloudimage = WordCloud(
        max_words=100,
        max_font_size=500,
        font_step=2,
        stopwords=customStopwords,
        background_color='white',
        width=1000,
        height=720
    ).generate(Tweet_Texts_Cleaned)


    data = io.BytesIO()
    wordcloudimage.to_image().save(data, 'PNG')
    data.seek(0)
    encoded_img_data = base64.b64encode(data.getvalue())

    return render_template("index.html", img_data=encoded_img_data.decode('utf-8'))

@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":

    app.run(port="8080", debug=True)
