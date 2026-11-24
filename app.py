import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Netflix EDA Dashboard",
    page_icon="🎬",
    layout="wide"
)

DATA_PATH = Path(__file__).parent / "netflix_titles.csv"

# -----------------------------
# Load and prepare data
# -----------------------------
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)

    data["date_added"] = pd.to_datetime(
        data["date_added"].astype("string").str.strip(),
        format="%B %d, %Y",
        errors="coerce"
    )

    data["release_year"] = pd.to_numeric(data["release_year"], errors="coerce")

    data["duration_minutes"] = pd.to_numeric(
        data["duration"].astype("string").str.extract(r"(\d+)\s*min", expand=False),
        errors="coerce"
    )

    data["country"] = data["country"].fillna("Unknown")
    data["rating"] = data["rating"].fillna("Unknown")
    data["listed_in"] = data["listed_in"].fillna("Unknown")
    data["type"] = data["type"].fillna("Unknown")

    return data


try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "Could not find netflix_titles.csv. Place the CSV file in the same folder as app.py."
    )
    st.stop()

# -----------------------------
# Dashboard heading
# -----------------------------
st.title("🎬 Netflix Movies & TV Shows – EDA Dashboard")
st.write(
    "An interactive analysis of Netflix titles, including content types, "
    "release trends, countries, genres, ratings, and movie durations."
)

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filter the dashboard")

type_options = sorted(df["type"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect(
    "Select content type",
    options=type_options,
    default=type_options
)

min_year = int(df["release_year"].min())
max_year = int(df["release_year"].max())

selected_years = st.sidebar.slider(
    "Select release year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

filtered_df = df[
    (df["type"].isin(selected_types))
    & (df["release_year"].between(selected_years[0], selected_years[1]))
].copy()

if filtered_df.empty:
    st.warning("No titles match these filters. Please change your selections.")
    st.stop()

# -----------------------------
# Four key metrics
# -----------------------------
total_titles = len(filtered_df)
movie_count = int((filtered_df["type"] == "Movie").sum())
tv_count = int((filtered_df["type"] == "TV Show").sum())

country_count = (
    filtered_df.loc[filtered_df["country"] != "Unknown", "country"]
    .str.split(", ")
    .explode()
    .nunique()
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Titles", f"{total_titles:,}")
col2.metric("Movies", f"{movie_count:,}")
col3.metric("TV Shows", f"{tv_count:,}")
col4.metric("Countries Represented", f"{country_count:,}")

st.divider()

# -----------------------------
# Graph 1: Movies vs TV Shows
# -----------------------------
st.subheader("1. Content Type Distribution")
type_counts = filtered_df["type"].value_counts().reset_index()
type_counts.columns = ["Content Type", "Number of Titles"]

fig_type = px.bar(
    type_counts,
    x="Content Type",
    y="Number of Titles",
    color="Content Type",
    title="Movies vs TV Shows",
    text="Number of Titles"
)
fig_type.update_layout(showlegend=False)
st.plotly_chart(fig_type, use_container_width=True)

# -----------------------------
# Graph 2: Titles by release year
# -----------------------------
st.subheader("2. Titles by Release Year")
year_counts = (
    filtered_df.groupby(["release_year", "type"])
    .size()
    .reset_index(name="Number of Titles")
)
fig_year = px.line(
    year_counts,
    x="release_year",
    y="Number of Titles",
    color="type",
    markers=True,
    title="Netflix Titles by Release Year",
    labels={"release_year": "Release Year", "type": "Content Type"}
)
st.plotly_chart(fig_year, use_container_width=True)

# -----------------------------
# Graph 3: Top countries
# -----------------------------
st.subheader("3. Top 10 Countries")
country_data = filtered_df.loc[
    filtered_df["country"] != "Unknown", ["country"]
].copy()
country_data["country"] = country_data["country"].str.split(", ")
country_counts = (
    country_data.explode("country")["country"]
    .value_counts()
    .head(10)
    .sort_values()
    .reset_index()
)
country_counts.columns = ["Country", "Number of Titles"]

fig_country = px.bar(
    country_counts,
    x="Number of Titles",
    y="Country",
    orientation="h",
    title="Top 10 Countries by Number of Titles",
    text="Number of Titles"
)
st.plotly_chart(fig_country, use_container_width=True)

# -----------------------------
# Graph 4: Top genres/categories
# -----------------------------
st.subheader("4. Most Common Genres")
genre_data = filtered_df[["listed_in"]].copy()
genre_counts = (
    genre_data["listed_in"].str.split(", ").explode()
    .value_counts()
    .head(10)
    .sort_values()
    .reset_index()
)
genre_counts.columns = ["Genre", "Number of Titles"]

fig_genre = px.bar(
    genre_counts,
    x="Number of Titles",
    y="Genre",
    orientation="h",
    title="Top 10 Netflix Genres",
    text="Number of Titles"
)
st.plotly_chart(fig_genre, use_container_width=True)

# -----------------------------
# Graph 5: Movie duration
# -----------------------------
st.subheader("5. Movie Duration Distribution")
movie_durations = filtered_df.loc[
    (filtered_df["type"] == "Movie")
    & filtered_df["duration_minutes"].notna(),
    ["duration_minutes"]
]

if not movie_durations.empty:
    fig_duration = px.histogram(
        movie_durations,
        x="duration_minutes",
        nbins=30,
        title="Distribution of Movie Durations",
        labels={"duration_minutes": "Duration (minutes)"},
    )
    st.plotly_chart(fig_duration, use_container_width=True)
else:
    st.info("No movie duration data is available for the selected filters.")

# -----------------------------
# Graph 6: Ratings
# -----------------------------
st.subheader("6. Content Ratings")
rating_counts = (
    filtered_df["rating"].value_counts()
    .head(10)
    .sort_values()
    .reset_index()
)
rating_counts.columns = ["Rating", "Number of Titles"]

fig_rating = px.bar(
    rating_counts,
    x="Number of Titles",
    y="Rating",
    orientation="h",
    title="Top Content Ratings",
    text="Number of Titles"
)
st.plotly_chart(fig_rating, use_container_width=True)

# -----------------------------
# Findings
# -----------------------------
st.divider()
st.header("Key Findings")

st.markdown("""
- The dataset contains both Movies and TV Shows, allowing comparison between the two content types.
- Country and genre fields can contain multiple values for one title, so each listed country or genre is counted separately in those charts.
- Movie runtime is analyzed in minutes; TV Show season counts are not mixed into the movie-duration chart.
- Use the sidebar filters to explore how the charts and key numbers change for different release-year ranges and content types.
""")

# -----------------------------
# Raw data
# -----------------------------
st.divider()
show_raw_data = st.checkbox("Show raw data")

if show_raw_data:
    st.subheader("Raw Netflix Dataset")
    st.dataframe(filtered_df, use_container_width=True)
    st.caption(f"Showing {len(filtered_df):,} filtered rows.")
