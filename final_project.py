# final_project.py

# --- Imports ---
import streamlit as st
import requests

# --- Streamlit App Title ---
st.title("NHL Free Agency Analyzer")

# --- Team Input Section ---
team_input = st.text_input("Enter an NHL team name (e.g., Toronto Maple Leafs):")

# --- Helper Function to Get Team Info and Roster ---
def get_team_info(team_name):
    try:
        # Step 1: Get all teams from NHL API
        teams_url = "https://statsapi.web.nhl.com/api/v1/teams"
        response = requests.get(teams_url)
        teams = response.json()["teams"]

        # Step 2: Match user input to a valid team name
        team_id = None
        for team in teams:
            if team_name.lower() in team["name"].lower():
                team_id = team["id"]
                break

        # If no team matched
        if team_id is None:
            return None, f"Team '{team_name}' not found. Please check your spelling."

        # Step 3: Get detailed info including roster for the matched team
        team_detail_url = f"https://statsapi.web.nhl.com/api/v1/teams/{team_id}?expand=team.roster"
        team_response = requests.get(team_detail_url).json()
        team_info = team_response["teams"][0]

        return team_info, None

    except Exception as e:
        return None, f"Error fetching team data: {str(e)}"

# --- Display Team Info After Input ---
if team_input:
    st.success(f"You entered: {team_input}")
    
    # Call the function to get team data
    team_info, error = get_team_info(team_input)
    
    # Handle any API or team name errors
    if error:
        st.error(error)
    else:
        # Display basic team information
        st.subheader("Team Information")
        st.write(f"**Team Name:** {team_info['name']}")
        st.write(f"**Venue:** {team_info['venue']['name']}")
        st.write(f"**Official Site:** {team_info['officialSiteUrl']}")

        # Display full player roster
        st.subheader("Team Roster")
        for player in team_info["roster"]["roster"]:
            st.write(f"- {player['person']['fullName']} ({player['position']['name']})")
