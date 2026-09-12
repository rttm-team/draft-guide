import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import unicodedata
import os
import re
import difflib

# Set Page Config for a professional look
st.set_page_config(
    page_title="2026-27 Fantasy Hockey Draft Companion",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to normalize player names to match accents/umlauts flawlessly
def normalize_name(name):
    normalized = "".join(
        c for c in unicodedata.normalize('NFD', str(name))
        if unicodedata.category(c) != 'Mn'
    ).lower().replace('-', ' ').replace('.', '').strip()
    
    overrides = {
        "bradly nadeau": "bradley nadeau",
        "dmitri simashev": "dmitriy simashev",
    }
    return overrides.get(normalized, normalized)


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
if 'favorite_players' not in st.session_state:
    st.session_state.favorite_players = set()

# --- 2. PRE-SEEDED FANTASY DATABASE ---
# Curated list of elite prospects, snipers, sleepers, and post-draft performers across 2023-2026 classes
@st.cache_data
def get_preseeded_prospects():
    data = [
        # 2026 Class
        {
            'Name': 'Gavin McKenna', 'Year': 2026, 'Round': 1, 'Pick': 1, 'NHL_Team': '2026 Draft Eligible',
            'Pos': 'F', 'Projected_Pts': 88.5, 'Projected_PPP': 32.0, 'GP': 35, 'Goals_Last_Yr': 15, 'Assists_Last_Yr': 36, 'Pts_Last_Yr': 51,
            'League': 'NCAA', 'Tier': 'Elite', 'Sniper_Score': 8.5, 'Sleeper_Score': 1.0, 'NHL_Drafted': True,
            'Notes': 'Franchise winger. Projects for immediate 1PP role. Universal consensus #1 pick.'
        },
        {
            'Name': 'Viggo Björck', 'Year': 2026, 'Round': 1, 'Pick': 8, 'NHL_Team': '2026 Draft Eligible',
            'Pos': 'F', 'Projected_Pts': 78.0, 'Projected_PPP': 26.0, 'GP': 42, 'Goals_Last_Yr': 25, 'Assists_Last_Yr': 40, 'Pts_Last_Yr': 65,
            'League': 'SHL', 'Tier': 'Elite', 'Sniper_Score': 8.0, 'Sleeper_Score': 1.5, 'NHL_Drafted': True,
            'Notes': 'Tier 1 Franchise talent. Undersized but fearless. Highly deceptive shot, excellent on power play.'
        },
        {
            'Name': 'Ivar Stenberg', 'Year': 2026, 'Round': 1, 'Pick': 2, 'NHL_Team': '2026 Draft Eligible',
            'Pos': 'F', 'Projected_Pts': 74.0, 'Projected_PPP': 24.5, 'GP': 38, 'Goals_Last_Yr': 11, 'Assists_Last_Yr': 22, 'Pts_Last_Yr': 33,
            'League': 'SHL', 'Tier': 'Elite', 'Sniper_Score': 8.0, 'Sleeper_Score': 1.0, 'NHL_Drafted': True,
            'Notes': 'Outstanding Swedish playmaker; elite vision and power-play utility.'
        },
        {
            'Name': 'Caleb Malhotra', 'Year': 2026, 'Round': 1, 'Pick': 3, 'NHL_Team': 'Vancouver Canucks',
            'Pos': 'F', 'Projected_Pts': 71.0, 'Projected_PPP': 23.0, 'GP': 68, 'Goals_Last_Yr': 29, 'Assists_Last_Yr': 55, 'Pts_Last_Yr': 84,
            'League': 'OHL', 'Tier': 'Elite', 'Sniper_Score': 8.2, 'Sleeper_Score': 2.0, 'NHL_Drafted': True,
            'Notes': 'OHL playoff goal-scoring leader. Extremely clutch net-front presence.'
        },
        {
            'Name': 'J.P. Hurlbert', 'Year': 2026, 'Round': 1, 'Pick': 23, 'NHL_Team': 'Detroit Red Wings',
            'Pos': 'F', 'Projected_Pts': 70.0, 'Projected_PPP': 22.5, 'GP': 68, 'Goals_Last_Yr': 42, 'Assists_Last_Yr': 55, 'Pts_Last_Yr': 97,
            'League': 'WHL', 'Tier': 'Sniper', 'Sniper_Score': 9.5, 'Sleeper_Score': 3.0, 'NHL_Drafted': True,
            'Notes': 'High-volume shooter (294 SOG). Rocket of a wrist shot; lethal on 1PP. Michigan commit.'
        },
        {
            'Name': 'Liam Ruck', 'Year': 2026, 'Round': 1, 'Pick': 22, 'NHL_Team': 'Pittsburgh Penguins',
            'Pos': 'F', 'Projected_Pts': 68.0, 'Projected_PPP': 21.0, 'GP': 68, 'Goals_Last_Yr': 45, 'Assists_Last_Yr': 59, 'Pts_Last_Yr': 104,
            'League': 'WHL', 'Tier': 'Sniper', 'Sniper_Score': 9.2, 'Sleeper_Score': 4.0, 'NHL_Drafted': True,
            'Notes': 'Elite one-touch finisher who scored 45 goals last year. Dynamic duo candidate with twin Markus.'
        },
        {
            'Name': 'Ryan Roobroeck', 'Year': 2026, 'Round': 2, 'Pick': 35, 'NHL_Team': 'Chicago Blackhawks',
            'Pos': 'F', 'Projected_Pts': 66.5, 'Projected_PPP': 19.0, 'GP': 62, 'Goals_Last_Yr': 30, 'Assists_Last_Yr': 28, 'Pts_Last_Yr': 58,
            'League': 'OHL', 'Tier': 'Sniper', 'Sniper_Score': 9.0, 'Sleeper_Score': 5.0, 'NHL_Drafted': True,
            'Notes': '6-foot-4 power winger with an NHL-caliber release. Elite net-front trigger option.'
        },
        {
            'Name': 'Ethan Belchetz', 'Year': 2026, 'Round': 1, 'Pick': 17, 'NHL_Team': 'Utah Mammoth',
            'Pos': 'F', 'Projected_Pts': 66.0, 'Projected_PPP': 20.0, 'GP': 60, 'Goals_Last_Yr': 30, 'Assists_Last_Yr': 30, 'Pts_Last_Yr': 60,
            'League': 'OHL', 'Tier': 'Elite', 'Sniper_Score': 8.2, 'Sleeper_Score': 2.5, 'NHL_Drafted': True,
            'Notes': 'Pure power forward. Tasmanian Devil on skates, physical force with dominance behind the goal line.'
        },
        {
            'Name': 'Nikita Klepov', 'Year': 2026, 'Round': 1, 'Pick': 15, 'NHL_Team': 'Anaheim Ducks',
            'Pos': 'F', 'Projected_Pts': 65.5, 'Projected_PPP': 19.0, 'GP': 67, 'Goals_Last_Yr': 37, 'Assists_Last_Yr': 60, 'Pts_Last_Yr': 97,
            'League': 'OHL', 'Tier': 'Sniper', 'Sniper_Score': 9.1, 'Sleeper_Score': 6.5, 'NHL_Drafted': True,
            'Notes': '1st Round #15 Anaheim pick. Pure playmaker & 37-goal sniper (97 pts in 67 GP). Michigan State commit.'
        },
        {
            'Name': 'Egor Barabanov', 'Year': 2026, 'Round': 4, 'Pick': 100, 'NHL_Team': 'Calgary Flames',
            'Pos': 'F', 'Projected_Pts': 65.5, 'Projected_PPP': 18.0, 'GP': 68, 'Goals_Last_Yr': 28, 'Assists_Last_Yr': 63, 'Pts_Last_Yr': 91,
            'League': 'OHL', 'Tier': 'Sleeper', 'Sniper_Score': 7.2, 'Sleeper_Score': 8.5, 'NHL_Drafted': True,
            'Notes': 'Calgary 4th-rounder in 2026. Exploded for 91 pts in OHL. Elite playmaking vision and nasty competes.'
        },
        {
            'Name': 'Chase Reid', 'Year': 2026, 'Round': 1, 'Pick': 7, 'NHL_Team': 'Seattle Kraken',
            'Pos': 'D', 'Projected_Pts': 65.0, 'Projected_PPP': 23.0, 'GP': 64, 'Goals_Last_Yr': 12, 'Assists_Last_Yr': 36, 'Pts_Last_Yr': 48,
            'League': 'OHL', 'Tier': 'PP Quarterback', 'Sniper_Score': 7.0, 'Sleeper_Score': 1.5, 'NHL_Drafted': True,
            'Notes': 'Top defensive prospect in this draft. Drives possession and pace of play. Great skater, solid 6-foot-2 frame.'
        },
        {
            'Name': 'Markus Ruck', 'Year': 2026, 'Round': 2, 'Pick': 39, 'NHL_Team': 'Pittsburgh Penguins',
            'Pos': 'F', 'Projected_Pts': 65.0, 'Projected_PPP': 20.0, 'GP': 68, 'Goals_Last_Yr': 21, 'Assists_Last_Yr': 87, 'Pts_Last_Yr': 108,
            'League': 'WHL', 'Tier': 'Sleeper', 'Sniper_Score': 6.5, 'Sleeper_Score': 8.0, 'NHL_Drafted': True,
            'Notes': 'Pass-first genius with historic chemistry playing with his brother Liam. CHL\'s Top Scorer with 108 points.'
        },
        {
            'Name': 'Tynan Lawrence', 'Year': 2026, 'Round': 1, 'Pick': 11, 'NHL_Team': 'St. Louis Blues',
            'Pos': 'F', 'Projected_Pts': 64.0, 'Projected_PPP': 18.0, 'GP': 54, 'Goals_Last_Yr': 22, 'Assists_Last_Yr': 36, 'Pts_Last_Yr': 58,
            'League': 'NCAA', 'Tier': 'Elite', 'Sniper_Score': 7.0, 'Sleeper_Score': 2.0, 'NHL_Drafted': True,
            'Notes': 'Smart, solid two-way center who plays with power and energy. Committed to BU.'
        },
        {
            'Name': 'Wyatt Cullen', 'Year': 2026, 'Round': 1, 'Pick': 10, 'NHL_Team': 'Nashville Predators',
            'Pos': 'F', 'Projected_Pts': 62.0, 'Projected_PPP': 19.0, 'GP': 52, 'Goals_Last_Yr': 24, 'Assists_Last_Yr': 31, 'Pts_Last_Yr': 55,
            'League': 'USNTDP', 'Tier': 'Elite', 'Sniper_Score': 7.5, 'Sleeper_Score': 2.0, 'NHL_Drafted': True,
            'Notes': 'High-end hockey sense, puck-handling, and skating. Constant scoring threat.'
        },
        {
            'Name': 'Adam Novotný', 'Year': 2026, 'Round': 1, 'Pick': 24, 'NHL_Team': 'Vancouver Canucks',
            'Pos': 'F', 'Projected_Pts': 62.0, 'Projected_PPP': 17.5, 'GP': 62, 'Goals_Last_Yr': 34, 'Assists_Last_Yr': 31, 'Pts_Last_Yr': 65,
            'League': 'OHL', 'Tier': 'Sniper', 'Sniper_Score': 8.8, 'Sleeper_Score': 4.0, 'NHL_Drafted': True,
            'Notes': 'Blends heavy physical presence with a booming shot off the rush. 30-goal rookie season.'
        },
        {
            'Name': 'Carson Carels', 'Year': 2026, 'Round': 1, 'Pick': 6, 'NHL_Team': 'Calgary Flames',
            'Pos': 'D', 'Projected_Pts': 60.5, 'Projected_PPP': 21.0, 'GP': 66, 'Goals_Last_Yr': 20, 'Assists_Last_Yr': 53, 'Pts_Last_Yr': 73,
            'League': 'WHL', 'Tier': 'PP Quarterback', 'Sniper_Score': 7.5, 'Sleeper_Score': 2.0, 'NHL_Drafted': True,
            'Notes': 'Highly mobile blueliner. Elite puck distributor built to run a power play. Fourth in WHL defense scoring with 73 points.'
        },
        {
            'Name': 'Maddox Dagenais', 'Year': 2026, 'Round': 1, 'Pick': 16, 'NHL_Team': 'St. Louis Blues',
            'Pos': 'F', 'Projected_Pts': 59.5, 'Projected_PPP': 16.0, 'GP': 60, 'Goals_Last_Yr': 30, 'Assists_Last_Yr': 32, 'Pts_Last_Yr': 62,
            'League': 'QMJHL', 'Tier': 'Sniper', 'Sniper_Score': 8.5, 'Sleeper_Score': 3.0, 'NHL_Drafted': True,
            'Notes': 'Big 6-foot-4 frame with a lethal mid-range shot. High hockey IQ.'
        },
        {
            'Name': 'Daxon Rudolph', 'Year': 2026, 'Round': 1, 'Pick': 4, 'NHL_Team': 'Buffalo Sabres',
            'Pos': 'D', 'Projected_Pts': 58.0, 'Projected_PPP': 22.0, 'GP': 65, 'Goals_Last_Yr': 28, 'Assists_Last_Yr': 50, 'Pts_Last_Yr': 78,
            'League': 'WHL', 'Tier': 'PP Quarterback', 'Sniper_Score': 8.0, 'Sleeper_Score': 2.0, 'NHL_Drafted': True,
            'Notes': 'Elite offensive defenseman. High-volume shooter and pure 1PP QB.'
        },
        {
            'Name': 'Tommy Bleyl', 'Year': 2026, 'Round': 1, 'Pick': 31, 'NHL_Team': 'Nashville Predators',
            'Pos': 'D', 'Projected_Pts': 58.0, 'Projected_PPP': 21.0, 'GP': 64, 'Goals_Last_Yr': 15, 'Assists_Last_Yr': 66, 'Pts_Last_Yr': 81,
            'League': 'QMJHL', 'Tier': 'PP Quarterback', 'Sniper_Score': 8.0, 'Sleeper_Score': 6.5, 'NHL_Drafted': True,
            'Notes': 'Highly skilled two-way defender who came out of nowhere to score 81 points as a QMJHL rookie. Exceptionally crafty.'
        },
        {
            'Name': 'Aiden Fink', 'Year': 2023, 'Round': 7, 'Pick': 218, 'NHL_Team': 'Nashville Predators',
            'Pos': 'F', 'Projected_Pts': 58.0, 'Projected_PPP': 19.0, 'GP': 34, 'Goals_Last_Yr': 15, 'Assists_Last_Yr': 19, 'Pts_Last_Yr': 34,
            'League': 'NCAA', 'Tier': 'Sleeper', 'Sniper_Score': 7.2, 'Sleeper_Score': 9.0, 'NHL_Drafted': True,
            'Notes': 'Unowned 7th-round steal. Absolutely crushed NCAA scoring with Penn State as a freshman. Small, highly elusive playmaker.'
        },
        {
            'Name': 'Niklas Aaram-Olsen', 'Year': 2026, 'Round': 2, 'Pick': 41, 'NHL_Team': 'Vancouver Canucks',
            'Pos': 'F', 'Projected_Pts': 55.0, 'Projected_PPP': 15.0, 'GP': 45, 'Goals_Last_Yr': 20, 'Assists_Last_Yr': 20, 'Pts_Last_Yr': 40,
            'League': 'Sweden Jr', 'Tier': 'Sniper', 'Sniper_Score': 8.6, 'Sleeper_Score': 7.0, 'NHL_Drafted': True,
            'Notes': 'Elite-level snap shot and rapid release. Strong performance at World Juniors.'
        },
        {
            'Name': 'Xavier Villeneuve', 'Year': 2026, 'Round': 2, 'Pick': 34, 'NHL_Team': 'Chicago Blackhawks',
            'Pos': 'D', 'Projected_Pts': 55.0, 'Projected_PPP': 22.0, 'GP': 62, 'Goals_Last_Yr': 18, 'Assists_Last_Yr': 44, 'Pts_Last_Yr': 62,
            'League': 'QMJHL', 'Tier': 'PP Quarterback', 'Sniper_Score': 7.5, 'Sleeper_Score': 3.0, 'NHL_Drafted': True,
            'Notes': 'Elite power play quarterback with excellent vision from the point. Helped Canada win gold at U-18s.'
        },
        {
            'Name': 'Danny Nelson', 'Year': 2023, 'Round': 2, 'Pick': 49, 'NHL_Team': 'New York Islanders',
            'Pos': 'F', 'Projected_Pts': 55.0, 'Projected_PPP': 14.5, 'GP': 37, 'Goals_Last_Yr': 16, 'Assists_Last_Yr': 16, 'Pts_Last_Yr': 32,
            'League': 'NCAA', 'Tier': 'Sleeper', 'Sniper_Score': 7.0, 'Sleeper_Score': 7.8, 'NHL_Drafted': True,
            'Notes': 'Unowned Islanders 2nd-rounder. Big, physical Notre Dame scoring center.'
        },
        {
            'Name': 'Beckett Hamilton', 'Year': 2026, 'Round': 3, 'Pick': 74, 'NHL_Team': 'Colorado Avalanche',
            'Pos': 'F', 'Projected_Pts': 54.0, 'Projected_PPP': 14.0, 'GP': 67, 'Goals_Last_Yr': 24, 'Assists_Last_Yr': 38, 'Pts_Last_Yr': 62,
            'League': 'WHL', 'Tier': 'Sleeper', 'Sniper_Score': 7.0, 'Sleeper_Score': 8.5, 'NHL_Drafted': True,
            'Notes': 'Dragged Red Deer\'s offense singlehandedly. High-compete with massive ceiling. Colorado 3rd-rounder in 2026.'
        },
        {
            'Name': 'Axel Elofsson', 'Year': 2026, 'Round': 4, 'Pick': 128, 'NHL_Team': 'Colorado Avalanche',
            'Pos': 'D', 'Projected_Pts': 53.0, 'Projected_PPP': 19.5, 'GP': 48, 'Goals_Last_Yr': 14, 'Assists_Last_Yr': 28, 'Pts_Last_Yr': 42,
            'League': 'Sweden Jr', 'Tier': 'Sleeper', 'Sniper_Score': 7.0, 'Sleeper_Score': 8.5, 'NHL_Drafted': True,
            'Notes': 'Colorado 4th-rounder in 2026. Swedish puck-mover. Virtuoso skater with dynamic perimeter play. Built for running 1PP units.'
        },
        {
            'Name': 'Kamil Bednarik', 'Year': 2024, 'Round': 2, 'Pick': 61, 'NHL_Team': 'Florida Panthers',
            'Pos': 'F', 'Projected_Pts': 53.0, 'Projected_PPP': 15.0, 'GP': 36, 'Goals_Last_Yr': 12, 'Assists_Last_Yr': 18, 'Pts_Last_Yr': 30,
            'League': 'NCAA', 'Tier': 'Sleeper', 'Sniper_Score': 6.5, 'Sleeper_Score': 8.0, 'NHL_Drafted': True,
            'Notes': 'Unowned Florida 2nd-rounder. Smart USNTDP playmaking center with high-end offensive hockey sense heading to BU.'
        },
        {
            'Name': 'Theo Lindstein', 'Year': 2023, 'Round': 1, 'Pick': 29, 'NHL_Team': 'St. Louis Blues',
            'Pos': 'D', 'Projected_Pts': 52.0, 'Projected_PPP': 18.0, 'GP': 49, 'Goals_Last_Yr': 8, 'Assists_Last_Yr': 23, 'Pts_Last_Yr': 31,
            'League': 'SHL', 'Tier': 'Sleeper', 'Sniper_Score': 6.0, 'Sleeper_Score': 9.0, 'NHL_Drafted': True,
            'Notes': 'Unowned Swedish playmaker. St. Louis 1st-rounder who dominated the World Juniors with elite vision and PP QB play.'
        },
        {
            'Name': 'Domán Kristóf Szongoth', 'Year': 2026, 'Round': 5, 'Pick': 156, 'NHL_Team': 'Buffalo Sabres',
            'Pos': 'F', 'Projected_Pts': 52.0, 'Projected_PPP': 15.0, 'GP': 44, 'Goals_Last_Yr': 22, 'Assists_Last_Yr': 23, 'Pts_Last_Yr': 45,
            'League': 'Finland Jr', 'Tier': 'Sleeper', 'Sniper_Score': 7.5, 'Sleeper_Score': 8.5, 'NHL_Drafted': True,
            'Notes': 'Buffalo 5th-rounder in 2026. Dynamic Hungarian-born speedster. Dangerous shot release; joining Greyhounds in OHL.'
        },
        {
            'Name': 'Keaton Verhoeff', 'Year': 2026, 'Round': 1, 'Pick': 9, 'NHL_Team': '2026 Draft Eligible',
            'Pos': 'D', 'Projected_Pts': 52.0, 'Projected_PPP': 18.0, 'GP': 42, 'Goals_Last_Yr': 10, 'Assists_Last_Yr': 25, 'Pts_Last_Yr': 35,
            'League': 'NCAA', 'Tier': 'PP Quarterback', 'Sniper_Score': 6.5, 'Sleeper_Score': 2.0, 'NHL_Drafted': True,
            'Notes': 'Calm demeanor, takes up a ton of space at 6-foot-4. Committed to UND, raw but sky-high ceiling.'
        },
        {
            'Name': 'Aron Kiviharju', 'Year': 2024, 'Round': 4, 'Pick': 122, 'NHL_Team': 'Minnesota Wild',
            'Pos': 'D', 'Projected_Pts': 51.5, 'Projected_PPP': 21.0, 'GP': 48, 'Goals_Last_Yr': 6, 'Assists_Last_Yr': 38, 'Pts_Last_Yr': 44,
            'League': 'Liiga', 'Tier': 'Sleeper', 'Sniper_Score': 5.0, 'Sleeper_Score': 9.5, 'NHL_Drafted': True,
            'Notes': 'Unowned top-tier steal! Formerly ranked top-5 overall before a knee injury. Post-recovery 0.92 PPG breakout in Liiga/AHL.'
        },
        {
            'Name': 'Simon Katolicky', 'Year': 2026, 'Round': 5, 'Pick': 132, 'NHL_Team': 'Calgary Flames',
            'Pos': 'F', 'Projected_Pts': 51.0, 'Projected_PPP': 13.0, 'GP': 48, 'Goals_Last_Yr': 24, 'Assists_Last_Yr': 16, 'Pts_Last_Yr': 40,
            'League': 'Finland Jr', 'Tier': 'Sleeper', 'Sniper_Score': 6.8, 'Sleeper_Score': 8.0, 'NHL_Drafted': True,
            'Notes': 'Calgary 5th-rounder in 2026. 6-foot-6 Finnish giant power forward. Unbelievable net-front utility and screen presence.'
        },
        {
            'Name': 'Jonas Woo', 'Year': 2026, 'Round': 6, 'Pick': 185, 'NHL_Team': 'Columbus Blue Jackets',
            'Pos': 'D', 'Projected_Pts': 51.0, 'Projected_PPP': 16.5, 'GP': 56, 'Goals_Last_Yr': 29, 'Assists_Last_Yr': 57, 'Pts_Last_Yr': 86,
            'League': 'WHL', 'Tier': 'Sleeper', 'Sniper_Score': 8.0, 'Sleeper_Score': 10.0, 'NHL_Drafted': True,
            'Notes': 'WHL defenseman scoring leader with 86 points in 56 games (1.54 PPG!). Columbus 6th-rounder in 2026. Premier 1PP QB steal.'
        },
        {
            'Name': 'Tomáš Galvas', 'Year': 2026, 'Round': 2, 'Pick': 54, 'NHL_Team': 'Pittsburgh Penguins',
            'Pos': 'D', 'Projected_Pts': 50.0, 'Projected_PPP': 16.0, 'GP': 32, 'Goals_Last_Yr': 8, 'Assists_Last_Yr': 16, 'Pts_Last_Yr': 24,
            'League': 'Czechia', 'Tier': 'Sleeper', 'Sniper_Score': 4.5, 'Sleeper_Score': 9.0, 'NHL_Drafted': True,
            'Notes': 'Pittsburgh 2nd-rounder in 2026. Elite transition skater. Calm, composed puck carrier who dominated WJC play.'
        },
        {
            'Name': 'Dmitriy Simashev', 'Year': 2023, 'Round': 1, 'Pick': 6, 'NHL_Team': 'Utah Hockey Club',
            'Pos': 'D', 'Projected_Pts': 49.0, 'Projected_PPP': 15.0, 'GP': 63, 'Goals_Last_Yr': 5, 'Assists_Last_Yr': 13, 'Pts_Last_Yr': 18,
            'League': 'KHL', 'Tier': 'Sleeper', 'Sniper_Score': 4.5, 'Sleeper_Score': 8.5, 'NHL_Drafted': True,
            'Notes': 'Unowned 6th overall pick from 2023. Massive 6-foot-4 skating wizard developing highly potent offensive transition game.'
        },
        {
            'Name': 'Alberts Šmits', 'Year': 2026, 'Round': 1, 'Pick': 5, 'NHL_Team': 'New York Rangers',
            'Pos': 'D', 'Projected_Pts': 48.0, 'Projected_PPP': 15.0, 'GP': 40, 'Goals_Last_Yr': 8, 'Assists_Last_Yr': 20, 'Pts_Last_Yr': 28,
            'League': 'DEL', 'Tier': 'PP Quarterback', 'Sniper_Score': 6.0, 'Sleeper_Score': 2.0, 'NHL_Drafted': True,
            'Notes': '6-foot-3 physical, engaged defender. Played against men in Finland and Germany, and represented Latvia at Olympics.'
        },
        {
            'Name': 'Timofei Runtso', 'Year': 2026, 'Round': 2, 'Pick': 57, 'NHL_Team': 'Montreal Canadiens',
            'Pos': 'D', 'Projected_Pts': 48.0, 'Projected_PPP': 14.5, 'GP': 68, 'Goals_Last_Yr': 11, 'Assists_Last_Yr': 33, 'Pts_Last_Yr': 44,
            'League': 'WHL', 'Tier': 'Sleeper', 'Sniper_Score': 5.8, 'Sleeper_Score': 8.5, 'NHL_Drafted': True,
            'Notes': 'Montreal 2nd-rounder in 2026. Rugged, heavy-hitting WHL blueliner who exploded for 44 points. Committing to Miami University.'
        },
        {
            'Name': 'Leo Sahlin Wallenius', 'Year': 2024, 'Round': 2, 'Pick': 53, 'NHL_Team': '2026 Draft Eligible',
            'Pos': 'D', 'Projected_Pts': 48.0, 'Projected_PPP': 16.0, 'GP': 43, 'Goals_Last_Yr': 6, 'Assists_Last_Yr': 22, 'Pts_Last_Yr': 28,
            'League': 'Sweden Jr', 'Tier': 'Sleeper', 'Sniper_Score': 5.5, 'Sleeper_Score': 8.0, 'NHL_Drafted': True,
            'Notes': 'Unowned Sharks 2nd-rounder. Sleek, beautiful skater with high-end offensive transition potential.'
        },
        {
            'Name': 'Caden Price', 'Year': 2023, 'Round': 3, 'Pick': 84, 'NHL_Team': 'Seattle Kraken',
            'Pos': 'D', 'Projected_Pts': 47.0, 'Projected_PPP': 15.0, 'GP': 62, 'Goals_Last_Yr': 10, 'Assists_Last_Yr': 45, 'Pts_Last_Yr': 55,
            'League': 'WHL', 'Tier': 'Sleeper', 'Sniper_Score': 6.0, 'Sleeper_Score': 8.0, 'NHL_Drafted': True,
            'Notes': 'Unowned Seattle 3rd-rounder. Smooth-skating, highly mobile defenseman who exploded for 55 points in the WHL.'
        },
        {
            'Name': 'Lukas Sawchyn', 'Year': 2026, 'Round': 3, 'Pick': 80, 'NHL_Team': 'Arizona Coyotes',
            'Pos': 'F', 'Projected_Pts': 64.0, 'Projected_PPP': 20.0, 'GP': 68, 'Goals_Last_Yr': 27, 'Assists_Last_Yr': 61, 'Pts_Last_Yr': 88,
            'League': 'WHL', 'Tier': 'Sleeper', 'Sniper_Score': 6.8, 'Sleeper_Score': 9.0, 'NHL_Drafted': False,
            'Notes': 'Unowned overager. Pure power-play maestro with 88 WHL points (1.29 PPG). ASU commit.'
        },
        {
            'Name': 'Félix Lacerte', 'Year': 2026, 'Round': 4, 'Pick': 105, 'NHL_Team': 'Colorado Avalanche',
            'Pos': 'F', 'Projected_Pts': 63.0, 'Projected_PPP': 21.0, 'GP': 62, 'Goals_Last_Yr': 38, 'Assists_Last_Yr': 48, 'Pts_Last_Yr': 86,
            'League': 'QMJHL', 'Tier': 'Sleeper', 'Sniper_Score': 8.2, 'Sleeper_Score': 8.5, 'NHL_Drafted': False,
            'Notes': 'Unowned overager. Slick playmaker with 86 points in 62 games (1.39 PPG) and an elite shot release. Vermont commit.'
        },
        {
            'Name': 'Philippe Veilleux', 'Year': 2026, 'Round': 6, 'Pick': 195, 'NHL_Team': 'Detroit Red Wings',
            'Pos': 'F', 'Projected_Pts': 62.0, 'Projected_PPP': 18.0, 'GP': 68, 'Goals_Last_Yr': 43, 'Assists_Last_Yr': 53, 'Pts_Last_Yr': 96,
            'League': 'QMJHL', 'Tier': 'Sleeper', 'Sniper_Score': 8.0, 'Sleeper_Score': 8.8, 'NHL_Drafted': False,
            'Notes': 'Unowned overager. Incredibly productive junior star with 43 goals and 96 points (1.41 PPG). Northeastern commit.'
        },
        {
            'Name': 'James Hagens', 'Year': 2025, 'Round': 1, 'Pick': 7, 'NHL_Team': 'Boston Bruins',
            'Pos': 'F', 'Projected_Pts': 81.0, 'Projected_PPP': 28.0, 'GP': 37, 'Goals_Last_Yr': 18, 'Assists_Last_Yr': 29, 'Pts_Last_Yr': 47,
            'League': 'NCAA', 'Tier': 'Elite', 'Sniper_Score': 7.5, 'Sleeper_Score': 1.0, 'NHL_Drafted': True,
            'Notes': 'Dynamic center with world-class playmaking and elite power-play vision.'
        },
        {
            'Name': 'Porter Martone', 'Year': 2025, 'Round': 1, 'Pick': 6, 'NHL_Team': 'Philadelphia Flyers',
            'Pos': 'F', 'Projected_Pts': 76.5, 'Projected_PPP': 23.0, 'GP': 57, 'Goals_Last_Yr': 33, 'Assists_Last_Yr': 38, 'Pts_Last_Yr': 71,
            'League': 'OHL', 'Tier': 'Elite', 'Sniper_Score': 8.8, 'Sleeper_Score': 1.0, 'NHL_Drafted': True,
            'Notes': 'Power forward who dominates net-front and eats up power play goals.'
        },
        {
            'Name': 'Michael Misa', 'Year': 2025, 'Round': 1, 'Pick': 2, 'NHL_Team': '2026 Draft Eligible',
            'Pos': 'F', 'Projected_Pts': 72.0, 'Projected_PPP': 21.0, 'GP': 67, 'Goals_Last_Yr': 28, 'Assists_Last_Yr': 47, 'Pts_Last_Yr': 75,
            'League': 'OHL', 'Tier': 'Elite', 'Sniper_Score': 8.2, 'Sleeper_Score': 2.5, 'NHL_Drafted': True,
            'Notes': 'Exceptional status player with elite speed, processing, and finishing.'
        },
        {
            'Name': 'Macklin Celebrini', 'Year': 2024, 'Round': 1, 'Pick': 1, 'NHL_Team': '2026 Draft Eligible',
            'Pos': 'F', 'Projected_Pts': 84.0, 'Projected_PPP': 30.0, 'GP': 70, 'Goals_Last_Yr': 32, 'Assists_Last_Yr': 32, 'Pts_Last_Yr': 64,
            'League': 'NHL', 'Tier': 'Elite', 'Sniper_Score': 8.9, 'Sleeper_Score': 1.0, 'NHL_Drafted': True,
            'Notes': 'Franchise 1C. Shoots with high-end volume and dominates all point situations.'
        },
        {
            'Name': 'Artyom Levshunov', 'Year': 2024, 'Round': 1, 'Pick': 2, 'NHL_Team': 'Chicago Blackhawks',
            'Pos': 'D', 'Projected_Pts': 48.0, 'Projected_PPP': 16.5, 'GP': 55, 'Goals_Last_Yr': 9, 'Assists_Last_Yr': 26, 'Pts_Last_Yr': 35,
            'League': 'AHL', 'Tier': 'PP Quarterback', 'Sniper_Score': 7.0, 'Sleeper_Score': 2.0, 'NHL_Drafted': True,
            'Notes': 'Highly athletic defenseman. Projects to quarterback Chicago\'s 1PP unit.'
        },
        {
            'Name': 'Ivan Demidov', 'Year': 2024, 'Round': 1, 'Pick': 5, 'NHL_Team': 'Montreal Canadiens',
            'Pos': 'F', 'Projected_Pts': 78.0, 'Projected_PPP': 26.0, 'GP': 45, 'Goals_Last_Yr': 23, 'Assists_Last_Yr': 37, 'Pts_Last_Yr': 60,
            'League': 'MHL', 'Tier': 'Elite', 'Sniper_Score': 8.1, 'Sleeper_Score': 1.2, 'NHL_Drafted': True,
            'Notes': 'Incredibly creative winger with elite perimeter play and PP control.'
        },
        {
            'Name': 'Connor Bedard', 'Year': 2023, 'Round': 1, 'Pick': 1, 'NHL_Team': 'Chicago Blackhawks',
            'Pos': 'F', 'Projected_Pts': 92.0, 'Projected_PPP': 34.0, 'GP': 68, 'Goals_Last_Yr': 22, 'Assists_Last_Yr': 39, 'Pts_Last_Yr': 61,
            'League': 'NHL', 'Tier': 'Elite', 'Sniper_Score': 9.8, 'Sleeper_Score': 1.0, 'NHL_Drafted': True,
            'Notes': 'Generational sniper. Top-tier power play release from the left circle.'
        },
        {
            'Name': 'Leo Carlsson', 'Year': 2023, 'Round': 1, 'Pick': 2, 'NHL_Team': 'Anaheim Ducks',
            'Pos': 'F', 'Projected_Pts': 70.0, 'Projected_PPP': 22.0, 'GP': 55, 'Goals_Last_Yr': 12, 'Assists_Last_Yr': 17, 'Pts_Last_Yr': 29,
            'League': 'NHL', 'Tier': 'Elite', 'Sniper_Score': 7.8, 'Sleeper_Score': 1.5, 'NHL_Drafted': True,
            'Notes': 'Highly intelligent playmaker with excellent puck retention skills.'
        },
        {
            'Name': 'Adam Fantilli', 'Year': 2023, 'Round': 1, 'Pick': 3, 'NHL_Team': 'Columbus Blue Jackets',
            'Pos': 'F', 'Projected_Pts': 71.5, 'Projected_PPP': 21.0, 'GP': 49, 'Goals_Last_Yr': 20, 'Assists_Last_Yr': 20, 'Pts_Last_Yr': 40,
            'League': 'NHL', 'Tier': 'Elite', 'Sniper_Score': 8.4, 'Sleeper_Score': 1.5, 'NHL_Drafted': True,
            'Notes': 'Power forward package with an elite wrister. Projects to dominate top PP line.'
        }
    ]
    
    # Calculate PPG dynamically
    for row in data:
        gp = row.get('GP', 0)
        pts = row.get('Pts_Last_Yr', 0)
        row['PPG'] = round(pts / gp, 2) if gp > 0 else 0.0
        
    return pd.DataFrame(data)


# --- 3. LIVE NHL API FETCH FOR MULTIPLE YEARS ---
@st.cache_data(show_spinner=True)
def fetch_nhl_draft_data_for_years(years):
    combined_picks = []
    
    # Preseeded base map to check overlays (as pure Python dicts)
    df_preseeded = get_preseeded_prospects()
    preseeded_map = {normalize_name(p['Name']): p for p in df_preseeded.to_dict('records')}
    
    for year in years:
        try:
            url = f"https://api-web.nhle.com/v1/draft/picks/{year}/all"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for pick in data.get('picks', []):
                    first_raw = pick.get('firstName', '')
                    last_raw = pick.get('lastName', '')
                    
                    first_name = first_raw.get('default', '').strip() if isinstance(first_raw, dict) else str(first_raw).strip()
                    last_name = last_raw.get('default', '').strip() if isinstance(last_raw, dict) else str(last_raw).strip()
                    
                    full_name = f"{first_name} {last_name}".strip()
                    norm_name = normalize_name(full_name)
                    
                    nhl_team = pick.get('teamCommonName', {}).get('default', 'Unknown')
                    pos = pick.get('position', 'F')
                    round_num = pick.get('roundNumber', 1)
                    pick_num = pick.get('pickNumber', 1)
                    
                    if norm_name in preseeded_map:
                        p_data = preseeded_map[norm_name].copy()
                        p_data['NHL_Team'] = nhl_team
                        p_data['Round'] = round_num
                        p_data['Pick'] = pick_num
                        p_data['NHL_Drafted'] = True
                        combined_picks.append(p_data)
                    else:
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
                            "GP": 0,
                            "Goals_Last_Yr": 0,
                            "Assists_Last_Yr": 0,
                            "Pts_Last_Yr": 0,
                            "PPG": 0.0,
                            "League": "Draft API",
                            "Tier": "Prospect",
                            "Sniper_Score": 5.0,
                            "Sleeper_Score": 3.0,
                            "Notes": "Live synced player from official NHL Draft API.",
                            "NHL_Drafted": True
                        })
        except Exception as e:
            pass
            
    if combined_picks:
        return pd.DataFrame(combined_picks)
    else:
        return df_preseeded

# --- 4. PARSE FANTAX ROSTERS TO DISCOVER OWNED PLAYERS ---
def find_player_column(df):
    possible_cols = ['Player', 'Player Name', 'Name', 'player_name', 'player', 'PLAYER', 'PLAYER NAME', 'PlayerName', 'player name']
    for col in df.columns:
        if str(col).strip() in possible_cols:
            return col
    for col in df.columns:
        if 'player' in str(col).lower() or 'name' in str(col).lower():
            return col
    if len(df.columns) == 1:
        return df.columns[0]
    return None

@st.cache_data
def get_owned_players_database(file_tokens=(), _uploaded_files=None):
    owned_players = {}
    
    # Track which files we've processed to avoid duplicate counts
    processed_filenames = set()
    
    # 1. Automatically scan local/repo directories for Fantrax rosters
    search_paths = ["./", "./rosters/", "/workspace/knowledge/"]
    matched_files = []
    for path in search_paths:
        if os.path.exists(path):
            try:
                for f in os.listdir(path):
                    if f.endswith('.csv') and ('Fantrax' in f or 'Roster' in f):
                        matched_files.append(os.path.join(path, f))
            except Exception:
                pass
                
    for filepath in matched_files:
        filename = os.path.basename(filepath)
        if filename in processed_filenames:
            continue
        processed_filenames.add(filename)
        
        match = re.search(r"\((\d+)\)", filename)
        if match:
            team_name = f"Team {match.group(1)}"
        else:
            match_underscore = re.search(r"_(\d+)\.csv$", filename)
            if match_underscore:
                team_name = f"Team {match_underscore.group(1)}"
            else:
                team_name = filename.replace("Fantrax-Team-Roster-", "").replace(".csv", "").replace("_", " ").strip()
                
        try:
            df = pd.read_csv(filepath)
            p_col = find_player_column(df)
            if not p_col and len(df) > 0:
                df_alt = pd.read_csv(filepath, skiprows=1)
                p_col_alt = find_player_column(df_alt)
                if p_col_alt:
                    df = df_alt
                    p_col = p_col_alt
                    
            if p_col:
                for _, row in df.iterrows():
                    player = row[p_col]
                    if pd.notna(player) and str(player).strip():
                        status = row.get("Status", "Owned") if hasattr(row, "get") and "Status" in row else "Owned"
                        pos = row.get("Pos", "F") if hasattr(row, "get") and "Pos" in row else "F"
                        norm_p = normalize_name(str(player))
                        owned_players[norm_p] = {
                            "Team": team_name,
                            "Status": status,
                            "Pos": pos,
                            "Raw_Name": str(player).strip()
                        }
        except Exception:
            pass
            
    # 2. Overlay manually uploaded files from live sidebar
    if _uploaded_files:
        for uploaded_file in _uploaded_files:
            filename = uploaded_file.name
            if filename in processed_filenames:
                continue
            processed_filenames.add(filename)
            
            match = re.search(r"\((\d+)\)", filename)
            if match:
                team_name = f"Team {match.group(1)}"
            else:
                match_underscore = re.search(r"_(\d+)\.csv$", filename)
                if match_underscore:
                    team_name = f"Team {match_underscore.group(1)}"
                else:
                    clean_name = filename.replace("Fantrax-Team-Roster-", "").replace(".csv", "").replace("_", " ").strip()
                    team_name = clean_name if clean_name else "Uploaded List"
                    
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file)
                p_col = find_player_column(df)
                if not p_col and len(df) > 0:
                    uploaded_file.seek(0)
                    df_alt = pd.read_csv(uploaded_file, skiprows=1)
                    p_col_alt = find_player_column(df_alt)
                    if p_col_alt:
                        df = df_alt
                        p_col = p_col_alt
                        
                if p_col:
                    for _, row in df.iterrows():
                        player = row[p_col]
                        if pd.notna(player) and str(player).strip():
                            status = row.get("Status", "Owned") if hasattr(row, "get") and "Status" in row else "Owned"
                            pos = row.get("Pos", "F") if hasattr(row, "get") and "Pos" in row else "F"
                            norm_p = normalize_name(str(player))
                            owned_players[norm_p] = {
                                "Team": team_name,
                                "Status": status,
                                "Pos": pos,
                                "Raw_Name": str(player).strip()
                            }
            except Exception:
                pass
                
    return owned_players


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

# Sidebar: League Rosters Settings
st.sidebar.markdown("---")
st.sidebar.subheader("📋 League Rosters Settings")
hide_owned = st.sidebar.checkbox("Hide Already Owned Players", value=True)
filter_only_drafted = st.sidebar.checkbox("Only Show NHL-Drafted Prospects", value=True)
uploaded_rosters = st.sidebar.file_uploader("Upload More Rosters or Custom Player Lists (CSVs)", type=["csv"], accept_multiple_files=True)

# Parse Rosters with cache-invalidation file tokens
file_tokens = tuple((f.name, getattr(f, 'size', 0)) for f in uploaded_rosters) if uploaded_rosters else ()
owned_db = get_owned_players_database(file_tokens=file_tokens, _uploaded_files=uploaded_rosters)
if owned_db:
    st.sidebar.success(f"Loaded {len(owned_db)} owned players from Fantrax rosters.")

# Ensure NHL_Drafted column exists
if 'NHL_Drafted' not in df_base.columns:
    df_base['NHL_Drafted'] = True
df_base['NHL_Drafted'] = df_base['NHL_Drafted'].fillna(True)

# Merge Ownership into the Main Database
df_base['Owned_By'] = None
df_base['Owned_Status'] = None
if owned_db:
    owned_keys = list(owned_db.keys())
    for idx, row in df_base.iterrows():
        norm_n = normalize_name(row['Name'])
        matched_key = None
        if norm_n in owned_db:
            matched_key = norm_n
        else:
            # Strict last-name check for safety
            last_name_parts = norm_n.split()
            last_name = last_name_parts[-1] if last_name_parts else norm_n
            matches = difflib.get_close_matches(norm_n, owned_keys, n=1, cutoff=0.92)
            if matches and last_name in matches[0]:
                matched_key = matches[0]
                
        if matched_key:
            df_base.at[idx, 'Owned_By'] = owned_db[matched_key]['Team']
            df_base.at[idx, 'Owned_Status'] = owned_db[matched_key]['Status']

# Sidebar Sorting
st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Draft Board Sorting & Performance Filters")
sort_option = st.sidebar.selectbox(
    "Sort Board By:",
    [
        "Last Season Points Per Game (PPG)",
        "Pure Offensive Points (Proj. Pts)",
        "Powerplay Utility (Proj. PPP)",
        "Sniper Score / Goals",
        "Sleeper / Value Steal Rating",
        "Real NHL Draft Pick #"
    ],
    index=0
)

# Minimum PPG Filter
min_ppg = st.sidebar.slider("Minimum Last Season PPG Filter:", min_value=0.0, max_value=1.5, value=0.0, step=0.1)

# Sidebar Filters
filter_pos = st.sidebar.multiselect("Positions", ["F", "D"], default=["F", "D"])
filter_tier = st.sidebar.multiselect("Prospect Types", ["Elite", "Sniper", "Sleeper", "PP Quarterback", "Prospect"], default=["Elite", "Sniper", "Sleeper", "PP Quarterback", "Prospect"])

# Search Bar
search_query = st.sidebar.text_input("🔍 Search Player Name")

# Sidebar Action Buttons
col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    if st.button("🗑️ Reset Drafts"):
        st.session_state.drafted_players = set()
        st.session_state.draft_log = []
        st.rerun()
with col_sb2:
    if st.button("⭐ Clear Watchlist"):
        st.session_state.favorite_players = set()
        st.rerun()

# Apply Filters
df_filtered = df_base[df_base['Year'].isin(selected_years)].copy()
df_filtered = df_filtered[df_filtered['Pos'].isin(filter_pos)]
df_filtered = df_filtered[df_filtered['Tier'].isin(filter_tier)]
if min_ppg > 0.0:
    df_filtered = df_filtered[df_filtered['PPG'] >= min_ppg]
if search_query:
    df_filtered = df_filtered[df_filtered['Name'].str.contains(search_query, case=False)]

if hide_owned:
    df_filtered = df_filtered[df_filtered['Owned_By'].isna()]

if filter_only_drafted:
    df_filtered = df_filtered[df_filtered['NHL_Drafted'] == True]

# Create Tabs
tab_draft, tab_favs, tab_teams, tab_api = st.tabs([
    "🎯 Live Draft Center", 
    "⭐ Favorites Watchlist", 
    "🛡️ NHL Team Portfolios",
    "🔌 API Connection Hub"
])

# Helper function to get badge html
def get_performance_badge_html(row):
    ppg = row.get('PPG', 0.0)
    tier = row.get('Tier', '')
    round_num = row.get('Round', 1)
    
    if ppg >= 1.2 and round_num >= 3:
        return "<span style='background-color:#FEF3C7; color:#B45309; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:700;'>🔥 Breakout Sleeper</span>"
    elif ppg >= 1.0:
        return "<span style='background-color:#D1FAE5; color:#047857; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:700;'>💎 Top Producer</span>"
    elif tier == "PP Quarterback":
        return "<span style='background-color:#E0F2FE; color:#0369A1; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:700;'>🏒 1PP QB</span>"
    return ""

# ==================== TAB 1: LIVE DRAFT CENTER ====================
with tab_draft:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader(f"Available Prospects — {sort_option}")
        
        # Split available vs drafted players
        available_players = df_filtered[~df_filtered['Name'].isin(st.session_state.drafted_players)].copy()

        if sort_option == "Last Season Points Per Game (PPG)":
            available_players = available_players.sort_values(by=["PPG", "Projected_Pts"], ascending=[False, False])
        elif sort_option == "Pure Offensive Points (Proj. Pts)":
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
                is_owned = pd.notna(row['Owned_By'])
                is_fav = row['Name'] in st.session_state.favorite_players
                badge_html = get_performance_badge_html(row)
                
                with st.container():
                    cols = st.columns([1, 1, 3, 2, 2, 2, 2])
                    
                    # Draft Button
                    with cols[0]:
                        is_disabled = is_owned or (not row.get('NHL_Drafted', True))
                        button_label = "Owned" if is_owned else ("Ineligible" if not row.get('NHL_Drafted', True) else "Draft")
                        if st.button(button_label, key=f"draft_{row['Name']}_{row['Year']}", disabled=is_disabled):
                            st.session_state.drafted_players.add(row['Name'])
                            st.session_state.draft_log.append({
                                "Name": row['Name'],
                                "NHL_Team": row['NHL_Team'],
                                "Projected_Pts": row['Projected_Pts'],
                                "Pos": row['Pos'],
                                "Year": row['Year']
                            })
                            st.rerun()

                    # Favorite / Star Button
                    with cols[1]:
                        fav_label = "⭐ Saved" if is_fav else "☆ Star"
                        if st.button(fav_label, key=f"fav_{row['Name']}_{row['Year']}"):
                            if is_fav:
                                st.session_state.favorite_players.remove(row['Name'])
                            else:
                                st.session_state.favorite_players.add(row['Name'])
                            st.rerun()
                    
                    # Player Info
                    with cols[2]:
                        star_prefix = "⭐ " if is_fav else ""
                        badge_str = f" {badge_html}" if badge_html else ""
                        if is_owned:
                            st.markdown(f"{star_prefix}**{row['Name']}** ({row['Pos']}){badge_str} <span style='background-color:#FEE2E2; color:#DC2626; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; margin-left:8px;'>❌ Owned by {row['Owned_By']} ({row['Owned_Status']})</span>", unsafe_allow_html=True)
                        elif not row.get('NHL_Drafted', True):
                            st.markdown(f"{star_prefix}**{row['Name']}** ({row['Pos']}){badge_str} <span style='background-color:#FEF3C7; color:#D97706; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; margin-left:8px;'>⚠️ Ineligible (Undrafted)</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"{star_prefix}**{row['Name']}** ({row['Pos']}){badge_str}", unsafe_allow_html=True)
                        
                        if row.get('NHL_Drafted', True):
                            if 'Draft Eligible' in str(row.get('NHL_Team', '')) or 'Draft Eligible' in str(row.get('Notes', '')):
                                st.caption(f"{row['Year']} Draft Eligible · Projected #{row['Pick']} Overall · {row['League']}")
                            else:
                                st.caption(f"{row['Year']} Draft · Pick #{row['Pick']} by {row['NHL_Team']} · {row['League']}")
                        else:
                            st.caption(f"Undrafted · NCAA Commitment · {row['League']}")

                    # Stat Line & PPG
                    with cols[3]:
                        if row.get('GP', 0) > 0:
                            st.metric("Last Yr PPG", f"{row.get('PPG', 0.0):.2f}")
                            st.caption(f"{row.get('Goals_Last_Yr',0)}G · {row.get('Assists_Last_Yr',0)}A in {row.get('GP',0)} GP")
                        else:
                            st.metric("Proj. Pts", f"{row['Projected_Pts']} pts")

                    # Projected PPP
                    with cols[4]:
                        st.metric("Proj. PPP", f"{row['Projected_PPP']} pts")
                        
                    # Sniper / Sleeper Tiers
                    with cols[5]:
                        if row['Tier'] == "Sleeper":
                            st.markdown(f"⭐ **Sleeper** ({row['Sleeper_Score']}/10)")
                        elif row['Tier'] == "Sniper":
                            st.markdown(f"🎯 **Sniper** ({row['Sniper_Score']}/10)")
                        elif row['Tier'] == "PP Quarterback":
                            st.markdown(f"🏒 **PP QB**")
                        else:
                            st.markdown(f"💎 **{row['Tier']}**")
                            
                    # Scouting Notes
                    with cols[6]:
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

# ==================== TAB 2: FAVORITES WATCHLIST ====================
with tab_favs:
    st.subheader("⭐ Curated Favorites & Watchlist")
    st.write("Your priority shortlist of must-target prospects for draft day.")
    
    fav_names = list(st.session_state.favorite_players)
    
    if not fav_names:
        st.info("⭐ Your watchlist is currently empty! Click the '☆ Star' button next to any player in the Live Draft Center to save them here.")
    else:
        df_favs = df_base[df_base['Name'].isin(fav_names)].copy()
        
        # Summary metrics
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            st.metric("Total Watchlist Targets", f"{len(df_favs)} players")
        with f_col2:
            avg_proj = df_favs['Projected_Pts'].mean() if not df_favs.empty else 0
            st.metric("Avg Projected Pts", f"{avg_proj:.1f} pts")
        with f_col3:
            avg_ppp = df_favs['Projected_PPP'].mean() if not df_favs.empty else 0
            st.metric("Avg Projected PPP", f"{avg_ppp:.1f} pts")
            
        st.markdown("---")
        
        # Sorting for Watchlist
        fav_sort = st.selectbox(
            "Sort Watchlist By:",
            ["Points Per Game (PPG)", "Projected Points", "Projected PPP", "Real Draft Pick #", "Position"],
            index=0,
            key="fav_sort_selectbox"
        )
        
        if fav_sort == "Points Per Game (PPG)":
            df_favs = df_favs.sort_values(by=["PPG", "Projected_Pts"], ascending=[False, False])
        elif fav_sort == "Projected Points":
            df_favs = df_favs.sort_values(by="Projected_Pts", ascending=False)
        elif fav_sort == "Projected PPP":
            df_favs = df_favs.sort_values(by="Projected_PPP", ascending=False)
        elif fav_sort == "Real Draft Pick #":
            df_favs = df_favs.sort_values(by=["Year", "Round", "Pick"], ascending=[False, True, True])
        elif fav_sort == "Position":
            df_favs = df_favs.sort_values(by=["Pos", "Projected_Pts"], ascending=[True, False])
            
        # Render Watchlist Player Cards
        for index, row in df_favs.iterrows():
            is_drafted = row['Name'] in st.session_state.drafted_players
            is_owned = pd.notna(row['Owned_By'])
            badge_html = get_performance_badge_html(row)
            badge_str = f" {badge_html}" if badge_html else ""
            
            with st.container():
                f_cols = st.columns([1, 1, 3, 2, 2, 2, 2])
                
                # Draft Action
                with f_cols[0]:
                    if is_drafted:
                        st.markdown("<span style='color:#9CA3AF; font-size:12px;'>❌ Drafted</span>", unsafe_allow_html=True)
                    else:
                        button_label = "Owned" if is_owned else ("Ineligible" if not row.get('NHL_Drafted', True) else "Draft")
                        is_disabled = is_owned or (not row.get('NHL_Drafted', True))
                        if st.button(button_label, key=f"fav_tab_draft_{row['Name']}_{row['Year']}", disabled=is_disabled):
                            st.session_state.drafted_players.add(row['Name'])
                            st.session_state.draft_log.append({
                                "Name": row['Name'],
                                "NHL_Team": row['NHL_Team'],
                                "Projected_Pts": row['Projected_Pts'],
                                "Pos": row['Pos'],
                                "Year": row['Year']
                            })
                            st.rerun()

                # Remove from Favorites Button
                with f_cols[1]:
                    if st.button("🗑️ Remove", key=f"fav_tab_remove_{row['Name']}_{row['Year']}"):
                        st.session_state.favorite_players.remove(row['Name'])
                        st.rerun()

                # Player Info
                with f_cols[2]:
                    if is_drafted:
                        st.markdown(f"~~⭐ **{row['Name']}** ({row['Pos']}){badge_str}~~ <span style='background-color:#E5E7EB; color:#4B5563; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600;'>Taken</span>", unsafe_allow_html=True)
                    elif is_owned:
                        st.markdown(f"⭐ **{row['Name']}** ({row['Pos']}){badge_str} <span style='background-color:#FEE2E2; color:#DC2626; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; margin-left:8px;'>❌ Owned by {row['Owned_By']} ({row['Owned_Status']})</span>", unsafe_allow_html=True)
                    elif not row.get('NHL_Drafted', True):
                        st.markdown(f"⭐ **{row['Name']}** ({row['Pos']}){badge_str} <span style='background-color:#FEF3C7; color:#D97706; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; margin-left:8px;'>⚠️ Ineligible (Undrafted)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"⭐ **{row['Name']}** ({row['Pos']}){badge_str}", unsafe_allow_html=True)
                        
                    if row.get('NHL_Drafted', True):
                        if 'Draft Eligible' in str(row.get('NHL_Team', '')) or 'Draft Eligible' in str(row.get('Notes', '')):
                            st.caption(f"{row['Year']} Draft Eligible · Projected #{row['Pick']} Overall · {row['League']}")
                        else:
                            st.caption(f"{row['Year']} Draft · Pick #{row['Pick']} by {row['NHL_Team']} · {row['League']}")
                    else:
                        st.caption(f"Undrafted · NCAA Commitment · {row['League']}")

                # Metrics & Info
                with f_cols[3]:
                    if row.get('GP', 0) > 0:
                        st.metric("Last Yr PPG", f"{row.get('PPG', 0.0):.2f}")
                        st.caption(f"{row.get('Goals_Last_Yr',0)}G · {row.get('Assists_Last_Yr',0)}A in {row.get('GP',0)} GP")
                    else:
                        st.metric("Proj. Pts", f"{row['Projected_Pts']} pts")
                with f_cols[4]:
                    st.metric("Proj. PPP", f"{row['Projected_PPP']} pts")
                with f_cols[5]:
                    if row['Tier'] == "Sleeper":
                        st.markdown(f"⭐ **Sleeper** ({row['Sleeper_Score']}/10)")
                    elif row['Tier'] == "Sniper":
                        st.markdown(f"🎯 **Sniper** ({row['Sniper_Score']}/10)")
                    elif row['Tier'] == "PP Quarterback":
                        st.markdown(f"🏒 **PP QB**")
                    else:
                        st.markdown(f"💎 **{row['Tier']}**")
                with f_cols[6]:
                    st.caption(row['Notes'])

                st.markdown("---")

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
        st.dataframe(team_stash[["Name", "Year", "Round", "Pick", "Pos", "Projected_Pts", "Projected_PPP", "PPG", "Goals_Last_Yr", "Notes"]])
        
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
