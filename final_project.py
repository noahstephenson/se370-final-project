import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import plotly.graph_objects as go
import sqlite3

DB_PATH = "nhl_data.db"

@st.cache_data
def load_data_from_sqlite():
    conn = sqlite3.connect(DB_PATH)

    flyers_standard = pd.read_sql("SELECT * FROM flyers_standard_2024", conn)
    flyers_advanced = pd.read_sql("SELECT * FROM flyers_advanced_2024", conn)
    flyers_goalie = pd.read_sql("SELECT * FROM flyers_goalie_2024", conn)
    flyers_misc = pd.read_sql("SELECT * FROM flyers_misc_2024", conn)
    nhl_team_stats = pd.read_sql("SELECT * FROM nhl_team_stats_2024", conn)

    flyers_standard = flyers_standard.rename(columns={
        flyers_standard.columns[1]: "Player",
        flyers_standard.columns[4]: "GP",
        flyers_standard.columns[10]: "G",
        flyers_standard.columns[14]: "A",
        flyers_standard.columns[8]: "PIM",
        flyers_standard.columns[9]: "+/-"
    })

    flyers_advanced = flyers_advanced.rename(columns={
        flyers_advanced.columns[1]: "Player",
        flyers_advanced.columns[4]: "GP",
        flyers_advanced.columns[5]: "CF",
        flyers_advanced.columns[9]: "FF",
        flyers_advanced.columns[16]: "oZS%",
        flyers_advanced.columns[17]: "dZS%",
        flyers_advanced.columns[3]: "Pos"
    })

    flyers_merged = pd.merge(flyers_advanced, flyers_standard[["Player", "G", "A", "PIM", "+/-"]], on="Player", how="left")

    for col in ["GP", "G", "A", "PIM", "+/-", "CF", "FF", "oZS%", "dZS%"]:
        if col in flyers_merged.columns:
            flyers_merged[col] = pd.to_numeric(flyers_merged[col], errors='coerce')

    conn.close()
    return flyers_merged, flyers_goalie, flyers_misc, nhl_team_stats

flyers_advanced, flyers_goalie, flyers_misc, nhl_team_stats = load_data_from_sqlite()

if flyers_advanced is None:
    st.stop()

flyers_advanced = flyers_advanced[flyers_advanced['GP'] >= 10]
st.title("Philadelphia Flyers Advanced Analytics Dashboard")

tabs = st.tabs(["Flyers Player Visuals", "Team Summary", "League Stats", "Goalie Stats", "Player Compare", "Rink Map"])

# --------------------------- TAB 1 ---------------------------
with tabs[0]:
    st.header("Flyers Skater Analytics Dashboard (Min 10 GP)")

    flyers_advanced["PTS"] = flyers_advanced["G"] + flyers_advanced["A"]
    flyers_advanced["CF60"] = flyers_advanced["CF"] / flyers_advanced["GP"] * 60
    flyers_advanced["FF60"] = flyers_advanced["FF"] / flyers_advanced["GP"] * 60

    st.subheader("Player Production: Goals, Assists, and Total Points")
    production_df = flyers_advanced[["Player", "G", "A", "PTS"]].copy().dropna().sort_values("PTS", ascending=False).head(15)
    production_melted = production_df.melt(id_vars="Player", value_vars=["G", "A", "PTS"], var_name="Stat", value_name="Count")
    fig7 = px.bar(production_melted, x="Player", y="Count", color="Stat", barmode="group",
                  title="Top 15 Flyers by Goals, Assists, and Total Points")
    fig7.update_layout(xaxis_tickangle=-45, height=600)
    st.plotly_chart(fig7, use_container_width=True)
    st.caption("This grouped bar chart shows which players are contributing most to the Flyers’ offense in terms of goals, assists, and total points. A General Manager (GM) can use this to evaluate whether the team needs more finishers (goal scorers), playmakers (assisters), or well-rounded producers.")

    st.subheader("CF/60 vs Points per Game (PTS/GP)")

# Calculate Points per Game
    flyers_advanced["PTS_per_GP"] = flyers_advanced["PTS"] / flyers_advanced["GP"]

# Create the improved scatter plot
    fig1 = px.scatter(
        flyers_advanced,
        x="CF60",
        y="PTS_per_GP",
        text="Player",
        hover_data=["GP", "G", "A", "PTS"],
        color="Player",
        labels={
            "CF60": "Corsi For per 60 (CF/60)",
            "PTS_per_GP": "Points per Game (PTS/GP)"
        },
        title="Possession vs Offensive Output: CF/60 vs Points per Game"
    )

    fig1.update_traces(marker=dict(size=12), textposition="top center")
    fig1.update_layout(width=900, height=600)
    st.plotly_chart(fig1, use_container_width=True)

# Add new explanatory caption
    st.caption("This scatter plot compares Corsi For per 60 minutes (CF/60)—which measures how many shot attempts a player helps generate during their time on ice—with Points per Game (PTS/GP), a standard indicator of scoring output. CF/60 highlights players who are actively driving puck possession and offensive pressure, while PTS/GP shows who is converting those opportunities into tangible results. Players in the top-right quadrant are the most complete offensive contributors: they consistently tilt the ice in their team’s favor and finish plays with goals or assists. These are the ideal dual-threat players that coaches and GMs prioritize when building scoring lines. In contrast, players in the top-left may generate pressure but fail to capitalize, signaling a possible finishing issue. Those in the bottom-right might have scoring totals buoyed by power play time or")
    st.subheader("Top oZS% (Offensive Zone Start%)")
    top_ozs = flyers_advanced.sort_values("oZS%", ascending=False).head(10)
    fig2 = px.bar(top_ozs, x="oZS%", y="Player", orientation="h",
                  color="oZS%", title="Top 10 Flyers by Offensive Zone Start %")
    fig2.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Offensive Zone Start Percentage (oZS%) measures how frequently a player begins their shifts with a faceoff in the offensive zone, offering insight into how coaches choose to deploy their players. A high oZS% suggests that a player is being given favorable conditions to generate scoring chances, often reflecting a level of trust in their offensive abilities. However, deployment alone doesn’t guarantee results. By comparing oZS% to actual shot generation or point production, General Managers can evaluate whether a player is capitalizing on the opportunities they're given. If a player has a high oZS% but low output, it may indicate inefficiency or misuse; conversely, a player with modest oZS% but strong results might be underutilized. This metric helps GMs assess not only individual effectiveness but also coaching strategy and lineup optimization.")

    st.subheader("Player Share of Team CF and FF")
    total_cf = flyers_advanced["CF"].sum()
    total_ff = flyers_advanced["FF"].sum()
    flyers_advanced["CF_%"] = flyers_advanced["CF"] / total_cf * 100
    flyers_advanced["FF_%"] = flyers_advanced["FF"] / total_ff * 100

    fig4 = px.bar(flyers_advanced.sort_values("CF_%", ascending=False),
                  x="CF_%", y="Player", orientation="h",
                  title="Corsi For % Contribution by Player")
    fig4.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig4, use_container_width=True)

    fig5 = px.bar(flyers_advanced.sort_values("FF_%", ascending=False),
                  x="FF_%", y="Player", orientation="h",
                  title="Fenwick For % Contribution by Player")
    fig5.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("These horizontal bar charts show the percentage of total team shot attempts—measured by Corsi (CF) and Fenwick (FF)—that each player contributes over the season. Corsi counts all shot attempts, while Fenwick excludes blocked shots, making both metrics valuable for understanding puck possession. By expressing each player’s contribution as a percentage of the team total, we can clearly identify which individuals are consistently driving play. Players with the highest values are not just involved in offensive sequences—they’re the engines behind them. This allows General Managers to pinpoint who the team relies on to sustain offensive pressure, even beyond traditional stats like goals or assists. It also reveals players who may be undervalued or overused in their roles. A GM can use this data to determine line combinations, special teams assignments, or even make trade decisions based on possession impact rather than just scoring.")

    st.subheader("oZS% vs FF/60")
    fig6 = px.scatter(flyers_advanced, x="oZS%", y="FF60", text="Player", color="Player",
                      title="Deployment vs Shot Generation: oZS% vs FF/60",
                      labels={"oZS%": "Offensive Zone Start %", "FF60": "Fenwick For per 60"})
    fig6.update_traces(marker=dict(size=12), textposition="top center")
    st.plotly_chart(fig6, use_container_width=True)
    st.caption("This scatter plot compares how often players begin their shifts in the offensive zone (oZS%) with how frequently they generate unblocked shot attempts per 60 minutes (FF/60). A high oZS% means the coach is deliberately deploying a player in more favorable, offensive situations. FF/60 reflects how active a player is in helping the team generate legitimate scoring chances — specifically those that get past defenders.")
    st.caption("Players located in the top-right quadrant of this chart are making the most of their opportunities: they are trusted with offensive zone starts and are delivering high shot generation. This suggests they are valuable assets who can be relied on to sustain pressure in the opponent’s end.")
    st.caption("Meanwhile, players in the bottom-right quadrant are being deployed offensively but not generating many chances — a potential red flag for inefficiency. Conversely, those in the top-left quadrant are creating scoring opportunities despite fewer offensive zone starts, which may indicate hidden value or underutilization.")
    st.caption("For General Managers, this chart helps answer critical questions: Are our offensive players actually generating pressure? Are any players over-deployed or under-deployed? Should coaching strategies or line combinations be adjusted to maximize production?")

#-----------------------------------------------------------------

    import plotly.express as px
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    import streamlit as st

    # Load Flyers advanced stats CSV
    flyers_advanced = pd.read_csv("flyers_advanced_2024.csv", header=1)
    flyers_standard = pd.read_csv("flyers_standard_2024.csv", header=1)
    flyers_advanced = pd.read_csv("flyers_advanced_2024.csv", header=1)

    # Merge G and A from standard into advanced
    flyers_advanced = pd.merge(
        flyers_advanced,
        flyers_standard[["Player", "G", "A"]],
        on="Player",
        how="left"
    )

    # Filter players with at least 10 GP and drop missing values
    filtered_df = flyers_advanced[flyers_advanced["GP"] >= 10].dropna(subset=["CF", "CA", "oZS%", "dZS%"])

    # Select features and player names
    X = filtered_df[["CF", "CA", "oZS%", "dZS%"]]
    player_names = filtered_df["Player"]

    # Standardize the data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # KMeans clustering into 4 groups
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    # Add cluster labels
    filtered_df["Role Cluster"] = clusters

    # Create an interactive scatterplot
    fig = px.scatter(
        filtered_df,
        x="CF",
        y="CA",
        color="Role Cluster",
        text="Player",
        hover_data=["GP", "oZS%", "dZS%"],
        title="Flyers Player Archetypes: Corsi For vs Corsi Against (Clustered)",
        labels={"CF": "Corsi For", "CA": "Corsi Against"}
    )
    fig.update_traces(marker=dict(size=12), textposition="top center")
    fig.update_layout(height=600)

    # Display in Streamlit
    st.plotly_chart(fig)

    # Caption for context
    st.caption(
       "This chart visualizes Flyers players by clustering them into role-based archetypes using shot generation (Corsi For), shot suppression (Corsi Against), and zone deployment (oZS%, dZS%). Players are grouped not by position or ice time, but by how they tilt the ice and how coaches use them."
       "Offensive Drivers (e.g. Cluster 0) are given offensive zone starts and generate heavy shot volume while limiting chances against."
       "Defensive Anchors (Cluster 1) start in their own zone and effectively suppress opposing chances."
       "Transition Players (Cluster 2) are balanced in usage and performance — versatile in all situations."
        "Low-Impact Depth (Cluster 3) generate little offense and allow above-average shot volume, often in sheltered minutes."
        "This role-based clustering helps decision-makers evaluate roster composition, target specific player types in trades, and optimize matchups beyond raw scoring stats."
    )

#-----------------------------------------------------------------
with tabs[1]:
    st.header("Flyers 2024 Team Summary Dashboard")

    # Load Flyers player stats from CSV
    flyers_advanced = pd.read_csv("flyers_advanced_2024.csv", header=1)
    flyers_standard = pd.read_csv("flyers_standard_2024.csv", header=1)

    # Merge goals and assists into flyers_advanced
    flyers_advanced = pd.merge(
        flyers_advanced,
        flyers_standard[["Player", "G", "A"]],
        on="Player",
        how="left"
    )

    # Load NHL team stats from CSV
    nhl_team_stats = pd.read_csv("nhl_team_stats_2024.csv", header=1)
    nhl_team_stats = nhl_team_stats.rename(columns={"Unnamed: 1": "Team"})

    # === Flyers Team Stats ===
    total_goals = flyers_advanced["G"].sum()
    total_assists = flyers_advanced["A"].sum()
    total_points = total_goals + total_assists
    avg_cf = flyers_advanced["CF"].mean()
    avg_ca = flyers_advanced["CA"].mean()
    avg_ozs = flyers_advanced["oZS%"].mean()
    avg_dzs = flyers_advanced["dZS%"].mean()

    # === League Averages ===
    league_avg_goals = nhl_team_stats["GF"].mean()
    league_avg_assists = league_avg_goals * 1.5  # rough estimate
    league_avg_points = league_avg_goals + league_avg_assists

    # === Stat Deltas (Flyers vs League) ===
    goals_delta = total_goals - league_avg_goals
    assists_delta = total_assists - league_avg_assists
    points_delta = total_points - league_avg_points

    # === TOP ROW ===
    st.subheader("Overall Production vs League Avg")
    col1, col2, col3 = st.columns(3)
    col1.metric("Goals", f"{total_goals}", f"{goals_delta:+.0f}")
    col2.metric("Assists", f"{total_assists}", f"{assists_delta:+.0f}")
    col3.metric("Points", f"{total_points}", f"{points_delta:+.0f}")

    # === MIDDLE ROW ===
    st.subheader("Average Possession Performance")
    fig_possession = px.bar(
        x=["Corsi For", "Corsi Against", "Corsi Differential"],
        y=[avg_cf, avg_ca, avg_cf - avg_ca],
        labels={"x": "Metric", "y": "Average Value"},
        text=[f"{avg_cf:.1f}", f"{avg_ca:.1f}", f"{(avg_cf - avg_ca):.1f}"],
        color_discrete_sequence=["#1f77b4", "#d62728", "#2ca02c"]
    )
    fig_possession.update_layout(height=400)
    st.plotly_chart(fig_possession, use_container_width=True)

    # === BOTTOM ROW ===
    st.subheader("Average Deployment (Zone Start %)")
    fig_zone = px.pie(
        names=["Offensive Zone Start", "Defensive Zone Start"],
        values=[avg_ozs, avg_dzs],
        color_discrete_sequence=["#FFA15A", "#19D3F3"],
        hole=0.45
    )
    fig_zone.update_traces(textinfo='label+percent')
    st.plotly_chart(fig_zone, use_container_width=True)

    st.caption(
        "This dashboard provides a full-scope view of the Flyers' offensive totals, possession quality, and deployment strategy, "
        "with context against league averages. GM-level insights come from seeing how team scoring stacks up and whether the Flyers "
        "generate more chances than they allow, and how coaching decisions impact starting position."
    )





# --------------------------- TAB 3 ---------------------------
with tabs[2]:
    st.header("NHL Team Stats Overview")

    # Load the CSV and rename the correct column
    nhl_team_stats = pd.read_csv("nhl_team_stats_2024.csv", header=1)
    nhl_team_stats = nhl_team_stats.rename(columns={"Unnamed: 1": "Team"})

    # Optional: display only relevant columns
    columns_to_show = ["Team", "GP", "W", "L", "PTS", "PTS%", "GF", "GA", "SV%", "S%", "PP%", "PK%"]
    columns_to_show = [col for col in columns_to_show if col in nhl_team_stats.columns]

    # Properly hide the index column
    st.dataframe(nhl_team_stats[columns_to_show].style.hide(axis="index"), use_container_width=True)

    st.caption(
        "This table presents core statistics for all NHL teams, allowing for league-wide benchmarking. "
        "GMs and analysts use this overview to identify trends in team performance, such as goal output, special teams strength, or shot suppression, "
        "to better assess their own team's standing and prioritize roster decisions."
    )



# --------------------------- TAB 3 ---------------------------
with tabs[3]:
    
    flyers_goalie = pd.read_csv("flyers_goalie_2024.csv", header=1)

    goalie_df = flyers_goalie[["Player", "GP", "W", "L", "GA", "SV%", "GAA"]].sort_values("GP", ascending=False)
    st.dataframe(goalie_df)

    # Optional: bar chart
    fig, ax = plt.subplots(figsize=(10, 5))
    goalie_df.set_index("Player")[["SV%", "GAA"]].plot(kind="bar", ax=ax)
    ax.set_title("Flyers Goalies - Save % and GAA")
    ax.set_ylabel("Value")
    st.pyplot(fig)

    st.subheader("Save Percentage vs Goals Against Average")

    goalie_data = flyers_goalie[["Player", "SV%", "GAA", "GP"]].dropna()
    goalie_data = goalie_data[goalie_data["GP"] >= 5]  # Filter for real workload

    fig = px.scatter(
        goalie_data,
        x="SV%",
        y="GAA",
        text="Player",
        hover_data=["GP"],
        color="Player",
        title="Flyers Goalies: Save % vs Goals Against Average (GAA)"
    )

    fig.update_traces(marker=dict(size=12), textposition="top center")
    fig.update_layout(
        xaxis_title="Save Percentage (SV%)",
        yaxis_title="Goals Against Average (GAA)",
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "This chart compares each Flyers goalie’s Save Percentage (SV%) to their Goals Against Average (GAA). "
        "Goalies in the bottome right combine high save rates with low goals allowed, indicating elite performance. "
        "Those in the top left may be struggling under pressure. This chart helps GMs and coaches evaluate goalie efficiency and reliability across different workloads."
    )


# --------------------------- TAB 4 ---------------------------
with tabs[4]:
    st.header("Compare Two Flyers Players")

    players = flyers_advanced['Player'].dropna().unique().tolist()
    p1 = st.selectbox("Select Player 1", players)
    p2 = st.selectbox("Select Player 2", players, index=1)

    # Pull G and A stats
    comp_df = flyers_advanced[flyers_advanced["Player"].isin([p1, p2])][["Player", "G", "A"]]
    comp_df = comp_df.rename(columns={"G": "Goals", "A": "Assists"})

    # Reshape: Player as x-axis, bars = stat categories
    comp_melted = comp_df.melt(id_vars="Player", var_name="Stat", value_name="Total")

    # Bar chart: x = Player, grouped by Stat
    fig = px.bar(
        comp_melted,
        x="Player",
        y="Total",
        color="Stat",
        barmode="group",
        text="Total",
        color_discrete_sequence=["#636EFA", "#EF553B"],
        title=f"{p1} vs {p2}: Offensive Output (Goals & Assists)"
    )

    fig.update_traces(textposition="outside", marker_line_width=1)
    fig.update_layout(
        yaxis_title="Total",
        xaxis_title="",
        height=500,
        legend=dict(title="", orientation="h", y=1.02, x=1, xanchor='right'),
        bargap=0.25
    )

    st.plotly_chart(fig)

    st.caption(
        f"This comparison shows how {p1} and {p2} contribute offensively in terms of goals and assists. "
        "With players on the x-axis and stat categories as grouped bars, it's easy to distinguish pure scorers from playmakers. "
        "This view supports lineup optimization and player usage decisions by surfacing where each player adds value on the scoresheet."
    )
    
    with tabs[5]:
        from rink_map import render_rink_tab
        render_rink_tab()
