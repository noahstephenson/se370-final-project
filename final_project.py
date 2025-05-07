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

tabs = st.tabs(["Flyers Player Visuals", "Team Summary", "League Stats", "Goalie Stats", "Player Compare"])

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
# --------------------------- TAB 2 ---------------------------
with tabs[2]:
    st.header("NHL Team Stats Overview")
    st.dataframe(nhl_team_stats)
    st.caption("This table shows full NHL team statistics for comparison. GMs use league-wide benchmarks to spot weaknesses or strengths relative to the competition.")

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

    # Filter for selected players
    comp_df = flyers_advanced[flyers_advanced["Player"].isin([p1, p2])][["Player", "G", "A"]].set_index("Player")

    # Transpose for plotting
    comp_df_plot = comp_df.T.reset_index().rename(columns={"index": "Stat"})

    # Plotly bar chart
    fig = px.bar(comp_df_plot, x="Stat", y=[p1, p2], barmode="group",
                 labels={"value": "Count", "Stat": "Stat Type"},
                 title=f"{p1} vs {p2}: Goals and Assists Comparison")
    fig.update_layout(yaxis_title="Total", xaxis_title="Statistic", height=500)
    st.plotly_chart(fig)

    st.caption(
        "This bar chart compares total goals and assists between two selected Flyers players. "
        "General Managers use this simple scoring breakdown to evaluate who’s finishing plays versus setting them up. "
        "While raw production doesn’t tell the full story, it’s a useful snapshot of offensive contribution."
    )
