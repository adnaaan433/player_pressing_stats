import streamlit as st

from fucntions import get_competitions, get_matches_id, plot_top10_pressers

st.set_page_config(page_title="Football Pressure Analysis", layout="wide")

st.title("⚽ Football Player Pressure Analysis")
st.markdown("---")

# Check for secrets
if "statsbomb" not in st.secrets:
    st.error("⚠️ API Credentials not found!")
    st.info("""
    **To fix this on Streamlit Cloud:**
    1. Go to your app dashboard.
    2. Click on 'Manage app' (bottom right) or 'Settings' (top right menu).
    3. Go to the **Secrets** section.
    4. Paste your credentials in TOML format:
    ```toml
    [statsbomb]
    username = "your_email@example.com"
    password = "your_password"
    ```
    """)
    st.stop()

@st.cache_data
def load_competitions():
    return get_competitions()

@st.cache_data
def load_teams(competition_id, season_id):
    mdf = get_matches_id(competition_id, season_id)
    if mdf is not None:
        home_teams = set(mdf['home_team_name'].unique())
        away_teams = set(mdf['away_team_name'].unique())
        all_teams = sorted(list(home_teams.union(away_teams)))
        return all_teams
    return []

cdf = load_competitions()

if cdf is not None:
    col1, col2 = st.columns(2)
    
    with col1:
        competition_names = sorted(cdf['competition_name'].unique())
        selected_competition = st.selectbox(
            "Select Competition",
            options=competition_names,
            index=0
        )
    
    with col2:
        filtered_seasons = cdf[cdf['competition_name'] == selected_competition]['season_name'].unique()
        selected_season = st.selectbox(
            "Select Season",
            options=sorted(filtered_seasons, reverse=True),
            index=0
        )
    
    competition_id = cdf[
        (cdf['competition_name'] == selected_competition) & 
        (cdf['season_name'] == selected_season)
    ]['competition_id'].iloc[0]
    
    season_id = cdf[
        (cdf['competition_name'] == selected_competition) & 
        (cdf['season_name'] == selected_season)
    ]['season_id'].iloc[0]
    
    teams = load_teams(str(competition_id), str(season_id))
    
    if teams:
        team_name = st.selectbox(
            "Select Team",
            options=teams,
            index=0
        )
    else:
        st.warning("No teams found for this competition and season.")
        team_name = None
    
    st.markdown("---")
    
    per_90 = st.toggle("Show Per 90 Stats", value=False)
    
    min_minutes = 0
    if per_90:
        min_minutes = st.slider("Minimum Minutes Played", min_value=500, max_value=1500, value=500, step=100)
    
    if team_name and st.button("🔍 Analyze Top 10 Pressers", type="primary", use_container_width=True):
        with st.spinner("Fetching data and generating visualization..."):
            try:
                fig, pdf = plot_top10_pressers(selected_competition, selected_season, team_name, per_90=per_90, min_minutes=min_minutes)
                
                if fig:
                    st.pyplot(fig)
                    st.success("✅ Visualization generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Please try selecting different options.")
    
    with st.expander("ℹ️ About this app"):
        st.markdown("""
        This app analyzes player pressure statistics from StatsBomb data.
        
        **Features:**
        - Select any available competition and season
        - Choose from teams that played in that competition/season
        - View top 10 players by total pressures (pressures + counter-pressures)
        - Toggle "Per 90" stats and filter by minimum minutes played
        - Interactive visualization with dark modern design
        
        **How to use:**
        1. Select a competition from the dropdown
        2. Select a season
        3. Select a team from the available teams
        4. Toggle "Show Per 90 Stats" if desired (and adjust minimum minutes)
        5. Click the "🔍 Analyze" button
        """)
    
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #888888; padding: 10px;'>
            <p>
                Made by <a href="https://twitter.com/adnaaan433" target="_blank" style="text-decoration: none; color: #00d9ff;">@adnaaan433</a>
                | Special thanks to <a href="https://twitter.com/mckayjohns" target="_blank" style="text-decoration: none; color: #ff6b35;">@mckayjohns</a> for his amazing tutorial
            </p>
            <p style="font-size: 0.9em; margin-top: 5px;">
                Special Thanks to <a href="https://twitter.com/MichaelGMackin" target="_blank" style="text-decoration: none; color: #ffd700;">@MichaelGMackin</a> for providing the premium subscription of Statsbomb data
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.error("Failed to load competitions data. Please check your API credentials.")