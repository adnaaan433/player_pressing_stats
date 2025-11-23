import streamlit as st

from fucntions import get_competitions, get_matches_id, plot_top10_pressers

st.set_page_config(page_title="Football Pressure Analysis", layout="wide")

st.title("⚽ Football Player Pressure Analysis")
st.markdown("---")

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
    
    if team_name and st.button("🔍 Analyze Top 10 Pressers", type="primary", use_container_width=True):
        with st.spinner("Fetching data and generating visualization..."):
            try:
                fig, pdf = plot_top10_pressers(selected_competition, selected_season, team_name)
                st.pyplot(fig)
                
                st.success("✅ Visualization generated successfully!")

                # st.dataframe(pdf)
                
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
        - Interactive visualization with dark modern design
        
        **How to use:**
        1. Select a competition from the dropdown
        2. Select a season
        3. Select a team from the available teams
        4. Click the "Analyze" button
        """)

else:
    st.error("Failed to load competitions data. Please check your API credentials.")