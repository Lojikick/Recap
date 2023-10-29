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

    if (request.method == "POST"): #Checking if the method of request was post
        res = request.form["prompt"] 
        school = request.form["school"] #getting the name of the user from the form on home page
        data = score_keyword(res, school, 75)
        avg_sentiment = round(calculate_average_sentiment(data), 2)
        avg_difficulty = 10*round(calculate_average_difficulty(data), 1)
        avg_difficulty = str(avg_difficulty) + "/10.0"
        if (data.shape[0] > 0):
            data['Sentiment'] = data['Sentiment'].apply(add_emoji)
        # data = { 'Column1': [10, 20, 30], 'Column2': ['A', 'B', 'C'] }
        df = pd.DataFrame(data)

        if not res: #if name is not defined it is set to default string
            res = "<User Not Defined>"
    # return render_template("account.html",results=res, data = output.to_html()) #rendering
    temp = "Hello"
    div_elements = ''
    rows = list(df.index)
    for row in range(len(rows)):
        author = df.iloc[row,3]
        comment = df.iloc[row,1][0:50]
        link = df.iloc[row,2]
        sentiment = df.iloc[row,4] 

        div_elements += f'<div>{author}&nbsp;&nbsp;&nbsp;{comment}&nbsp;&nbsp;&nbsp;{sentiment}</div>'
    return render_template("account.html", results=res, divs=div_elements, sent = avg_sentiment, diff = avg_difficulty) 

    # our account.html contained within /templates
    # display_data(res, df)


#Major Backend Functions----
# def display_data(res, df):
#     div_elements = ''
#     for column in df.columns:
#         for value in df[column]:
#             div_elements += f'<div>{value}</div>'
    
   

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
        slftxt = submission.selftext
        url = submission.url
        if (slftxt.find('Piazza') != -1 or url[-4:] == '.jpg'):
            continue
        authors.append(submission.author.name)
        comments.append(slftxt)
        urls.append(url)
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
def process_data(data):
    new_data = data.copy()
    comments = new_data['Comment']
    comments = comments.str.lower()
    comments = comments.str.replace(r'http.*($|\s)', '') # Get rid of images
    comments = comments.str.replace(r'[^\w|_|\s]|\n', ' ') # Get rid of punctuation and newlines
    new_data['Split'] = comments.str.split() # Create split column
    new_data = new_data[new_data['Split'].str.len() > 1] # Remove empty or one word rows
    new_data = new_data.set_index('Author')
hard_words = ['fail', 'failing', 'suck', 'hard', 'difficult', 'dumb', 'drop', 'dropping', 'droppin', 'desperate', 'impossible',
    "hard", "strenuous", "arduous", "laborious", "heavy", "tough",
    "onerous", "burdensome", "demanding", "punishing", "grueling",
    "grinding", "back-breaking", "painful", "exhausting", "tiring",
    "fatiguing", "wearing", "wearying", "wearisome", "hellish",
    "killing", "knackering", "toilsome", "exigent", "problematic",
    "puzzling", "baffling", "perplexing", "confusing", "mystifying",
    "mysterious", "complicated", "complex", "involved", "intricate",
    "knotty", "thorny", "ticklish", "obscure", "abstract", "abstruse",
    "recondite", "enigmatic", "impenetrable", "unfathomable", "over one's head",
    "above one's head", "beyond one", "fiddly", "sticky",
    "gnarly", "wildering", "involute", "involuted", "😭", ":(", "wtf", "struggling", "fuck", "bad", "hurt", "dogshit"]
easy_words = ["easy", "simple", "effortless", "light", "gentle", "smooth",
    "easygoing", "simple", "undemanding", "unpunishing", "easy",
    "smooth", "effortless", "relaxing", "refreshing", "restful",
    "restorative", "refreshing", "restful", "restorative", "heavenly",
    "delightful", "invigorating", "easy", "straightforward", "clear",
    "obvious", "transparent", "self-explanatory", "clear", "self-evident",
    "intelligible", "comprehensible", "simple", "uncomplicated", "easy",
    "plain", "clear", "intelligible", "comprehensible", "simple",
    "shallow", "superficial", "commonplace", "basic", "self-explanatory",
    "easy", "troublesome", "straightforward", "clear", "obvious", "simple",
    'trivial', 'A+', 'easy', 'so easy', 'excellent', 'free', 'chill', 'cool', 'dubs', 'gigachad', "good", "best", "light"]
def score(phrase):
    return analyzer.polarity_scores(phrase)['compound']
def add_emoji(num):
    return get_emotion_emoji(num) + str(round(num, 1))
def predict_difficulty(input_string):
    input_string = input_string.lower()  # Convert the input string to lowercase for case-insensitive matching

    # Split the input string into words
    words = input_string.split()

    hard_score = sum(1 for word in words if word in hard_words)
    easy_score = sum(1 for word in words if word in easy_words)
    if hard_score + easy_score == 0:
        return None
    return hard_score/(hard_score + easy_score)
def score_data(data):
    """
    Input: DataFrame
    Output: DataFrame
    """
    if data.shape[0] == 0:
        print('No results found')
        return data
    new_data = data.copy()
    new_data.drop(axis=0, labels=data.index[data['Comment'].str.len() == 0], inplace=True)
    new_data['Sentiment'] = new_data['Comment'].apply(score)
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
    if (data.shape[0] == 0):
        return 0
    sentiments = data[['Author', 'Sentiment']].dropna().groupby('Author').mean()
    return np.mean(sentiments['Sentiment'])
def calculate_average_difficulty(data):
    if (data.shape[0] == 0):
        return 0
    diffs = data['Comment'].apply(predict_difficulty).dropna()
    return np.mean(diffs)
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
