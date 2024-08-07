import time
import streamlit as st
import requests
from newspaper import Article
from llama_index.llms.groq import Groq
from datetime import datetime
from pymongo import MongoClient, errors

# Groq API Key
GROQ_API_KEY = "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"
llm = Groq(model="llama3-70b-8192", api_key=GROQ_API_KEY)  # 8 000 tokens 
# llm = Groq(model="mixtral-8x7b-32768", api_key=GROQ_API_KEY)  # 32 000 tokens

# Predefined queries by country
queries_by_country = {
    "Brazil": ["Brazil hydro Drought", "Brazil low hydro", "Sao Paolo Blackouts", "Brazil blackouts"],
    "Dubai": ["Jebel Ali Dubai Port constraints", "Jebel Ali Dubai Port storm", "Jebel Ali Dubai Port flood"],
    "Saudi": ["Saudi new data centre", "Saudi new data center"],
    "Shanghai": ["Shanghai port congestion", "Shanghai port constraint", "Shanghai port delays"]
}

# queries_by_country = {
#     "Brazil": ["Brazil", "Brazil news", "brazil port"],
#     "Dubai": ["Dubai", "Dubai news", "dubai port"],
#     "Saudi": ["Saudi new data center", "Saudi"],
#     "Shanghai": ["Shanghai port", "Shanghai news", "Shanghai"]
# }

# Function to check if user is logged in
def check_login():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("You need to be logged in to view this page.")
        st.write("[Login](login.py)")
        st.stop()

def fetch_summary(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = article.text

        # Use Groq model for summarization
        prompt = f"Summarize the following text:\n\n{text}"
        summary = llm.complete(prompt)
        
        return f"{summary}\n\nFor more please visit {url}"
    except Exception as e:
        return f"For more please visit {url}"

def fetch_articles(query):
    url = "https://newsnow.p.rapidapi.com/newsv2"
    payload = {
        "query": query,
        "time_bounded": True,
        "from_date": "01/01/2023",
        "to_date": "30/12/2024",
        "location": "us",
        "language": "en",
        "page": 1
    }
    headers = {
        "x-rapidapi-key": "3f0b7a04abmshe28889e523915e1p12b5dcjsn4014e40913e8",
        "x-rapidapi-host": "newsnow.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 429:
            #st.warning("Too many requests. Waiting for 1 minute before retrying...")
            time.sleep(5)
            response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        json_data = response.json()
        if 'news' in json_data and json_data['news']:
            articles = []
            for article in json_data['news']:
                title = article.get('title', '')
                image_url = article.get('top_image', '')
                date = article.get('date', '')
                article_url = article.get('url', '')
                
                articles.append({
                    'title': title,
                    'image_url': image_url,
                    'date': datetime.strptime(date, '%a, %d %b %Y %H:%M:%S GMT'),
                    'url': article_url
                })
            
            articles.sort(key=lambda x: x['date'], reverse=True)
            
            for article in articles:
                with st.spinner(f"Processing article: {article['title']}"):
                    summary = fetch_summary(article['url'])
                    article['summary'] = summary
                    display_article(article)
                    st.write("---")
        else:
            st.error("No articles found.")
    # else:
    #     st.error(f"API request error: {response.status_code} - {response.reason}")

def display_article(article):
    st.markdown(f"""
    <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
        <a href="{article['url']}" target="_blank" style="text-decoration: none; color: inherit;">
            <h3>{article['title']}</h3>
        </a>
        <img src="{article['image_url']}" alt="{article['title']}" style="width:100%; height:auto;">
        <p>Date: {article['date'].strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>{article['summary']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(f"Save Article: {article['title']}", key=article['url']):
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

# def main():
#     check_login()  # Ensure the user is logged in

#     st.header(f"News Articles")
    
#     # Ensure country is set from session state
#     if 'country' not in st.session_state:
#         st.session_state.country = "Brazil"  # Default country if not set

#     # Get list of countries
#     countries = ["Brazil", "Dubai", "Saudi", "Shanghai"]

#     # Ensure the session state country is valid
#     if st.session_state.country not in countries:
#         st.session_state.country = "Brazil"

#     # Get the index of the default country
#     default_index = countries.index(st.session_state.country)

#     country = st.selectbox("Select Country", countries, index=default_index)
#     st.session_state.country = country

#     st.subheader("Search News")
#     query = st.text_input("Enter search query")

#     if query:
#         fetch_articles(query)
#     else:
#         queries = queries_by_country.get(st.session_state.country, [])
#         for query in queries:
#             fetch_articles(query)

# if __name__ == "__main__":
#     main()

def main():
    check_login()  # Ensure the user is logged in

    st.header("News Articles")
    
    # Ensure country is set from session state
    if 'country' not in st.session_state:
        st.session_state.country = "Brazil"  # Default country if not set

    # Get list of countries
    countries = ["Brazil", "Dubai", "Saudi", "Shanghai"]

    # Ensure the session state country is valid
    if st.session_state.country not in countries:
        st.session_state.country = "Brazil"

    # Get the index of the default country
    default_index = countries.index(st.session_state.country)

    # Select country and update session state
    country = st.selectbox("Select Country", countries, index=default_index, key='country_select')

    # Check if the selected country is different from the session state
    if country != st.session_state.country:
        st.session_state.country = country
        st.rerun()  # Trigger rerun if country is changed

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

