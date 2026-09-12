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
    return pd.DataFrame([   {   'Goals_Last_Yr': 15,
        'League': 'NCAA',
        'NHL_Drafted': True,
        'NHL_Team': 'Toronto Maple Leafs',
        'Name': 'Gavin McKenna',
        'Notes': 'Franchise winger. Projects for immediate 1PP role. Universal '
                 'consensus #1 pick.',
        'Pick': 1,
        'Pos': 'F',
        'Projected_PPP': 32.0,
        'Projected_Pts': 88.5,
        'Pts_Last_Yr': 51,
        'Round': 1,
        'Sleeper_Score': 1.0,
        'Sniper_Score': 8.5,
        'Tier': 'Elite',
        'Year': 2026},
    {   'Goals_Last_Yr': 25,
        'League': 'SHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Winnipeg Jets',
        'Name': 'Viggo Björck',
        'Notes': 'Tier 1 Franchise talent. Undersized but fearless. Highly '
                 'deceptive shot, excellent on power play.',
        'Pick': 8,
        'Pos': 'F',
        'Projected_PPP': 26.0,
        'Projected_Pts': 78.0,
        'Pts_Last_Yr': 65,
        'Round': 1,
        'Sleeper_Score': 1.5,
        'Sniper_Score': 8.0,
        'Tier': 'Elite',
        'Year': 2026},
    {   'Goals_Last_Yr': 11,
        'League': 'SHL',
        'NHL_Drafted': True,
        'NHL_Team': 'San Jose Sharks',
        'Name': 'Ivar Stenberg',
        'Notes': 'Outstanding Swedish playmaker; elite vision and power-play '
                 'utility.',
        'Pick': 2,
        'Pos': 'F',
        'Projected_PPP': 24.5,
        'Projected_Pts': 74.0,
        'Pts_Last_Yr': 33,
        'Round': 1,
        'Sleeper_Score': 1.0,
        'Sniper_Score': 8.0,
        'Tier': 'Elite',
        'Year': 2026},
    {   'Goals_Last_Yr': 29,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Vancouver Canucks',
        'Name': 'Caleb Malhotra',
        'Notes': 'OHL playoff goal-scoring leader. Extremely clutch net-front '
                 'presence.',
        'Pick': 3,
        'Pos': 'F',
        'Projected_PPP': 23.0,
        'Projected_Pts': 71.0,
        'Pts_Last_Yr': 84,
        'Round': 1,
        'Sleeper_Score': 2.0,
        'Sniper_Score': 8.2,
        'Tier': 'Elite',
        'Year': 2026},
    {   'Goals_Last_Yr': 42,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Detroit Red Wings',
        'Name': 'J.P. Hurlbert',
        'Notes': 'High-volume shooter (294 SOG). Rocket of a wrist shot; '
                 'lethal on 1PP. Michigan commit.',
        'Pick': 23,
        'Pos': 'F',
        'Projected_PPP': 22.5,
        'Projected_Pts': 70.0,
        'Pts_Last_Yr': 97,
        'Round': 1,
        'Sleeper_Score': 3.0,
        'Sniper_Score': 9.5,
        'Tier': 'Sniper',
        'Year': 2026},
    {   'Goals_Last_Yr': 45,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Pittsburgh Penguins',
        'Name': 'Liam Ruck',
        'Notes': 'Elite one-touch finisher who scored 45 goals last year. '
                 'Dynamic duo candidate with twin Markus.',
        'Pick': 22,
        'Pos': 'F',
        'Projected_PPP': 21.0,
        'Projected_Pts': 68.0,
        'Pts_Last_Yr': 104,
        'Round': 1,
        'Sleeper_Score': 4.0,
        'Sniper_Score': 9.2,
        'Tier': 'Sniper',
        'Year': 2026},
    {   'Goals_Last_Yr': 30,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Chicago Blackhawks',
        'Name': 'Ryan Roobroeck',
        'Notes': '6\'4" power winger with an NHL-caliber release. Elite '
                 'net-front trigger option.',
        'Pick': 35,
        'Pos': 'F',
        'Projected_PPP': 19.0,
        'Projected_Pts': 66.5,
        'Pts_Last_Yr': 58,
        'Round': 2,
        'Sleeper_Score': 5.0,
        'Sniper_Score': 9.0,
        'Tier': 'Sniper',
        'Year': 2026},
    {   'Goals_Last_Yr': 30,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Utah Mammoth',
        'Name': 'Ethan Belchetz',
        'Notes': 'Pure power forward. Tasmanian Devil on skates, physical '
                 'force with dominance behind the goal line.',
        'Pick': 17,
        'Pos': 'F',
        'Projected_PPP': 20.0,
        'Projected_Pts': 66.0,
        'Pts_Last_Yr': 60,
        'Round': 1,
        'Sleeper_Score': 2.5,
        'Sniper_Score': 8.2,
        'Tier': 'Elite',
        'Year': 2026},
    {   'Goals_Last_Yr': 37,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Anaheim Ducks',
        'Name': 'Nikita Klepov',
        'Notes': '1st Round #15 Anaheim pick. Pure playmaker & 37-goal sniper '
                 '(97 pts in 67 GP). Michigan State commit.',
        'Pick': 15,
        'Pos': 'F',
        'Projected_PPP': 19.0,
        'Projected_Pts': 65.5,
        'Pts_Last_Yr': 97,
        'Round': 1,
        'Sleeper_Score': 6.5,
        'Sniper_Score': 9.1,
        'Tier': 'Sniper',
        'Year': 2026},
    {   'Goals_Last_Yr': 28,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Calgary Flames',
        'Name': 'Egor Barabanov',
        'Notes': 'Calgary 4th-rounder in 2026. Exploded for 91 pts in OHL. '
                 'Elite playmaking vision and nasty competes.',
        'Pick': 100,
        'Pos': 'F',
        'Projected_PPP': 18.0,
        'Projected_Pts': 65.5,
        'Pts_Last_Yr': 91,
        'Round': 4,
        'Sleeper_Score': 8.5,
        'Sniper_Score': 7.2,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 12,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Seattle Kraken',
        'Name': 'Chase Reid',
        'Notes': 'Top defensive prospect in this draft. Drives possession and '
                 'pace of play. Great skater, solid 6-foot-2 frame.',
        'Pick': 7,
        'Pos': 'D',
        'Projected_PPP': 23.0,
        'Projected_Pts': 65.0,
        'Pts_Last_Yr': 48,
        'Round': 1,
        'Sleeper_Score': 1.5,
        'Sniper_Score': 7.0,
        'Tier': 'PP Quarterback',
        'Year': 2026},
    {   'Goals_Last_Yr': 21,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Pittsburgh Penguins',
        'Name': 'Markus Ruck',
        'Notes': 'Pass-first genius with historic chemistry playing with his '
                 "brother Liam. CHL's Top Scorer with 108 points.",
        'Pick': 39,
        'Pos': 'F',
        'Projected_PPP': 20.0,
        'Projected_Pts': 65.0,
        'Pts_Last_Yr': 108,
        'Round': 2,
        'Sleeper_Score': 8.0,
        'Sniper_Score': 6.5,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 22,
        'League': 'NCAA',
        'NHL_Drafted': True,
        'NHL_Team': 'St. Louis Blues',
        'Name': 'Tynan Lawrence',
        'Notes': 'Smart, solid two-way center who plays with power and energy. '
                 'Committed to BU.',
        'Pick': 11,
        'Pos': 'F',
        'Projected_PPP': 18.0,
        'Projected_Pts': 64.0,
        'Pts_Last_Yr': 58,
        'Round': 1,
        'Sleeper_Score': 2.0,
        'Sniper_Score': 7.0,
        'Tier': 'Elite',
        'Year': 2026},
    {   'Goals_Last_Yr': 24,
        'League': 'USNTDP',
        'NHL_Drafted': True,
        'NHL_Team': 'Nashville Predators',
        'Name': 'Wyatt Cullen',
        'Notes': 'High-end hockey sense, puck-handling, and skating. Constant '
                 'scoring threat.',
        'Pick': 10,
        'Pos': 'F',
        'Projected_PPP': 19.0,
        'Projected_Pts': 62.0,
        'Pts_Last_Yr': 55,
        'Round': 1,
        'Sleeper_Score': 2.0,
        'Sniper_Score': 7.5,
        'Tier': 'Elite',
        'Year': 2026},
    {   'Goals_Last_Yr': 34,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Vancouver Canucks',
        'Name': 'Adam Novotný',
        'Notes': 'Blends heavy physical presence with a booming shot off the '
                 'rush. 30-goal rookie season.',
        'Pick': 24,
        'Pos': 'F',
        'Projected_PPP': 17.5,
        'Projected_Pts': 62.0,
        'Pts_Last_Yr': 65,
        'Round': 1,
        'Sleeper_Score': 4.0,
        'Sniper_Score': 8.8,
        'Tier': 'Sniper',
        'Year': 2026},
    {   'Goals_Last_Yr': 20,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Calgary Flames',
        'Name': 'Carson Carels',
        'Notes': 'Highly mobile blueliner. Elite puck distributor built to run '
                 'a power play. Fourth in WHL defense scoring with 73 points.',
        'Pick': 6,
        'Pos': 'D',
        'Projected_PPP': 21.0,
        'Projected_Pts': 60.5,
        'Pts_Last_Yr': 73,
        'Round': 1,
        'Sleeper_Score': 2.0,
        'Sniper_Score': 7.5,
        'Tier': 'PP Quarterback',
        'Year': 2026},
    {   'Goals_Last_Yr': 30,
        'League': 'QMJHL',
        'NHL_Drafted': True,
        'NHL_Team': 'St. Louis Blues',
        'Name': 'Maddox Dagenais',
        'Notes': 'Big 6\'4" frame with a lethal mid-range shot. High hockey '
                 'IQ.',
        'Pick': 16,
        'Pos': 'F',
        'Projected_PPP': 16.0,
        'Projected_Pts': 59.5,
        'Pts_Last_Yr': 62,
        'Round': 1,
        'Sleeper_Score': 3.0,
        'Sniper_Score': 8.5,
        'Tier': 'Sniper',
        'Year': 2026},
    {   'Goals_Last_Yr': 28,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Buffalo Sabres',
        'Name': 'Daxon Rudolph',
        'Notes': 'Elite offensive defenseman. High-volume shooter and pure 1PP '
                 'QB.',
        'Pick': 4,
        'Pos': 'D',
        'Projected_PPP': 22.0,
        'Projected_Pts': 58.0,
        'Pts_Last_Yr': 78,
        'Round': 1,
        'Sleeper_Score': 2.0,
        'Sniper_Score': 8.0,
        'Tier': 'PP Quarterback',
        'Year': 2026},
    {   'Goals_Last_Yr': 15,
        'League': 'QMJHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Nashville Predators',
        'Name': 'Tommy Bleyl',
        'Notes': 'Highly skilled two-way defender who came out of nowhere to '
                 'score 81 points as a QMJHL rookie. Exceptionally crafty.',
        'Pick': 31,
        'Pos': 'D',
        'Projected_PPP': 21.0,
        'Projected_Pts': 58.0,
        'Pts_Last_Yr': 81,
        'Round': 1,
        'Sleeper_Score': 6.5,
        'Sniper_Score': 8.0,
        'Tier': 'PP Quarterback',
        'Year': 2026},
    {   'Goals_Last_Yr': 15,
        'League': 'NCAA',
        'NHL_Drafted': True,
        'NHL_Team': 'Nashville Predators',
        'Name': 'Aiden Fink',
        'Notes': 'Unowned 7th-round steal. Absolutely crushed NCAA scoring '
                 'with Penn State as a freshman. Small, highly elusive '
                 'playmaker.',
        'Pick': 218,
        'Pos': 'F',
        'Projected_PPP': 19.0,
        'Projected_Pts': 58.0,
        'Pts_Last_Yr': 34,
        'Round': 7,
        'Sleeper_Score': 9.0,
        'Sniper_Score': 7.2,
        'Tier': 'Sleeper',
        'Year': 2023},
    {   'Goals_Last_Yr': 20,
        'League': 'Sweden Jr',
        'NHL_Drafted': True,
        'NHL_Team': 'Vancouver Canucks',
        'Name': 'Niklas Aaram-Olsen',
        'Notes': 'Elite-level snap shot and rapid release. Strong performance '
                 'at World Juniors.',
        'Pick': 41,
        'Pos': 'F',
        'Projected_PPP': 15.0,
        'Projected_Pts': 55.0,
        'Pts_Last_Yr': 40,
        'Round': 2,
        'Sleeper_Score': 7.0,
        'Sniper_Score': 8.6,
        'Tier': 'Sniper',
        'Year': 2026},
    {   'Goals_Last_Yr': 18,
        'League': 'QMJHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Chicago Blackhawks',
        'Name': 'Xavier Villeneuve',
        'Notes': 'Elite power play quarterback with excellent vision from the '
                 'point. Helped Canada win gold at U-18s.',
        'Pick': 34,
        'Pos': 'D',
        'Projected_PPP': 22.0,
        'Projected_Pts': 55.0,
        'Pts_Last_Yr': 62,
        'Round': 2,
        'Sleeper_Score': 3.0,
        'Sniper_Score': 7.5,
        'Tier': 'PP Quarterback',
        'Year': 2026},
    {   'Goals_Last_Yr': 16,
        'League': 'NCAA',
        'NHL_Drafted': True,
        'NHL_Team': 'New York Islanders',
        'Name': 'Danny Nelson',
        'Notes': 'Unowned Islanders 2nd-rounder. Big, physical Notre Dame '
                 'scoring center.',
        'Pick': 49,
        'Pos': 'F',
        'Projected_PPP': 14.5,
        'Projected_Pts': 55.0,
        'Pts_Last_Yr': 32,
        'Round': 2,
        'Sleeper_Score': 7.8,
        'Sniper_Score': 7.0,
        'Tier': 'Sleeper',
        'Year': 2023},
    {   'Goals_Last_Yr': 24,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Colorado Avalanche',
        'Name': 'Beckett Hamilton',
        'Notes': "Dragged Red Deer's offense singlehandedly. High-compete with "
                 'massive ceiling. Colorado 3rd-rounder in 2026.',
        'Pick': 74,
        'Pos': 'F',
        'Projected_PPP': 14.0,
        'Projected_Pts': 54.0,
        'Pts_Last_Yr': 62,
        'Round': 3,
        'Sleeper_Score': 8.5,
        'Sniper_Score': 7.0,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 14,
        'League': 'Sweden Jr',
        'NHL_Drafted': True,
        'NHL_Team': 'Colorado Avalanche',
        'Name': 'Axel Elofsson',
        'Notes': 'Colorado 4th-rounder in 2026. Swedish puck-mover. Virtuoso '
                 'skater with dynamic perimeter play. Built for running 1PP '
                 'units.',
        'Pick': 128,
        'Pos': 'D',
        'Projected_PPP': 19.5,
        'Projected_Pts': 53.0,
        'Pts_Last_Yr': 42,
        'Round': 4,
        'Sleeper_Score': 8.5,
        'Sniper_Score': 7.0,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 12,
        'League': 'NCAA',
        'NHL_Drafted': True,
        'NHL_Team': 'Florida Panthers',
        'Name': 'Kamil Bednarik',
        'Notes': 'Unowned Florida 2nd-rounder. Smart USNTDP playmaking center '
                 'with high-end offensive hockey sense heading to BU.',
        'Pick': 61,
        'Pos': 'F',
        'Projected_PPP': 15.0,
        'Projected_Pts': 53.0,
        'Pts_Last_Yr': 30,
        'Round': 2,
        'Sleeper_Score': 8.0,
        'Sniper_Score': 6.5,
        'Tier': 'Sleeper',
        'Year': 2024},
    {   'Goals_Last_Yr': 8,
        'League': 'SHL',
        'NHL_Drafted': True,
        'NHL_Team': 'St. Louis Blues',
        'Name': 'Theo Lindstein',
        'Notes': 'Unowned Swedish playmaker. St. Louis 1st-rounder who '
                 'dominated the World Juniors with elite vision and PP QB '
                 'play.',
        'Pick': 29,
        'Pos': 'D',
        'Projected_PPP': 18.0,
        'Projected_Pts': 52.0,
        'Pts_Last_Yr': 31,
        'Round': 1,
        'Sleeper_Score': 9.0,
        'Sniper_Score': 6.0,
        'Tier': 'Sleeper',
        'Year': 2023},
    {   'Goals_Last_Yr': 22,
        'League': 'Finland Jr',
        'NHL_Drafted': True,
        'NHL_Team': 'Buffalo Sabres',
        'Name': 'Domán Kristóf Szongoth',
        'Notes': 'Buffalo 5th-rounder in 2026. Dynamic Hungarian-born '
                 'speedster. Dangerous shot release; joining Greyhounds in '
                 'OHL.',
        'Pick': 156,
        'Pos': 'F',
        'Projected_PPP': 15.0,
        'Projected_Pts': 52.0,
        'Pts_Last_Yr': 45,
        'Round': 5,
        'Sleeper_Score': 8.5,
        'Sniper_Score': 7.5,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 10,
        'League': 'NCAA',
        'NHL_Drafted': True,
        'NHL_Team': 'San Jose Sharks',
        'Name': 'Keaton Verhoeff',
        'Notes': 'Calm demeanor, takes up a ton of space at 6-foot-4. '
                 'Committed to UND, raw but sky-high ceiling.',
        'Pick': 9,
        'Pos': 'D',
        'Projected_PPP': 18.0,
        'Projected_Pts': 52.0,
        'Pts_Last_Yr': 35,
        'Round': 1,
        'Sleeper_Score': 2.0,
        'Sniper_Score': 6.5,
        'Tier': 'PP Quarterback',
        'Year': 2026},
    {   'Goals_Last_Yr': 4,
        'League': 'Liiga',
        'NHL_Drafted': True,
        'NHL_Team': 'Minnesota Wild',
        'Name': 'Aron Kiviharju',
        'Notes': 'Unowned top-tier steal! Formerly ranked top-5 overall before '
                 'a knee injury. Generational hockey IQ and elite playmaker.',
        'Pick': 122,
        'Pos': 'D',
        'Projected_PPP': 21.0,
        'Projected_Pts': 51.5,
        'Pts_Last_Yr': 12,
        'Round': 4,
        'Sleeper_Score': 9.5,
        'Sniper_Score': 5.0,
        'Tier': 'Sleeper',
        'Year': 2024},
    {   'Goals_Last_Yr': 24,
        'League': 'Finland Jr',
        'NHL_Drafted': True,
        'NHL_Team': 'Calgary Flames',
        'Name': 'Simon Katolicky',
        'Notes': 'Calgary 5th-rounder in 2026. 6\'6" Finnish giant power '
                 'forward. Unbelievable net-front utility and screen presence.',
        'Pick': 132,
        'Pos': 'F',
        'Projected_PPP': 13.0,
        'Projected_Pts': 51.0,
        'Pts_Last_Yr': 40,
        'Round': 5,
        'Sleeper_Score': 8.0,
        'Sniper_Score': 6.8,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 29,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Columbus Blue Jackets',
        'Name': 'Jonas Woo',
        'Notes': 'WHL defenseman scoring leader with 86 points in 56 games. '
                 'Columbus 6th-rounder in 2026. Elite value target for deep '
                 'leagues.',
        'Pick': 185,
        'Pos': 'D',
        'Projected_PPP': 16.5,
        'Projected_Pts': 51.0,
        'Pts_Last_Yr': 86,
        'Round': 6,
        'Sleeper_Score': 10.0,
        'Sniper_Score': 8.0,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 4,
        'League': 'Czechia',
        'NHL_Drafted': True,
        'NHL_Team': 'Pittsburgh Penguins',
        'Name': 'Tomáš Galvas',
        'Notes': 'Pittsburgh 2nd-rounder in 2026. Elite transition skater. '
                 'Calm, composed puck carrier who dominated WJC play.',
        'Pick': 54,
        'Pos': 'D',
        'Projected_PPP': 16.0,
        'Projected_Pts': 50.0,
        'Pts_Last_Yr': 22,
        'Round': 2,
        'Sleeper_Score': 9.0,
        'Sniper_Score': 4.5,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 5,
        'League': 'KHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Utah Hockey Club',
        'Name': 'Dmitriy Simashev',
        'Notes': "Unowned 6th overall pick from 2023. Massive 6'4 skating "
                 'wizard developing highly potent offensive transition game.',
        'Pick': 6,
        'Pos': 'D',
        'Projected_PPP': 15.0,
        'Projected_Pts': 49.0,
        'Pts_Last_Yr': 18,
        'Round': 1,
        'Sleeper_Score': 8.5,
        'Sniper_Score': 4.5,
        'Tier': 'Sleeper',
        'Year': 2023},
    {   'Goals_Last_Yr': 8,
        'League': 'DEL',
        'NHL_Drafted': True,
        'NHL_Team': 'New York Rangers',
        'Name': 'Alberts Šmits',
        'Notes': '6-foot-3 physical, engaged defender. Played against men in '
                 'Finland and Germany, and represented Latvia at Olympics.',
        'Pick': 5,
        'Pos': 'D',
        'Projected_PPP': 15.0,
        'Projected_Pts': 48.0,
        'Pts_Last_Yr': 28,
        'Round': 1,
        'Sleeper_Score': 2.0,
        'Sniper_Score': 6.0,
        'Tier': 'PP Quarterback',
        'Year': 2026},
    {   'Goals_Last_Yr': 11,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Montreal Canadiens',
        'Name': 'Timofei Runtso',
        'Notes': 'Montreal 2nd-rounder in 2026. Rugged, heavy-hitting WHL '
                 'blueliner who exploded offensively. Committing to Miami '
                 'University.',
        'Pick': 57,
        'Pos': 'D',
        'Projected_PPP': 14.5,
        'Projected_Pts': 48.0,
        'Pts_Last_Yr': 36,
        'Round': 2,
        'Sleeper_Score': 8.5,
        'Sniper_Score': 5.8,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 6,
        'League': 'Sweden Jr',
        'NHL_Drafted': True,
        'NHL_Team': 'San Jose Sharks',
        'Name': 'Leo Sahlin Wallenius',
        'Notes': 'Unowned Sharks 2nd-rounder. Sleek, beautiful skater with '
                 'high-end offensive transition potential.',
        'Pick': 53,
        'Pos': 'D',
        'Projected_PPP': 16.0,
        'Projected_Pts': 48.0,
        'Pts_Last_Yr': 28,
        'Round': 2,
        'Sleeper_Score': 8.0,
        'Sniper_Score': 5.5,
        'Tier': 'Sleeper',
        'Year': 2024},
    {   'Goals_Last_Yr': 10,
        'League': 'WHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Seattle Kraken',
        'Name': 'Caden Price',
        'Notes': 'Unowned Seattle 3rd-rounder. Smooth-skating, highly mobile '
                 'defenseman who has seen his point totals explode in the WHL.',
        'Pick': 84,
        'Pos': 'D',
        'Projected_PPP': 15.0,
        'Projected_Pts': 47.0,
        'Pts_Last_Yr': 55,
        'Round': 3,
        'Sleeper_Score': 8.0,
        'Sniper_Score': 6.0,
        'Tier': 'Sleeper',
        'Year': 2023},
    {   'Goals_Last_Yr': 27,
        'League': 'WHL',
        'NHL_Drafted': False,
        'NHL_Team': 'Arizona Coyotes',
        'Name': 'Lukas Sawchyn',
        'Notes': 'Unowned overager. Pure power-play maestro with elite '
                 'edgework and playmaking. ASU commit.',
        'Pick': 80,
        'Pos': 'F',
        'Projected_PPP': 20.0,
        'Projected_Pts': 64.0,
        'Pts_Last_Yr': 88,
        'Round': 3,
        'Sleeper_Score': 9.0,
        'Sniper_Score': 6.8,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 38,
        'League': 'QMJHL',
        'NHL_Drafted': False,
        'NHL_Team': 'Colorado Avalanche',
        'Name': 'Félix Lacerte',
        'Notes': 'Unowned overager. Slick playmaker with an elite shot release '
                 'and highlight-reel stickhandling. Vermont commit.',
        'Pick': 105,
        'Pos': 'F',
        'Projected_PPP': 21.0,
        'Projected_Pts': 63.0,
        'Pts_Last_Yr': 86,
        'Round': 4,
        'Sleeper_Score': 8.5,
        'Sniper_Score': 8.2,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 43,
        'League': 'QMJHL',
        'NHL_Drafted': False,
        'NHL_Team': 'Detroit Red Wings',
        'Name': 'Philippe Veilleux',
        'Notes': 'Unowned overager. Incredibly productive junior star with 43 '
                 'goals and high-octane offensive IQ.',
        'Pick': 195,
        'Pos': 'F',
        'Projected_PPP': 18.0,
        'Projected_Pts': 62.0,
        'Pts_Last_Yr': 96,
        'Round': 6,
        'Sleeper_Score': 8.8,
        'Sniper_Score': 8.0,
        'Tier': 'Sleeper',
        'Year': 2026},
    {   'Goals_Last_Yr': 18,
        'League': 'NCAA',
        'NHL_Drafted': True,
        'NHL_Team': 'Boston Bruins',
        'Name': 'James Hagens',
        'Notes': 'Dynamic center with world-class playmaking and elite '
                 'power-play vision.',
        'Pick': 7,
        'Pos': 'F',
        'Projected_PPP': 28.0,
        'Projected_Pts': 81.0,
        'Pts_Last_Yr': 47,
        'Round': 1,
        'Sleeper_Score': 1.0,
        'Sniper_Score': 7.5,
        'Tier': 'Elite',
        'Year': 2025},
    {   'Goals_Last_Yr': 33,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Philadelphia Flyers',
        'Name': 'Porter Martone',
        'Notes': 'Power forward who dominates net-front and eats up power play '
                 'goals.',
        'Pick': 6,
        'Pos': 'F',
        'Projected_PPP': 23.0,
        'Projected_Pts': 76.5,
        'Pts_Last_Yr': 71,
        'Round': 1,
        'Sleeper_Score': 1.0,
        'Sniper_Score': 8.8,
        'Tier': 'Elite',
        'Year': 2025},
    {   'Goals_Last_Yr': 28,
        'League': 'OHL',
        'NHL_Drafted': True,
        'NHL_Team': 'San Jose Sharks',
        'Name': 'Michael Misa',
        'Notes': 'Exceptional status player with elite speed, processing, and '
                 'finishing.',
        'Pick': 2,
        'Pos': 'F',
        'Projected_PPP': 21.0,
        'Projected_Pts': 72.0,
        'Pts_Last_Yr': 75,
        'Round': 1,
        'Sleeper_Score': 2.5,
        'Sniper_Score': 8.2,
        'Tier': 'Elite',
        'Year': 2025},
    {   'Goals_Last_Yr': 32,
        'League': 'NHL',
        'NHL_Drafted': True,
        'NHL_Team': 'San Jose Sharks',
        'Name': 'Macklin Celebrini',
        'Notes': 'Franchise 1C. Shoots with high-end volume and dominates all '
                 'point situations.',
        'Pick': 1,
        'Pos': 'F',
        'Projected_PPP': 30.0,
        'Projected_Pts': 84.0,
        'Pts_Last_Yr': 64,
        'Round': 1,
        'Sleeper_Score': 1.0,
        'Sniper_Score': 8.9,
        'Tier': 'Elite',
        'Year': 2024},
    {   'Goals_Last_Yr': 9,
        'League': 'AHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Chicago Blackhawks',
        'Name': 'Artyom Levshunov',
        'Notes': 'Highly athletic defenseman. Projects to quarterback '
                 "Chicago's 1PP unit.",
        'Pick': 2,
        'Pos': 'D',
        'Projected_PPP': 16.5,
        'Projected_Pts': 48.0,
        'Pts_Last_Yr': 35,
        'Round': 1,
        'Sleeper_Score': 2.0,
        'Sniper_Score': 7.0,
        'Tier': 'PP Quarterback',
        'Year': 2024},
    {   'Goals_Last_Yr': 23,
        'League': 'MHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Montreal Canadiens',
        'Name': 'Ivan Demidov',
        'Notes': 'Incredibly creative winger with elite perimeter play and PP '
                 'control.',
        'Pick': 5,
        'Pos': 'F',
        'Projected_PPP': 26.0,
        'Projected_Pts': 78.0,
        'Pts_Last_Yr': 60,
        'Round': 1,
        'Sleeper_Score': 1.2,
        'Sniper_Score': 8.1,
        'Tier': 'Elite',
        'Year': 2024},
    {   'Goals_Last_Yr': 22,
        'League': 'NHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Chicago Blackhawks',
        'Name': 'Connor Bedard',
        'Notes': 'Generational sniper. Top-tier power play release from the '
                 'left circle.',
        'Pick': 1,
        'Pos': 'F',
        'Projected_PPP': 34.0,
        'Projected_Pts': 92.0,
        'Pts_Last_Yr': 61,
        'Round': 1,
        'Sleeper_Score': 1.0,
        'Sniper_Score': 9.8,
        'Tier': 'Elite',
        'Year': 2023},
    {   'Goals_Last_Yr': 12,
        'League': 'NHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Anaheim Ducks',
        'Name': 'Leo Carlsson',
        'Notes': 'Highly intelligent playmaker with excellent puck retention '
                 'skills.',
        'Pick': 2,
        'Pos': 'F',
        'Projected_PPP': 22.0,
        'Projected_Pts': 70.0,
        'Pts_Last_Yr': 29,
        'Round': 1,
        'Sleeper_Score': 1.5,
        'Sniper_Score': 7.8,
        'Tier': 'Elite',
        'Year': 2023},
    {   'Goals_Last_Yr': 20,
        'League': 'NHL',
        'NHL_Drafted': True,
        'NHL_Team': 'Columbus Blue Jackets',
        'Name': 'Adam Fantilli',
        'Notes': 'Power forward package with a elite wrister. Projects to '
                 'dominate top PP line.',
        'Pick': 3,
        'Pos': 'F',
        'Projected_PPP': 21.0,
        'Projected_Pts': 71.5,
        'Pts_Last_Yr': 40,
        'Round': 1,
        'Sleeper_Score': 1.5,
        'Sniper_Score': 8.4,
        'Tier': 'Elite',
        'Year': 2023}])


# --- 3. LIVE NHL API FETCH FOR MULTIPLE YEARS ---
@st.cache_data(show_spinner=True)
def fetch_nhl_draft_data_for_years(years):
    combined_picks = []
    
    # Preseeded base map to check overlays
    df_preseeded = get_preseeded_prospects()
    preseeded_map = {row['Name']: row for _, row in df_preseeded.iterrows()}
    
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


# Sidebar Sorting
st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Draft Board Sorting")
sort_option = st.sidebar.selectbox(
    "Sort Board By:",
    [
        "Pure Offensive Points (Proj. Pts)",
        "Powerplay Utility (Proj. PPP)",
        "Sniper Score / Goals",
        "Sleeper / Value Steal Rating",
        "Real NHL Draft Pick #"
    ],
    index=0
)

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
        st.subheader(f"Available Prospects — {sort_option}")
        
        # Split available vs drafted players
        available_players = df_filtered[~df_filtered['Name'].isin(st.session_state.drafted_players)].copy()

        if sort_option == "Pure Offensive Points (Proj. Pts)":
            available_players = available_players.sort_values(by=["Projected_Pts", "Projected_PPP"], ascending=[False, False])
        elif sort_option == "Powerplay Utility (Proj. PPP)":
            available_players = available_players.sort_values(by=["Projected_PPP", "Projected_Pts"], ascending=[False, False])
        elif sort_option == "Sniper Score / Goals":
            available_players = available_players.sort_values(by=["Sniper_Score", "Goals_Last_Yr"], ascending=[False, False])
        elif sort_option == "Sleeper / Value Steal Rating":
            available_players = available_players.sort_values(by=["Sleeper_Score", "Projected_Pts"], ascending=[False, False])
        elif sort_option == "Real NHL Draft Pick #":
            available_players = available_players.sort_values(by=["Year", "Round", "Pick"], ascending=[False, True, True])
        else:
            available_players = available_players.sort_values(by="Projected_Pts", ascending=False)
        
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
