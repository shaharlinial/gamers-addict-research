import praw
import pandas as pd
import tqdm 
import csv  # Import csv module for quoting options
from datetime import datetime
import time
import prawcore

# Reddit API credentials
reddit = praw.Reddit(

    user_agent="python3.11"
)

# Define parameters
subreddits = ['EASportsFC', 'Overwatch', 'RocketLeague','ApexLegends', 'DotA2', 'GlobalOffensive']
keywords_addiction = ["can't stop", "addicted", "hours played", "too much time", "hard to quit", "binge", "obsessed", "hooked"]
apex_ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Predator"]
dota2_ranks = ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"]
ranking = ["mmr", "rank", "ladder", "champion", "leaderboard", "competitive"]

# Normalize all rank keywords to lowercase for consistent matching
keywords_rank = [rank.lower() for rank in apex_ranks + dota2_ranks + ranking]

def is_self_report(post_text):
    """Check if post is likely a self-report based on certain keywords and length."""
    self_report_indicators = ["i ", "my ", "me ", "played", "stopped", "quit", "addicted", "time"]
    is_self_report = any(indicator in post_text for indicator in self_report_indicators)
    
    # Set a minimum length to filter out very short posts (e.g., announcements)
    if len(post_text) < 50 or len(post_text) > 400:
        return False
    return is_self_report

def scrape_reddit_posts(subreddits, keywords_addiction, keywords_rank, limit_per_keyword=500, retries=3):
    data = []
    
    # Loop through each subreddit
    for subreddit_name in tqdm.tqdm(subreddits):
        subreddit = reddit.subreddit(subreddit_name)
        
        # Fetch posts with addiction and rank keywords separately
        for keyword in tqdm.tqdm(keywords_addiction + keywords_rank):
            attempts = 0
            while attempts < retries:
                try:
                    print(f"Searching for keyword '{keyword}' in subreddit '{subreddit_name}'...")
                    
                    for post in subreddit.search(keyword, limit=limit_per_keyword):
                        title = post.title.lower()  # Normalize title to lowercase
                        body = post.selftext.lower()  # Normalize body to lowercase
                        comments = post.num_comments
                        upvotes = post.score
                        
                        # Convert Unix timestamp to date and time
                        post_datetime = datetime.utcfromtimestamp(post.created_utc)
                        post_date = post_datetime.strftime('%Y-%m-%d')
                        post_time = post_datetime.strftime('%H:%M:%S')
                        
                        # Check if post is a self-report
                        if not is_self_report(body):
                            continue
                        
                        # Check for keywords
                        addiction_related = any(add_keyword in body or add_keyword in title for add_keyword in keywords_addiction)
                        rank_related = any(rank_keyword in body or rank_keyword in title for rank_keyword in keywords_rank)
                        
                        # Append data
                        data.append({
                            "subreddit": subreddit_name,
                            "title": post.title,
                            "body": post.selftext,
                            "comments": comments,
                            "upvotes": upvotes,
                            "date": post_date,          # Add the post date
                            "time": post_time,          # Add the post time
                            "addiction_related": addiction_related,
                            "rank_related": rank_related
                        })
                    
                    break  # Exit the retry loop if successful
                
                except prawcore.exceptions.ServerError:
                    attempts += 1
                    if attempts < retries:
                        wait_time = 2 ** attempts  # Exponential backoff
                        print(f"Server error, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"Failed to retrieve posts for keyword '{keyword}' in subreddit '{subreddit_name}' after {retries} attempts.")
                        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df

# Run the scraper and save to CSV
df = scrape_reddit_posts(subreddits, keywords_addiction, keywords_rank, limit_per_keyword=200)
if df is not None:
    output_filename = f'self_report_reddit_gaming_posts_{datetime.now().strftime("%m-%d-%Y-%H:%M:%S")}.csv'
    df.to_csv(output_filename, index=False, quoting=csv.QUOTE_ALL, escapechar='\\')
    print(f"Data saved to {output_filename}")
else:
    print("No data was collected due to repeated errors.")
