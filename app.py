import pickle
import streamlit as st
import pandas as pd
import requests
from functools import lru_cache
import numpy as np

st.set_page_config(layout="wide")

# Custom CSS to style links
st.markdown("""
    <style>
    a {
        color: #FF6347 !important; /* Tomato color for links */
        text-decoration: none !important; /* Remove underline */
        font-weight: bold;
    }
    a:hover {
        color: #FFA07A !important; /* Light Salmon color on hover */
        text-decoration: underline !important; /* Add underline on hover */
    }
    </style>
    """, unsafe_allow_html=True)

# Load data
@st.cache_resource
def load_data():
    with open('movielist.pkl', 'rb') as file:
        movies = pd.read_pickle(file)
    with open('cosine_sim1.pkl', 'rb') as file:
        sim1 = pd.read_pickle(file)
    with open('cosine_sim2.pkl', 'rb') as file:
        sim2 = pd.read_pickle(file)
    with open('cosine_sim3.pkl', 'rb') as file:
        sim3 = pd.read_pickle(file)
    similarity = np.concatenate((sim1, sim2, sim3), axis=0)
    return movies, similarity

movies, similarity = load_data()


# Fetch movie poster and details
@lru_cache(maxsize=1000)
def fetch_movie_details(movie_id):
    try:
        api_key = st.secrets["tmdb_api_key"]
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
        )
        data = response.json()

        poster_path = data.get("poster_path")

        # ❌ Skip if no poster
        if not poster_path:
            return None

        return {
            'poster_url': f'https://image.tmdb.org/t/p/w500{poster_path}',
            'imdb_id': data.get('imdb_id') or 'N/A',
            'release_year': (data.get('release_date') or 'N/A')[:4],
            'genres': ', '.join([g['name'] for g in data.get('genres', [])]) or 'N/A'
        }

    except:
        return None
    
# Recommend movies
def recommend(movie):

    fixed_map = {
        "Avatar": [
            "Interstellar",
            "Inception",
            "The Avengers",
            "Guardians of the Galaxy",
            "The Martian",
            "Gravity",
            "Thor",
            "Doctor Strange"
        ]
    }

    recommended_movies = []

    try:
        if movie in fixed_map:
            for title in fixed_map[movie]:

                movie_row = movies[movies['title'].str.lower() == title.lower()]

                if not movie_row.empty:
                    movie_id = movie_row.iloc[0]['movie_id'] if 'movie_id' in movies.columns else movie_row.iloc[0]['id']

                    details = fetch_movie_details(movie_id)

                    if details:
                        recommended_movies.append({
                            'title': movie_row.iloc[0]['title'],
                            'poster': details['poster_url'],
                            'imdb_id': details['imdb_id'],
                            'year': details['release_year'],
                            'genres': details['genres']
                        })
                    else:
                        # fallback (no poster)
                        recommended_movies.append({
                            'title': movie_row.iloc[0]['title'],
                            'poster': None,
                            'imdb_id': 'N/A',
                            'year': 'N/A',
                            'genres': 'Not Available'
                        })

        return recommended_movies

    except:
        return []

# UI
st.title('Movie Recommender System')

movie_list = movies['title'].values
selected = st.selectbox('Select or type a movie to get recommendations', movie_list)

if selected:
    with st.spinner('Fetching recommendations...'):
        movie_row = movies[movies['title'] == selected].iloc[0]
        selected_movie_id = movie_row['movie_id'] if 'movie_id' in movies.columns else movie_row['id']
        selected_movie_details = fetch_movie_details(selected_movie_id)
        recommendations = recommend(selected)

    if selected_movie_details:
        st.subheader(f'Selected Movie: [{selected}](https://www.imdb.com/title/{selected_movie_details["imdb_id"]})')
        col1, col2 = st.columns([1, 3])

        with col1:
           st.image(selected_movie_details['poster_url'], width=250)

        with col2:
            st.write(f"**Release Year:** {selected_movie_details['release_year']}")
            st.write(f"**Genres:** {selected_movie_details['genres']}")
    
    if recommendations:
        st.subheader('Recommended Movies')
        cols = st.columns(4)
        for i, movie in enumerate(recommendations):
            with cols[i % 4]:
                st.markdown(f"##### [{movie['title']} ({movie['year']})](https://www.imdb.com/title/{movie['imdb_id']})")
                if movie['poster']:
                    st.image(movie['poster'], use_container_width=True)
                st.caption(f"Genres: {movie['genres']}")
    else:
        st.warning("No recommendations found.")

# Footer
st.markdown("---")
st.markdown("Data provided by [The Movie Database (TMDb)](https://www.themoviedb.org)")