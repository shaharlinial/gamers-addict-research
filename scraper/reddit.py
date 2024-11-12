import praw
import pandas as pd
import tqdm 
import csv  # Import csv module for quoting options


# Reddit API credentials
reddit = praw.Reddit(
    client_id="x",
    client_secret="x",
    user_agent="python3.11"
)


# Define parameters
subreddits = ['ApexLegends', 'DotA2', 'GlobalOffensive']
keywords_addiction = ["can't stop", "addicted", "hours played", "too much time", "hard to quit"]
apex_ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Predator"]
dota2_ranks = ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"]
ranking = ["mmr", "rank", "ladder", "champion", "leaderboard", "competitve"]
keywords_rank = apex_ranks + dota2_ranks + ranking

def is_self_report(post_text):
    """Check if post is likely a self-report based on certain keywords and length."""
    # Look for first-person pronouns or experience-sharing words
    self_report_indicators = ["i ", "my ", "me ", "played", "stopped", "quit", "addicted", "time"]
    is_self_report = any(indicator in post_text for indicator in self_report_indicators)
    
    # Set a minimum length to filter out very short posts (e.g., announcements)
    if len(post_text) < 50 or len(post_text) > 400:
        return False
    return is_self_report

def scrape_reddit_posts(subreddits, keywords_addiction, keywords_rank, limit=100):
    data = []
    
    for subreddit_name in tqdm.tqdm(subreddits):
        subreddit = reddit.subreddit(subreddit_name)
        
        # Fetch posts
        for post in tqdm.tqdm(subreddit.hot(limit=limit)):
            title = post.title.lower()
            body = post.selftext.lower()
            comments = post.num_comments
            upvotes = post.score
            
            # Check if post is a self-report
            if not is_self_report(body):
                continue
            
            # Check for keywords
            addiction_related = any(keyword in body or keyword in title for keyword in keywords_addiction)
            rank_related = any(keyword in body or keyword in title for keyword in keywords_rank)
            
            # Append data
            data.append({
                "subreddit": subreddit_name,
                "title": post.title,
                "body": post.selftext,
                "comments": comments,
                "upvotes": upvotes,
                "addiction_related": addiction_related,
                "rank_related": rank_related
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df

# Run the scraper and save to CSV
df = scrape_reddit_posts(subreddits, keywords_addiction, keywords_rank, limit=1500)
df.to_csv('self_report_reddit_gaming_posts.csv', index=False, quoting=csv.QUOTE_ALL, escapechar='\\')
print("Data saved to self_report_reddit_gaming_posts.csv")