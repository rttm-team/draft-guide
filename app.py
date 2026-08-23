import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import json

# Set Page Config for a professional look
st.set_page_config(
    page_title="2026-27 Fantasy Hockey Draft Companion",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #3B82F6;
    }
    .sleeper-card {
        background-color: #FEF3C7;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #F59E0B;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. SESSION STATE INITIALIZATION ---
if 'drafted_players' not in st.session_state:
    st.session_state.drafted_players = set()
if 'draft_log' not in st.session_state:
    st.session_state.draft_log = []

# --- 2. PRE-SEEDED FANTASY DATABASE ---
# Curated list of elite prospects, snipers, and sleepers across 2023-2026 classes
@st.cache_data
def get_preseeded_prospects():
    return pd.DataFrame([
        # 2026 Class
        {"Name": "Gavin McKenna", "Year": 2026, "Round": 1, "Pick": 1, "NHL_Team": "Toronto Maple Leafs", "Pos": "F", "Projected_Pts": 88.5, "Projected_PPP": 32.0, "Goals_Last_Yr": 15, "Pts_Last_Yr": 51, "League": "NCAA", "Tier": "Elite", "Sniper_Score": 8.5, "Sleeper_Score": 1.0, "Notes": "Franchise winger. Projects for immediate 1PP role."},
        {"Name": "Ivar Stenberg", "Year": 2026, "Round": 1, "Pick": 2, "NHL_Team": "San Jose Sharks", "Pos": "F", "Projected_Pts": 74.0, "Projected_PPP": 24.5, "Goals_Last_Yr": 11, "Pts_Last_Yr": 33, "League": "SHL", "Tier": "Elite", "Sniper_Score": 8.0, "Sleeper_Score": 1.0, "Notes": "Outstanding Swedish playmaker; elite vision and power-play utility."},
        {"Name": "Daxon Rudolph", "Year": 2026, "Round": 1, "Pick": 4, "NHL_Team": "Buffalo Sabres", "Pos": "D", "Projected_Pts": 58.0, "Projected_PPP": 22.0, "Goals_Last_Yr": 28, "Pts_Last_Yr": 78, "League": "WHL", "Tier": "PP Quarterback", "Sniper_Score": 8.0, "Sleeper_Score": 2.0, "Notes": "Elite offensive defenseman. High-volume shooter and pure 1PP QB."},
        {"Name": "Carson Carels", "Year": 2026, "Round": 1, "Pick": 6, "NHL_Team": "Calgary Flames", "Pos": "D", "Projected_Pts": 52.5, "Projected_PPP": 18.0, "Goals_Last_Yr": 20, "Pts_Last_Yr": 73, "League": "WHL", "Tier": "PP Quarterback", "Sniper_Score": 7.5, "Sleeper_Score": 2.0, "Notes": "Highly mobile blueliner. Elite puck distributor built to run a power play."},
        {"Name": "Markus Ruck", "Year": 2026, "Round": 2, "Pick": 39, "NHL_Team": "Pittsburgh Penguins", "Pos": "F", "Projected_Pts": 65.0, "Projected_PPP": 20.0, "Goals_Last_Yr": 21, "Pts_Last_Yr": 108, "League": "WHL", "Tier": "Sleeper", "Sniper_Score": 6.5, "Sleeper_Score": 8.0, "Notes": "Pass-first genius with historic chemistry playing with his brother Liam."},
        {"Name": "Liam Ruck", "Year": 2026, "Round": 1, "Pick": 22, "NHL_Team": "Pittsburgh Penguins", "Pos": "F", "Projected_Pts": 68.0, "Projected_PPP": 21.0, "Goals_Last_Yr": 45, "Pts_Last_Yr": 104, "League": "WHL", "Tier": "Sniper", "Sniper_Score": 9.2, "Sleeper_Score": 4.0, "Notes": "Elite one-touch finisher who scored 45 goals last year. Dynamic duo candidate."},
        {"Name": "J.P. Hurlbert", "Year": 2026, "Round": 1, "Pick": 23, "NHL_Team": "Detroit Red Wings", "Pos": "F", "Projected_Pts": 70.0, "Projected_PPP": 22.5, "Goals_Last_Yr": 42, "Pts_Last_Yr": 97, "League": "WHL", "Tier": "Sniper", "Sniper_Score": 9.5, "Sleeper_Score": 3.0, "Notes": "High-volume shooter (294 SOG). Rocket of a wrist shot; lethal on 1PP."},
        {"Name": "Ryan Roobroeck", "Year": 2026, "Round": 2, "Pick": 35, "NHL_Team": "Chicago Blackhawks", "Pos": "F", "Projected_Pts": 66.5, "Projected_PPP": 19.0, "Goals_Last_Yr": 30, "Pts_Last_Yr": 58, "League": "OHL", "Tier": "Sniper", "Sniper_Score": 9.0, "Sleeper_Score": 5.0, "Notes": "6'4\" power winger with an NHL-caliber release. Elite net-front trigger option."},
        {"Name": "Beckett Hamilton", "Year": 2026, "Round": 3, "Pick": 74, "NHL_Team": "Colorado Avalanche", "Pos": "F", "Projected_Pts": 54.0, "Projected_PPP": 14.0, "Goals_Last_Yr": 24, "Pts_Last_Yr": 62, "League": "WHL", "Tier": "Sleeper", "Sniper_Score": 7.0, "Sleeper_Score": 8.5, "Notes": "Dragged Red Deer's offense singlehandedly. High-compete with massive ceiling."},
        {"Name": "Jonas Woo", "Year": 2026, "Round": 6, "Pick": 185, "NHL_Team": "Columbus Blue Jackets", "Pos": "D", "Projected_Pts": 51.0, "Projected_PPP": 16.5, "Goals_Last_Yr": 29, "Pts_Last_Yr": 86, "League": "WHL", "Tier": "Sleeper", "Sniper_Score": 8.0, "Sleeper_Score": 10.0, "Notes": "WHL defenseman scoring leader. Elite value target for deep leagues."},
        {"Name": "Adam Novotný", "Year": 2026, "Round": 1, "Pick": 24, "NHL_Team": "Vancouver Canucks", "Pos": "F", "Projected_Pts": 62.0, "Projected_PPP": 17.5, "Goals_Last_Yr": 34, "Pts_Last_Yr": 65, "League": "OHL", "Tier": "Sniper", "Sniper_Score": 8.8, "Sleeper_Score": 4.0, "Notes": "Blends heavy physical presence with a booming shot off the rush."},
        {"Name": "Maddox Dagenais", "Year": 2026, "Round": 1, "Pick": 16, "NHL_Team": "St. Louis Blues", "Pos": "F", "Projected_Pts": 59.5, "Projected_PPP": 16.0, "Goals_Last_Yr": 30, "Pts_Last_Yr": 62, "League": "QMJHL", "Tier": "Sniper", "Sniper_Score": 8.5, "Sleeper_Score": 3.0, "Notes": "Big 6'4\" frame with a lethal mid-range shot. High hockey IQ."},
        {"Name": "Caleb Malhotra", "Year": 2026, "Round": 1, "Pick": 3, "NHL_Team": "Vancouver Canucks", "Pos": "F", "Projected_Pts": 71.0, "Projected_PPP": 23.0, "Goals_Last_Yr": 29, "Pts_Last_Yr": 84, "League": "OHL", "Tier": "Elite", "Sniper_Score": 8.2, "Sleeper_Score": 2.0, "Notes": "OHL playoff goal-scoring leader. Extremely clutch net-front presence."},
        {"Name": "Niklas Aaram-Olsen", "Year": 2026, "Round": 2, "Pick": 41, "NHL_Team": "Vancouver Canucks", "Pos": "F", "Projected_Pts": 55.0, "Projected_PPP": 15.0, "Goals_Last_Yr": 20, "Pts_Last_Yr": 40, "League": "Sweden Jr", "Tier": "Sniper", "Sniper_Score": 8.6, "Sleeper_Score": 7.0, "Notes": "Elite-level snap shot and rapid release. Strong performance at World Juniors."},
        
        # 2025 Class
        {"Name": "James Hagens", "Year": 2025, "Round": 1, "Pick": 1, "NHL_Team": "San Jose Sharks", "Pos": "F", "Projected_Pts": 81.0, "Projected_PPP": 28.0, "Goals_Last_Yr": 18, "Pts_Last_Yr": 47, "League": "NCAA", "Tier": "Elite", "Sniper_Score": 7.5, "Sleeper_Score": 1.0, "Notes": "Dynamic center with world-class playmaking and elite power-play vision."},
        {"Name": "Porter Martone", "Year": 2025, "Round": 1, "Pick": 2, "NHL_Team": "Chicago Blackhawks", "Pos": "F", "Projected_Pts": 76.5, "Projected_PPP": 23.0, "Goals_Last_Yr": 33, "Pts_Last_Yr": 71, "League": "OHL", "Tier": "Elite", "Sniper_Score": 8.8, "Sleeper_Score": 1.0, "Notes": "Power forward who dominates net-front and eats up power play goals."},
        {"Name": "Michael Misa", "Year": 2025, "Round": 1, "Pick": 5, "NHL_Team": "Montreal Canadiens", "Pos": "F", "Projected_Pts": 72.0, "Projected_PPP": 21.0, "Goals_Last_Yr": 28, "Pts_Last_Yr": 75, "League": "OHL", "Tier": "Elite", "Sniper_Score": 8.2, "Sleeper_Score": 2.5, "Notes": "Exceptional status player with elite speed, processing, and finishing."},
        
        # 2024 Class
        {"Name": "Macklin Celebrini", "Year": 2024, "Round": 1, "Pick": 1, "NHL_Team": "San Jose Sharks", "Pos": "F", "Projected_Pts": 84.0, "Projected_PPP": 30.0, "Goals_Last_Yr": 32, "Pts_Last_Yr": 64, "League": "NHL", "Tier": "Elite", "Sniper_Score": 8.9, "Sleeper_Score": 1.0, "Notes": "Franchise 1C. Shoots with high-end volume and dominates all point situations."},
        {"Name": "Artyom Levshunov", "Year": 2024, "Round": 1, "Pick": 2, "NHL_Team": "Chicago Blackhawks", "Pos": "D", "Projected_Pts": 48.0, "Projected_PPP": 16.5, "Goals_Last_Yr": 9, "Pts_Last_Yr": 35, "League": "AHL", "Tier": "PP Quarterback", "Sniper_Score": 7.0, "Sleeper_Score": 2.0, "Notes": "Highly athletic defenseman. Projects to quarterback Chicago's 1PP unit."},
        {"Name": "Ivan Demidov", "Year": 2024, "Round": 1, "Pick": 5, "NHL_Team": "Montreal Canadiens", "Pos": "F", "Projected_Pts": 78.0, "Projected_PPP": 26.0, "Goals_Last_Yr": 23, "Pts_Last_Yr": 60, "League": "MHL", "Tier": "Elite", "Sniper_Score": 8.1, "Sleeper_Score": 1.2, "Notes": "Incredibly creative winger with elite perimeter play and PP control."},
        
        # 2023 Class
        {"Name": "Connor Bedard", "Year": 2023, "Round": 1, "Pick": 1, "NHL_Team": "Chicago Blackhawks", "Pos": "F", "Projected_Pts": 92.0, "Projected_PPP": 34.0, "Goals_Last_Yr": 22, "Pts_Last_Yr": 61, "League": "NHL", "Tier": "Elite", "Sniper_Score": 9.8, "Sleeper_Score": 1.0, "Notes": "Generational sniper. Top-tier power play release from the left circle."},
        {"Name": "Leo Carlsson", "Year": 2023, "Round": 1, "Pick": 2, "NHL_Team": "Anaheim Ducks", "Pos": "F", "Projected_Pts": 70.0, "Projected_PPP": 22.0, "Goals_Last_Yr": 12, "Pts_Last_Yr": 29, "League": "NHL", "Tier": "Elite", "Sniper_Score": 7.8, "Sleeper_Score": 1.5, "Notes": "Highly intelligent playmaker with excellent puck retention skills."},
        {"Name": "Adam Fantilli", "Year": 2023, "Round": 1, "Pick": 3, "NHL_Team": "Columbus Blue Jackets", "Pos": "F", "Projected_Pts": 71.5, "Projected_PPP": 21.0, "Goals_Last_Yr": 20, "Pts_Last_Yr": 40, "League": "NHL", "Tier": "Elite", "Sniper_Score": 8.4, "Sleeper_Score": 1.5, "Notes": "Power forward package with a elite wrister. Projects to dominate top PP line."}
    ])

# --- 3. LIVE NHL API FETCH FOR MULTIPLE YEARS ---
@st.cache_data(show_spinner=True)
def fetch_nhl_draft_data_for_years(years):
    combined_picks = []
    
    # Preseeded base map to check overlays - convert rows to dict to prevent nested Series mismatch
    df_preseeded = get_preseeded_prospects()
    preseeded_map = {row['Name']: row.to_dict() for _, row in df_preseeded.iterrows()}
    
    for year in years:
        try:
            url = f"https://api-web.nhle.com/v1/draft/picks/{year}/all"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for pick in data.get('picks', []):
                    # Parse names correctly.
                    # The NHL API returns firstName and lastName as nested dictionaries: {"default": "Firstname"}
                    first_raw = pick.get('firstName', '')
                    last_raw = pick.get('lastName', '')
                    
                    first_name = first_raw.get('default', '').strip() if isinstance(first_raw, dict) else str(first_raw).strip()
                    last_name = last_raw.get('default', '').strip() if isinstance(last_raw, dict) else str(last_raw).strip()
                    
                    full_name = f"{first_name} {last_name}".strip()
                    
                    nhl_team = pick.get('teamCommonName', {}).get('default', 'Unknown')
                    pos = pick.get('position', 'F')
                    round_num = pick.get('roundNumber', 1)
                    pick_num = pick.get('pickNumber', 1)
                    
                    # Check if player exists in preseeded mapping to overlay rich analytics
                    if full_name in preseeded_map:
                        p_data = preseeded_map[full_name].copy()
                        # Ensure actual API drafted information is accurate
                        p_data['NHL_Team'] = nhl_team
                        p_data['Round'] = round_num
                        p_data['Pick'] = pick_num
                        combined_picks.append(p_data)
                    else:
                        # Create standard roster entry from API
                        proj_pts = 45.0 if pos == 'F' else 28.0
                        proj_ppp = 12.0 if pos == 'F' else 8.0
                        combined_picks.append({
                            "Name": full_name,
                            "Year": year,
                            "Round": round_num,
                            "Pick": pick_num,
                            "NHL_Team": nhl_team,
                            "Pos": pos,
                            "Projected_Pts": proj_pts,
                            "Projected_PPP": proj_ppp,
                            "Goals_Last_Yr": 0,
                            "Pts_Last_Yr": 0,
                            "League": "Draft API",
                            "Tier": "Prospect",
                            "Sniper_Score": 5.0,
                            "Sleeper_Score": 3.0,
                            "Notes": "Live synced player from official NHL Draft API."
                        })
        except Exception as e:
            # If a specific year's API fails, we skip and use the other years' or offline fallback
            pass
            
    if combined_picks:
        return pd.DataFrame(combined_picks)
    else:
        # Complete fallback to preseeded list if offline completely
        return df_preseeded

# Title and Logo banner
st.markdown("<div class='main-header'>🏒 2026-27 Fantasy Hockey Draft Companion</div>", unsafe_allow_html=True)
st.write("Dynamic live tracker and analysis built directly upon official NHL Entry Draft APIs (2023 - 2026).")

# Sidebar Controls
st.sidebar.header("⚙️ Draft Settings & Filters")

# Draft Years selection
selected_years = st.sidebar.multiselect("Draft Classes to Sync", [2023, 2024, 2025, 2026], default=[2023, 2024, 2025, 2026])

# Trigger loading data from APIs
with st.spinner("Fetching live data from NHL APIs..."):
    df_base = fetch_nhl_draft_data_for_years(selected_years)

# Sidebar Filters
filter_pos = st.sidebar.multiselect("Positions", ["F", "D"], default=["F", "D"])
filter_tier = st.sidebar.multiselect("Prospect Types", ["Elite", "Sniper", "Sleeper", "PP Quarterback", "Prospect"], default=["Elite", "Sniper", "Sleeper", "PP Quarterback", "Prospect"])

# Search Bar
search_query = st.sidebar.text_input("🔍 Search Player Name")

# Reset Board Button
if st.sidebar.button("🗑️ Reset Drafted Players"):
    st.session_state.drafted_players = set()
    st.session_state.draft_log = []
    st.rerun()

# Apply Filters
df_filtered = df_base[df_base['Year'].isin(selected_years)]
df_filtered = df_filtered[df_filtered['Pos'].isin(filter_pos)]
df_filtered = df_filtered[df_filtered['Tier'].isin(filter_tier)]
if search_query:
    df_filtered = df_filtered[df_filtered['Name'].str.contains(search_query, case=False)]

# Create Tabs
tab_draft, tab_analytics, tab_teams, tab_api = st.tabs([
    "🎯 Live Draft Center", 
    "📈 Prospect Sniper & Sleeper Analytics", 
    "🛡️ NHL Team Portfolios",
    "🔌 API Connection Hub"
])

# ==================== TAB 1: LIVE DRAFT CENTER ====================
with tab_draft:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Available Prospects (Sorted by Projected Points)")
        
        # Split available vs drafted players
        available_players = df_filtered[~df_filtered['Name'].isin(st.session_state.drafted_players)].sort_values(by="Projected_Pts", ascending=False)
        
        if available_players.empty:
            st.info("No available players match your filter criteria.")
        else:
            # Render custom interactive data table with action buttons
            for index, row in available_players.iterrows():
                with st.container():
                    cols = st.columns([1, 4, 2, 2, 2, 2])
                    
                    # Draft Button
                    with cols[0]:
                        if st.button("Draft", key=f"draft_{row['Name']}_{row['Year']}"):
                            st.session_state.drafted_players.add(row['Name'])
                            st.session_state.draft_log.append({
                                "Name": row['Name'],
                                "NHL_Team": row['NHL_Team'],
                                "Projected_Pts": row['Projected_Pts'],
                                "Pos": row['Pos'],
                                "Year": row['Year']
                            })
                            st.rerun()
                    
                    # Player Info
                    with cols[1]:
                        st.markdown(f"**{row['Name']}** ({row['Pos']})")
                        st.caption(f"{row['Year']} Draft · Pick #{row['Pick']} by {row['NHL_Team']} · {row['League']}")
                    
                    # Projected Points
                    with cols[2]:
                        st.metric("Proj. Pts", f"{row['Projected_Pts']} pts")
                        
                    # Projected PPP
                    with cols[3]:
                        st.metric("Proj. PPP", f"{row['Projected_PPP']} pts")
                        
                    # Sniper / Sleeper Tiers
                    with cols[4]:
                        if row['Tier'] == "Sleeper":
                            st.markdown(f"⭐ **Sleeper** (Score: {row['Sleeper_Score']}/10)")
                        elif row['Tier'] == "Sniper":
                            st.markdown(f"🎯 **Sniper** (Score: {row['Sniper_Score']}/10)")
                        elif row['Tier'] == "PP Quarterback":
                            st.markdown(f"🏒 **PP QB**")
                        else:
                            st.markdown(f"💎 **{row['Tier']}**")
                            
                    # Scouting Notes
                    with cols[5]:
                        st.caption(row['Notes'])
                        
                    st.markdown("---")
                    
    with col_right:
        st.subheader("Live Draft Summary")
        
        # Display Metrics
        total_drafted = len(st.session_state.drafted_players)
        st.markdown(f"""
        <div class='metric-card'>
            <h4>Draft Tracker</h4>
            <p><b>Total Prospects Picked:</b> {total_drafted}</p>
            <p><b>Remaining Database Targets:</b> {len(df_base) - total_drafted}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Log of Drafted Players
        st.subheader("📋 Drafted Board Feed")
        if not st.session_state.draft_log:
            st.caption("No players drafted yet. Press 'Draft' on a player to live track.")
        else:
            for item in reversed(st.session_state.draft_log):
                st.markdown(f"❌ **{item['Name']}** ({item['Pos']}) — {item['Year']} Drafted by *{item['NHL_Team']}* (Proj: {item['Projected_Pts']} pts)")

# ==================== TAB 2: PROSPECT ANALYTICS ====================
with tab_analytics:
    st.subheader("Deep Goal-Scoring & Sleeper Analytics")
    
    col_chart_1, col_chart_2 = st.columns(2)
    
    with col_chart_1:
        st.write("🎯 **Pure Snipers: Goals last season vs. Projected Sniper Score**")
        snipers_only = df_base[df_base['Sniper_Score'] >= 7.0].sort_values(by="Goals_Last_Yr", ascending=False)
        fig_snipers = px.scatter(
            snipers_only, 
            x="Goals_Last_Yr", 
            y="Sniper_Score", 
            size="Projected_Pts", 
            color="Tier",
            hover_name="Name",
            text="Name",
            title="Elite Snipers (Sized by Projected NHL Points)",
            color_discrete_sequence=px.colors.qualitative.Dark2
        )
        fig_snipers.update_traces(textposition='top center')
        st.plotly_chart(fig_snipers, use_container_width=True)
        
    with col_chart_2:
        st.write("⭐ **Sleepers: Draft Pick vs. Sleeper Value Rating**")
        sleepers_only = df_base[df_base['Sleeper_Score'] >= 5.0].sort_values(by="Pick")
        fig_sleepers = px.scatter(
            sleepers_only, 
            x="Pick", 
            y="Sleeper_Score", 
            size="Projected_Pts", 
            color="NHL_Team",
            hover_name="Name",
            text="Name",
            title="Sleeper Value Curve (High Sleepers are Late Round Steals)",
            labels={"Pick": "Overall Draft Pick Number", "Sleeper_Score": "Sleeper Score (Out of 10)"}
        )
        fig_sleepers.update_traces(textposition='top center')
        st.plotly_chart(fig_sleepers, use_container_width=True)

    # Sleeper & Sniper Highlights Grid
    st.subheader("🔥 Top Scouting Spotlights")
    highlight_cols = st.columns(2)
    
    with highlight_cols[0]:
        st.markdown("""
        <div class='sleeper-card'>
            <h4>⭐ Jonas Woo (D, Columbus) - The Ultimate Sleeper</h4>
            <p><b>Draft Position:</b> Round 6, Pick #185 (2026)</p>
            <p><b>2025-26 Season:</b> 29 Goals, 57 Assists, 86 Points in 56 games for Medicine Hat (WHL).</p>
            <p><b>Fantasy Profile:</b> Woo shattered the franchise record for points by a defenseman. Despite his 6th-round real-world draft slot due to his 5'10" frame, his PNHLe is massive and he projects as a stellar late-round steal for power-play goals.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with highlight_cols[1]:
        st.markdown("""
        <div class='metric-card' style='border-left: 5px solid #10B981;'>
            <h4>🎯 Mathis Preston (F, Anaheim) - Best Pure Release</h4>
            <p><b>Draft Position:</b> Round 2, Pick #50 (2026)</p>
            <p><b>Scout Verdict:</b> Preston slipped in the draft due to injuries, but possesses the absolute best, most game-breaking wrist-shot release of the 2026 class. He is incredibly dangerous in open ice and represents major goal-scoring upside.</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== TAB 3: NHL TEAM PORTFOLIOS ====================
with tab_teams:
    st.subheader("NHL Team Stash Investigator")
    st.write("Inspect which franchises have selected the highest-octane fantasy prospects over the last four draft cycles.")
    
    selected_team = st.selectbox("Select NHL Team to Analyze", sorted(df_base['NHL_Team'].unique()))
    
    team_stash = df_base[df_base['NHL_Team'] == selected_team].sort_values(by="Projected_Pts", ascending=False)
    
    if team_stash.empty:
        st.info("No matching drafted prospects registered for this team.")
    else:
        st.write(f"### {selected_team}'s Fantasy Prospect Portfolio")
        st.dataframe(team_stash[["Name", "Year", "Round", "Pick", "Pos", "Projected_Pts", "Projected_PPP", "Goals_Last_Yr", "Notes"]])
        
        # Quick team metrics
        st.write("#### Team Metric Comparison")
        team_avg_pts = team_stash['Projected_Pts'].mean()
        st.metric("Average Project point potential of drafted stash:", f"{team_avg_pts:.1f} pts")

# ==================== TAB 4: API CONNECTION HUB ====================
with tab_api:
    st.subheader("Live NHL API Connection Guide")
    st.markdown("""
    This app is designed to connect directly with the official NHL Web API. Since you are running this locally on your machine, you can sync real-time draft data live.
    
    ### 🔌 API Endpoints Used:
    - 2023 Draft: `https://api-web.nhle.com/v1/draft/picks/2023/all`
    - 2024 Draft: `https://api-web.nhle.com/v1/draft/picks/2024/all`
    - 2025 Draft: `https://api-web.nhle.com/v1/draft/picks/2025/all`
    - 2026 Draft: `https://api-web.nhle.com/v1/draft/picks/2026/all`
    
    ### 💻 How to Use with your Globe Life laptop environment:
    1. Save this script to your workspace folder as `app.py`.
    2. Run Streamlit from your terminal:
       ```bash
       pip install streamlit pandas requests plotly openpyxl
       streamlit run app.py
       ```
    """)

# Footer message
st.markdown("---")
st.caption("🏒 2026-27 Draft Companion · Built for elite point-heavy fantasy leagues.")
