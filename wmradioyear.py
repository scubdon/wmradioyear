import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Cache data loading for performance
def load_data(path_or_buffer):
    df = pd.read_csv(path_or_buffer, parse_dates=['timestamp'])
    # Rename artwork column for clarity
    if 'artwork_large' in df.columns:
        df = df.rename(columns={'artwork_large': 'artwork_url'})
    # Filter out ads and promos
    mask = ~((df['artist'] == 'The WMW Radio Network') | (df['song'] == 'Promo'))
    df = df.loc[mask].copy()
    # Extract day of week and hour
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['hour'] = df['timestamp'].dt.hour
    return df

@st.cache_data

def get_data(uploaded_file):
    if uploaded_file is not None:
        return load_data(uploaded_file)
    # fallback to local file if no upload
    return load_data('https://b2.richardcooney.com/wmradiodata_yr.csv')

# Sidebar: Data upload and filters
st.sidebar.title("Filters")
uploaded = st.sidebar.file_uploader("Upload playback CSV", type="csv")
df = get_data(uploaded)

days = st.sidebar.multiselect(
    "Select days of week", 
    options=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
    default=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
)
hour_range = st.sidebar.slider(
    "Select hour range", 0, 24, (14, 22)
)

# Filter data based on user selections
def filter_data(df, days, hour_range):
    start, end = hour_range
    return df[(df['day_of_week'].isin(days)) & (df['hour'].between(start, end))]

filtered = filter_data(df, days, hour_range)

# Main dashboard
st.title("Walmart Radio Yearly Playback Dashboard")
st.markdown(
    "Use the filters to select the days and hours you work, and explore what songs and artists you would hear over a year's worth of shifts."
)

# Summary metrics
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Plays", len(filtered))
col2.metric("Unique Songs", filtered['song'].nunique())
col3.metric("Unique Artists", filtered['artist'].nunique())

# Top songs
st.subheader("Top 30 Played Songs")
top_songs = filtered['song'].value_counts().head(30)
st.bar_chart(top_songs)

# Top artists
st.subheader("Top 30 Played Artists")
top_artists = filtered['artist'].value_counts().head(30)
st.bar_chart(top_artists)

# Artwork display for top songs
st.subheader("Artwork for Top Songs")
top_song_names = top_songs.index.tolist()
cols = st.columns(min(len(top_song_names), 5))
for col, song in zip(cols, top_song_names):
    art_url = filtered.loc[filtered['song'] == song, 'artwork_url'].iloc[0]
    col.image(art_url, caption=song, use_column_width=True)

# Average time between plays for top songs
st.subheader("Average Hours Between Plays (Top Songs)")
avg_data = []
for song in top_song_names:
    times = filtered.loc[filtered['song'] == song, 'timestamp'].sort_values()
    diffs = times.diff().dropna().dt.total_seconds() / 3600
    avg = diffs.mean() if not diffs.empty else np.nan
    avg_data.append({'song': song, 'avg_hours_between_plays': round(avg, 2)})
avg_df = pd.DataFrame(avg_data)
st.dataframe(avg_df)

# Heatmap of play frequency by day and hour
st.subheader("Hourly Play Frequency Heatmap")
import altair as alt
heatmap_df = (
    filtered.groupby(['day_of_week', 'hour'])
    .size()
    .reset_index(name='count')
)
heatmap = alt.Chart(heatmap_df).mark_rect().encode(
    x=alt.X('hour:O', title='Hour of Day'),
    y=alt.Y('day_of_week:O', title='Day of Week', sort=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']),
    color=alt.Color('count:Q', title='Plays')
).properties(width=600, height=300)
st.altair_chart(heatmap, use_container_width=True)

# Additional ideas: Play distribution over time
st.subheader("Plays Over Time")
daily_counts = filtered.set_index('timestamp').resample('D').size()
st.line_chart(daily_counts)

# End of dashboard
st.markdown("---")
st.write("Built with ❤️ using Streamlit")