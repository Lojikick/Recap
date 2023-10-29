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
    for submission in submissions:
        authors.append(submission.author.name)
        #print(f"Author: {submission.author}\n")
        comments.append(submission.selftext)
        #print(f"Comment: {submission.selftext}")
        urls.append(submission.url)
        titles.append(submission.title)
    raw_data = pd.DataFrame({'Title': titles, 'Author':authors, 'Comment':comments, 'URL':urls})
    return raw_data
analyzer = SentimentIntensityAnalyzer()
def score(phrase):
    return analyzer.polarity_scores(phrase)['compound']
def score_data(data):
    new_data = data.copy()
    new_data.drop(axis=0, labels=data.index[data['Comment'].str.len() == 0], inplace=True)
    new_data['Sentiment'] = new_data['Comment'].apply(score)
    #sentiments = new_data[['Author', 'Sentiment']].groupby('Author').mean()
    return new_data#, np.mean(sentiments['Sentiment'])
def score_keyword(search_word, subreddit_name, search_limit):
    raw_data = search_reddit(search_word, subreddit_name, search_limit)
    return score_data(raw_data)

if __name__ == "__main__": #checking if __name__'s value is '__main__'. __name__ is an python environment variable who's value will always be '__main__' till this is the first instatnce of app.py running
    app.run(debug=True,port=4949) #running flask (Initalised on line 4)
