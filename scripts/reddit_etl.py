import praw
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr
import psycopg2
from datetime import datetime, timedelta

def fetch_reddit_data(subreddit_name):
    reddit = praw.Reddit(
        client_id="EiwJLkPvrhTF-EqRsvGZUA",
        client_secret="9Cl9vQmyssHPX4KuaPhnVwTEIuHqUA",
        user_agent="data_eng_project"
    )
    
    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    SUBREDDIT = "datascience"
    TIME_FILTER = "day"
    LIMIT = None

    for post in subreddit.top(time_filter=TIME_FILTER, limit=LIMIT):
        post_time = datetime.utcfromtimestamp(post.created_utc)
        
        posts.append({
            "post_id": post.id,
            "title": post.title,
            "author": str(post.author),
            "upvotes": post.score,
            "created_utc": post_time.strftime("%Y-%m-%d %H:%M:%S"),  # Convert to string for PySpark
            "num_comments": post.num_comments,
            "subreddit": subreddit_name
        })

    return posts

def transform_with_pyspark(raw_data):
    # Initialize PySpark
    spark = SparkSession.builder \
        .appName("Reddit ETL") \
        .getOrCreate()

    # Load raw data into a PySpark DataFrame
    raw_df = spark.createDataFrame(raw_data)

    # Perform transformations
    transformed_df = raw_df.withColumn("title", expr("trim(initcap(title))")) \
                           .withColumnRenamed("num_comments", "comments_count") \
                           .filter(col("upvotes") > 10)  # Example filter: only keep posts with >10 upvotes

    # Convert the PySpark DataFrame back to a list of dictionaries
    transformed_data = [row.asDict() for row in transformed_df.collect()]
    spark.stop()

    return transformed_data

def save_to_postgresql(data, table_name, db_config):
    connection = psycopg2.connect(**db_config)
    cursor = connection.cursor()

    for record in data:
        cursor.execute(
            f"""
            INSERT INTO {table_name} 
            (post_id, title, author, upvotes, created_utc, comments_count, subreddit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING
            """,
            (record["post_id"], record["title"], record["author"],
             record["upvotes"], record["created_utc"], record["comments_count"], record["subreddit"])
        )

    connection.commit()
    cursor.close()
    connection.close()

if __name__ == "__main__":
    subreddit_name = "datascience"
    raw_data = fetch_reddit_data(subreddit_name)
    transformed_data = transform_with_pyspark(raw_data)

    db_config = {
        "dbname": "reddit_db",
        "user": "root",
        "password": "hello123",
        "host": "localhost",
        "port": 5432
    }

    save_to_postgresql(transformed_data, "processed_reddit_data", db_config)
