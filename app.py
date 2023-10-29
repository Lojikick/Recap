from flask import * #importing flask (Install it using python -m pip install flask)

from flask import *
import praw
import numpy as np
import pandas as pd
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
pd.options.mode.chained_assignment = None

app = Flask(__name__) #initialising flask

# Reddit API credentials
client_id = 'Lnt2q1aiGONcbox9EyK-Mw'
client_secret = 'VdTP86mTMJIPop59Xeks_Ldr_AgWCQ'
user_agent = 'test'  # A description of your application

# Initialize PRAW
reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

@app.route("/") #defining the routes for the home() funtion (Multiple routes can be used as seen here)
@app.route("/home")
def home():
    return render_template("home.html") #rendering our home.html contained within /templates

@app.route("/account", methods=["POST", "GET"]) #defining the routes for the account() funtion
def account():
    res = "<User Not Defined>" #Creating a variable usr
    output = score_keyword("cs170", 'berkeley', 200)
    if (request.method == "POST"): #Checking if the method of request was post
        res = request.form["prompt"] #getting the name of the user from the form on home page
        output = score_keyword(res, 'berkeley', 200)
        if not res: #if name is not defined it is set to default string
            res = "<User Not Defined>"
    return render_template("account.html",results=res, data = output.to_html()) #rendering our account.html contained within /templates

#Major Backend Functions----

def search_reddit(search_word, subreddit_name, search_limit):
    # Search for comments related to the specified word
    if subreddit_name:
        subreddit = reddit.subreddit(subreddit_name)
        submissions = subreddit.search(search_word, limit=search_limit)  # You can adjust the limit as needed
    else:
        submissions = reddit.subreddit('all').search(search_word, limit=search_limit)
    authors, comments, urls, titles = [], [], [], []
    # Iterate through the comments and extract their data
    counter = 0
    for submission in submissions:
        if (counter >= search_limit):
            break
        authors.append(submission.author.name)
        comments.append(submission.selftext)
        urls.append(submission.url)
        titles.append(submission.title)
        counter+=1
        for comment in submission.comments:
            if (counter >= search_limit):
                break
            if (comment.author):
                authors.append(comment.author.name)
            else:
                authors.append('')
            comments.append(comment.body)
            urls.append(submission.url)
            titles.append(submission.title)
            counter+=1
    raw_data = pd.DataFrame({'Title': titles, 'Comment':comments, 'URL':urls, 'Author':authors})
    return raw_data
analyzer = SentimentIntensityAnalyzer()
def get_emotion_emoji(score):
        if score < -0.6:
            return "😢"  # Very sad
        elif score < -0.2:
            return "😔"  # Somewhat sad
        elif score > 0.6:
            return "😄"  # Very happy
        elif score > 0.2:
            return "😊"  # Somewhat happy
        else:
            return "😐"  # Neutral
def score(phrase):
    num = analyzer.polarity_scores(phrase)['compound']
    return get_emotion_emoji(num) + str(round(num, 1))
def score_data(data):
    """
    Input: DataFrame
    Output: DataFrame
    """
    if raw_data.shape[0] == 0:
        print('No results found')
        return
    new_data = data.copy()
    new_data.drop(axis=0, labels=data.index[data['Comment'].str.len() == 0], inplace=True)
    new_data['Sentiment'] = new_data['Comment'].apply(score)
    new_data['Comment'] = new_data['Comment']
    return new_data
def score_keyword(search_word, subreddit_name, search_limit):
    raw_data = search_reddit(search_word, subreddit_name, search_limit)
    return score_data(raw_data)
def top3bot3(data):
    """
    Input: DataFrame
    Output: tuple (DataFrame, DataFrame)
    """
    new_data = data.sort_values('Sentiment', ascending=False)
    top3 = new_data.iloc[:3, :]
    bot3 = new_data.iloc[-3:, :]
    return top3, bot3
def calculate_average_sentiment(data):
    sentiments = data[['Author', 'Sentiment']].groupby('Author').mean()
    return np.mean(sentiments['Sentiment'])
def format_data(data):
    """
    Input: DataFrame
    Output: DataFrame
    """
    new_data = data.copy()
    new_data['Comment'] = new_data['Comment'].str[:241]
    return new_data

if __name__ == "__main__": #checking if __name__'s value is '__main__'. __name__ is an python environment variable who's value will always be '__main__' till this is the first instatnce of app.py running
    app.run(debug=True,port=4949) #running flask (Initalised on line 4)
