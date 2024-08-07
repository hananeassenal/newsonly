import requests
import json
import streamlit as st
from newspaper import Article
from llama_index.llms.groq import Groq
from datetime import datetime, timedelta
import re
from pymongo import MongoClient, errors
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Groq API Key
GROQ_API_KEY = "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"
llm = Groq(model="llama3-70b-8192", api_key=GROQ_API_KEY)

# Predefined queries by country
queries_by_country = {
    "Brazil": ["Brazil hydro Drought", "Brazil low hydro", "Sao Paolo Blackouts", "Brazil blackouts"],
    "Dubai": ["Jebel Ali Dubai Port constraints", "Jebel Ali Dubai Port storm", "Jebel Ali Dubai Port flood"],
    "Saudi": ["Saudi new data centre", "Saudi new data center"],
    "Shanghai": ["Shanghai port congestion", "Shanghai port constraint", "Shanghai port delays"]
}

def parse_relative_date(relative_date_str):
    now = datetime.now()
    patterns = {
        'hour': r'(\d+) hours? ago',
        'day': r'(\d+) days? ago',
        'month': r'(\d+) months? ago',
        'year': r'(\d+) years? ago'
    }
    for unit, pattern in patterns.items():
        match = re.search(pattern, relative_date_str)
        if match:
            amount = int(match.group(1))
            if unit == 'hour':
                return now - timedelta(hours=amount)
            elif unit == 'day':
                return now - timedelta(days=amount)
            elif unit == 'month':
                return now - timedelta(days=amount * 30)
            elif unit == 'year':
                return now - timedelta(days=amount * 365)
    return now

def fetch_summary(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = article.text
        prompt = f"Summarize the following text:\n\n{text}"
        summary = llm.complete(prompt)
        return f"{summary}\n\nFor more please visit {url}"
    except Exception as e:
        logger.error(f"Failed to fetch summary for {url}: {e}")
        return f"For more please visit {url}"

def fetch_articles(query):
    country_code = {
        "Brazil": "br",
        "Dubai": "ae",
        "Saudi": "sa",
        "Shanghai": "cn"
    }.get(st.session_state.country, "us")

    url = "https://google.serper.dev/news"
    payload = json.dumps({
        "q": query,
        "gl": country_code,
        "num": 20,  # Adjust the number of results if needed
        "tbs": "qdr:m"
    })
    headers = {
        'X-API-KEY': '72961141ec55e220e7bfac56098cc1627f49bd9b',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 429:
            st.warning("Too many requests. Waiting for 5 seconds before retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
            response = requests.post(url, headers=headers, data=payload)

        response.raise_for_status()  # Raise an HTTPError for bad responses

        json_data = response.json()
        logger.info(f"API Response: {json.dumps(json_data, indent=2)}")

        if 'news' in json_data and json_data['news']:
            articles = []
            for article in json_data['news']:
                title = article.get('title', '')
                snippet = article.get('snippet', '')
                article_url = article.get('link', '')
                date_str = article.get('date', '')

                if "ago" in date_str:
                    date = parse_relative_date(date_str)
                else:
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    except ValueError:
                        date = datetime.now()

                articles.append({
                    'title': title,
                    'snippet': snippet,
                    'date': date,
                    'url': article_url
                })

            articles.sort(key=lambda x: x['date'], reverse=True)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(fetch_summary, article['url']): article for article in articles}
                for future in as_completed(futures):
                    article = futures[future]
                    with st.spinner(f"Processing article: {article['title']}"):
                        try:
                            summary = future.result()
                            article['summary'] = summary
                            display_article(article)
                            st.write("---")
                        except Exception as exc:
                            logger.error(f"Generated an exception: {exc}")
        else:
            st.warning("No articles found.")
    except requests.RequestException as e:
        st.error(f"API request error: {e}")

def display_article(article):
    button_key = f"save_{article['url']}"
    st.markdown(f"""
    <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
        <a href="{article['url']}" target="_blank" style="text-decoration: none; color: inherit;">
            <h3>{article['title']}</h3>
        </a>
        <p>{article['snippet']}</p>
        <p>Date: {article['date'].strftime('%Y-%m-%d')}</p>
        <p>{article['summary']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(f"Save Article: {article['title']}", key=button_key):
        save_article(article)
        st.success(f"Article saved: {article['title']}")

def save_article(article):
    try:
        client = MongoClient("mongodb+srv://hananeassendal:RebelDehanane@cluster0.6bgmgnf.mongodb.net/Newsapp?retryWrites=true&w=majority")
        db = client.Newsapp
        saved_articles_collection = db.SavedArticles
    except errors.OperationFailure as e:
        st.error(f"Authentication failed: {e.details['errmsg']}")
        return
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return

    saved_articles_collection.update_one(
        {"url": article['url']},
        {"$set": article},
        upsert=True
    )

def main():
    st.title("News Articles")

    if 'country' not in st.session_state:
        st.session_state.country = "France"

    country_options = ["Dubai", "Saudi", "Shanghai", "Brazil"]
    try:
        country_index = country_options.index(st.session_state.country)
    except ValueError:
        country_index = 0

    country = st.selectbox("Select Country", country_options, index=country_index)
    
    if country != st.session_state.country:
        st.session_state.country = country
        st.rerun()

    st.subheader("Search News")
    query = st.text_input("Enter search query")

    if query:
        fetch_articles(query)
    else:
        queries = queries_by_country.get(st.session_state.country, [])
        for query in queries:
            fetch_articles(query)

if __name__ == "__main__":
    main()
