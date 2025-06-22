import streamlit as st
from PIL import Image
import pandas as pd
import snowflake.connector
import requests


# Wikipedia image fetcher
def get_wikipedia_image(place_name, city):
    search_url = "https://en.wikipedia.org/w/api.php"

    # Step 1: Search for the most relevant Wikipedia page
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{place_name} {city} India",
        "format": "json"
    }
    search_response = requests.get(search_url, params=search_params).json()
    search_results = search_response.get("query", {}).get("search", [])

    if not search_results:
        return None

    # Step 2: Get thumbnail for best result
    best_match_title = search_results[0]['title']
    image_params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "titles": best_match_title,
        "pithumbsize": 800
    }
    image_response = requests.get(search_url, params=image_params).json()
    pages = image_response.get("query", {}).get("pages", {})

    for page_id, page_data in pages.items():
        if "thumbnail" in page_data:
            return page_data["thumbnail"]["source"]
    return None


# Wikipedia summary fetcher (2 sentences max, ends with a full stop)
def get_wikipedia_summary(place_name, city):
    search_url = "https://en.wikipedia.org/w/api.php"

    # Search for the most relevant Wikipedia page
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{place_name} {city} India",
        "format": "json"
    }
    search_response = requests.get(search_url, params=search_params).json()
    search_results = search_response.get("query", {}).get("search", [])

    if not search_results:
        return None

    best_match_title = search_results[0]['title']

    # Fetch the extract/summary of the page intro
    summary_params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "titles": best_match_title
    }
    summary_response = requests.get(search_url, params=summary_params).json()
    pages = summary_response.get("query", {}).get("pages", {})

    for page_id, page_data in pages.items():
        if "extract" in page_data:
            extract = page_data["extract"].strip()
            sentences = extract.split('. ')
            if len(sentences) > 2:
                summary = '. '.join(sentences[:2]).strip()
                if not summary.endswith('.'):
                    summary += '.'
                return summary
            else:
                if not extract.endswith('.'):
                    extract += '.'
                return extract
    return None


# Snowflake DB connection
conn = snowflake.connector.connect(
    user='heenasubash',
    password='Snowflake12345',
    account='MDHACTW-AP13265',
    warehouse='COMPUTE_WH',
    database='INDIATOURISMAPP',
    schema='PUBLIC'
)

df = pd.read_sql("SELECT * FROM INDIATOURISMAPP.PUBLIC.CITIES WHERE LAT IS NOT NULL", conn)

query_ls = """
           SELECT Name, \
                  Domestic1920, \
                  Foreign1920, \
                  (Domestic1920 + Foreign1920) AS total_visitors_2019
           FROM INDIATOURISMAPP.PUBLIC.MOUNMENT
           WHERE LOWER(Name) NOT LIKE '%total%'
           ORDER BY total_visitors_2019 ASC LIMIT 10; \
           """
df_least_visited = pd.read_sql(query_ls, conn)
conn.close()

st.set_page_config(page_title="Travel Suggestion Planner", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "home"


def go_to(page):
    st.session_state.page = page
    st.rerun()


# HOME PAGE
def show_home():
    st.markdown("""
        <style>
            .banner-img {
                display: block;
                margin-left: auto;
                margin-right: auto;
                width: 100%;
                max-height: 200px;
                object-fit: cover;
            }
            .content-block {
                padding: 30px;
                margin-top: 10px;
                background-color: #f9f9f9;
                border-radius: 10px;
                text-align: center;
            }
            h1 {
                color: #c94f4f;
                font-size: 36px;
            }
            .small-text {
                font-size: 16px;
                line-height: 1.6;
            }
        </style>
    """, unsafe_allow_html=True)

    banner = Image.open("india-travel-attraction-banner-landmarks-tourism-traditional-culture-97612811.webp")
    st.image(banner, use_container_width=True)

    st.subheader("📍 Discover These Lesser-Known Gems!")
    st.markdown(
        "While the Taj Mahal grabs all the headlines, these monuments saw the **fewest visitors** in 2019–20. Perfect for crowd-free exploring:")

    st.table(df_least_visited["NAME"])

    st.markdown("""
        <div class="content-block">
            <h1>Travel Suggestion Planner</h1>
            <p class="small-text">
                Welcome to the <strong>Travel Suggestion Planner!</strong> This is a Simple, Smart, and Cultural Experience-Driven Trip Planner!
            </p>
            <p class="small-text">
                This planner uses <strong>real government data</strong> (from 
                <a href='https://data.gov.in' target='_blank'>data.gov.in</a>) to help you explore India’s hidden cultural treasures based on your interests.
            </p>
            <hr style="border: 1px solid #ccc;">
            <h3>What this website offers:</h3>
            <ul style="text-align: left; display: inline-block;" class="small-text">
                <li>Discover museums, heritage sites, monuments, and traditional art forms</li>
                <li>Plan a cultural visit in just a few clicks</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Start Quiz"):
        go_to("quiz")


# QUIZ PAGE
def show_quiz():
    st.title("Discover Places by Nature")
    st.markdown("Select a city and explore its unique nature spots")

    st.map(df.rename(columns={'LAT': 'latitude', 'LON': 'longitude'}), size=1)
    selected_city = st.sidebar.radio("Choose a city", df['CITY'].dropna().unique())

    city_nature_values = (
        df[df['CITY'] == selected_city]['NATURE']
        .dropna()
        .unique()
    )
    city_nature_options = [val.strip() for val in city_nature_values if val.strip() != ""]

    if city_nature_options:
        selected_nature = st.radio(f"What kind of nature do you want to explore in {selected_city}?",
                                   city_nature_options)
        st.success(f"You chose: {selected_nature}")
    else:
        st.warning(f"No nature data available for {selected_city}.")
        selected_nature = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Back to Home"):
            go_to("home")
    with col2:
        if selected_nature and st.button("Submit"):
            st.session_state.answers = {
                "city": selected_city,
                "nature": selected_nature,
            }
            go_to("itinerary")


# ITINERARY PAGE
def show_itinerary():
    st.title("🗺 Your Custom Itinerary")

    st.markdown("Based on your preferences, here’s a cultural experience tailored for you:")

    answers = st.session_state.get("answers", {})
    selected_city = answers.get("city")
    selected_nature = answers.get("nature")

    st.subheader(f"City: {selected_city}")
    st.subheader(f"Nature of Place: {selected_nature}")

    filtered_places = df[
        (df['CITY'] == selected_city) &
        (df['NATURE'] == selected_nature)
    ]

    if filtered_places.empty:
        st.warning("No matching places found in the database.")
    else:
        for _, row in filtered_places.iterrows():
            place_name = row['NAME']
            image_url = get_wikipedia_image(place_name, selected_city)
            summary = get_wikipedia_summary(place_name, selected_city)

            if image_url:
                st.image(image_url, caption=place_name)
            else:
                st.info(f"No image found for {place_name}")

            if summary:
                st.markdown(summary)
            else:
                st.markdown("_No description available._")

            st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Quiz"):
            go_to("quiz")
    with col2:
        if st.button("Start Over"):
            st.session_state.page = "home"
            st.session_state.answers = {}
            st.rerun()


# MAIN NAVIGATION
if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "quiz":
    show_quiz()
elif st.session_state.page == "itinerary":
    show_itinerary()
