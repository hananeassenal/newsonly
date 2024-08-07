import streamlit as st
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# Function to check if user is logged in
def check_login():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("You need to be logged in to view this page.")
        st.write("[Login](login.py)")
        st.stop()

def display_saved_articles():
    st.title("Saved Articles")
    
    # MongoDB connection
    try:
        client = MongoClient("mongodb+srv://hananeassendal:RebelDehanane@cluster0.6bgmgnf.mongodb.net/Newsapp?retryWrites=true&w=majority")
        db = client.Newsapp
        saved_articles_collection = db.SavedArticles
    except OperationFailure as e:
        st.error(f"Authentication failed: {e.details['errmsg']}")
        return
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return
    
    # Fetch saved articles from MongoDB
    articles = list(saved_articles_collection.find().sort("date", -1))
    
    if len(articles) > 0:
        for article in articles:
            col1, col2 = st.columns([6, 1])  # Create two columns
            
            with col1:
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
                    <a href="{article['url']}" target="_blank" style="text-decoration: none; color: inherit;">
                        <h3>{article['title']}</h3>
                    </a>
                    <img src="{article['image_url']}" alt="{article['title']}" style="width:100%; height:auto;">
                    <p>Date: {article['date'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>{article['summary']}</p>
                    <p>For more please visit <a href="{article['url']}" target="_blank">this link</a></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add a delete button below the "For more please visit" link
                if st.button(f"Delete Article: {article['title']}", key=article['url']):
                    delete_article(article['url'])
                    st.success(f"Article deleted: {article['title']}")
                    st.experimental_rerun()  # Refresh the page
    else:
        st.write("No saved articles found.")

def delete_article(url):
    # MongoDB connection
    try:
        client = MongoClient("mongodb+srv://hananeassendal:RebelDehanane@cluster0.6bgmgnf.mongodb.net/Newsapp?retryWrites=true&w=majority")
        db = client.Newsapp
        saved_articles_collection = db.SavedArticles
    except OperationFailure as e:
        st.error(f"Authentication failed: {e.details['errmsg']}")
        return
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return

    # Delete the article from MongoDB
    result = saved_articles_collection.delete_one({"url": url})
    if result.deleted_count == 0:
        st.error("Failed to delete the article. It might not exist.")

def main():
    check_login()  # Ensure the user is logged in
    display_saved_articles()

if __name__ == "__main__":
    main()
