# flyers_analytics_app.py (Updated Tab 1 with Plotly and Detailed Captions)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

@st.cache_data
def load_data():
    flyers_standard = pd.read_csv("flyers_standard_2024.csv")
    flyers_advanced = pd.read_csv("flyers_advanced_2024.csv")
    flyers_goalie = pd.read_csv("flyers_goalie_2024.csv")
    flyers_misc = pd.read_csv("flyers_misc_2024.csv")
    nhl_team_stats = pd.read_csv("nhl_team_stats_2024.csv")
    nhl_advanced = pd.read_csv("nhl_advanced_2024.csv")
    return flyers_standard, flyers_advanced, flyers_goalie, flyers_misc, nhl_team_stats, nhl_advanced

flyers_standard, flyers_advanced, flyers_goalie, flyers_misc, nhl_team_stats, nhl_advanced = load_data()

flyers_advanced = flyers_advanced.iloc[:, :10]
flyers_advanced.columns = ["Rk", "Player", "Age", "Pos", "GP", "CF", "FF", "PDO", "oZS%", "dZS%"]
flyers_advanced[["GP", "CF", "FF", "PDO", "oZS%", "dZS%"]] = flyers_advanced[["GP", "CF", "FF", "PDO", "oZS%", "dZS%"]].apply(pd.to_numeric, errors="coerce")
flyers_advanced = flyers_advanced[flyers_advanced['GP'] >= 10]

nhl_advanced = nhl_advanced.iloc[:, :5]
nhl_advanced.columns = ["Team", "GP", "CF%", "xGF%", "oZone%"]
nhl_advanced[["CF%", "xGF%", "oZone%"]] = nhl_advanced[["CF%", "xGF%", "oZone%"]].apply(pd.to_numeric, errors="coerce")

st.title("Philadelphia Flyers 2024 Advanced Analytics Dashboard")
st.markdown("### All charts below reflect skaters with **10+ games played**.")
tabs = st.tabs(["Flyers Player Visuals", "Team vs League", "Goalie Stats", "Misc Stats", "Player Compare"])

# Tab 1: Flyers Player Visuals
with tabs[0]:
    st.header("Flyers Skater Analytics (Min 10 GP)")

    # CF/60 vs PDO
    st.subheader("CF/60 vs PDO")
    flyers_advanced["CF60"] = flyers_advanced["CF"] / flyers_advanced["GP"] * 60
    fig1 = px.scatter(
        flyers_advanced,
        x="CF60", y="PDO", text="Player",
        hover_data=["GP"], color="Player",
        labels={"CF60": "Corsi For per 60", "PDO": "PDO"},
        title="Flyers Player Efficiency: CF/60 vs. PDO (Min 10 GP)"
    )
    fig1.add_shape(type="line", x0=flyers_advanced["CF60"].min(), x1=flyers_advanced["CF60"].max(), y0=100, y1=100,
                  line=dict(color="red", dash="dash"))
    fig1.update_traces(marker=dict(size=12), textposition="top center")
    st.plotly_chart(fig1, use_container_width=True)
    st.caption("This chart visualizes offensive shot generation versus puck luck. Corsi For per 60 (CF/60) estimates how many shot attempts a player’s team generates while they are on the ice per 60 minutes of 5v5 play. PDO is the sum of on-ice shooting percentage and save percentage, used as a luck indicator. Values above 100 imply good fortune or hot streaks, while below 100 may suggest bad puck luck or poor finishing/goaltending.")

    # Top oZS%
    st.subheader("Top oZS% (Offensive Zone Start%)")
    top_ozs = flyers_advanced.sort_values("oZS%", ascending=False).head(10)
    fig2 = px.bar(
        top_ozs,
        x="oZS%", y="Player", orientation="h",
        color="oZS%", labels={"oZS%": "Offensive Zone Start %"},
        title="Top 10 Flyers by Offensive Zone Start %"
    )
    fig2.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Offensive Zone Start % (oZS%) reflects deployment strategy. Players with higher oZS% are typically used in offensive situations and may be sheltered from defensive responsibilities. This chart shows which Flyers are most frequently used in advantageous zone situations.")

    # PDO Distribution
    st.subheader("PDO Distribution")
    fig3 = px.histogram(
        flyers_advanced, x="PDO", nbins=20, marginal="rug", opacity=0.7,
        labels={"PDO": "PDO Value"},
        title="PDO Distribution (Luck Index)"
    )
    fig3.add_vline(x=100, line_dash="dash", line_color="red")
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("This histogram shows the spread of PDO values among Flyers skaters. A tightly grouped distribution around 100 suggests consistent team performance, while a wide spread suggests varying degrees of puck luck. Outliers on the high or low end may regress to the mean.")

    # CF% and FF% contribution
    st.subheader("Player Share of Team CF% and FF%")
    total_cf = flyers_advanced["CF"].sum()
    total_ff = flyers_advanced["FF"].sum()
    flyers_advanced["CF_%"] = flyers_advanced["CF"] / total_cf * 100
    flyers_advanced["FF_%"] = flyers_advanced["FF"] / total_ff * 100

    fig4 = px.bar(
        flyers_advanced.sort_values("CF_%", ascending=False),
        x="CF_%", y="Player", orientation="h",
        title="Corsi For % Contribution by Player",
        labels={"CF_%": "% of Team Corsi For"}
    )
    fig4.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig4, use_container_width=True)

    fig5 = px.bar(
        flyers_advanced.sort_values("FF_%", ascending=False),
        x="FF_%", y="Player", orientation="h",
        title="Fenwick For % Contribution by Player",
        labels={"FF_%": "% of Team Fenwick For"}, color_discrete_sequence=["green"]
    )
    fig5.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("These bar charts show which players are driving offensive shot attempts. Corsi includes all attempts, while Fenwick excludes blocked shots. A high contribution suggests that the player is central to driving play while on the ice.")

    # oZS% vs PDO
    st.subheader("Deployment vs Luck: oZS% vs PDO")
    fig6 = px.scatter(
        flyers_advanced, x="oZS%", y="PDO", text="Player", color="Player",
        title="Flyers: Offensive Zone Start % vs PDO",
        labels={"oZS%": "Offensive Zone Start %", "PDO": "PDO"}
    )
    fig6.add_shape(type="line", x0=flyers_advanced["oZS%"].min(), x1=flyers_advanced["oZS%"].max(), y0=100, y1=100,
                  line=dict(color="red", dash="dash"))
    fig6.update_traces(marker=dict(size=12), textposition="top center")
    st.plotly_chart(fig6, use_container_width=True)
    st.caption("This scatterplot compares player deployment (offensive zone usage) with their PDO. Players in the top-right quadrant are both heavily used in the offensive zone and experiencing elevated puck luck. Those in the bottom-left may be playing in tougher situations and seeing poor results.")

# Tab 2: Team vs League
with tabs[1]:
    st.header("Flyers vs League (2024)")
    st.subheader("Flyers vs League CF% and xGF%")
    df_melted = pd.melt(nhl_advanced, id_vars=["Team"], value_vars=["CF%", "xGF%"], var_name="Metric", value_name="Value")
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df_melted, x="Team", y="Value", hue="Metric", ax=ax4)
    ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45, ha="right")
    st.pyplot(fig4)

    st.subheader("Offensive Zone Time % Comparison")
    fig5, ax5 = plt.subplots(figsize=(10, 6))
    sns.barplot(data=nhl_advanced.sort_values("oZone%", ascending=False), x="oZone%", y="Team", ax=ax5)
    ax5.set_title("League oZone% Ranking")
    st.pyplot(fig5)

# Tab 3: Goalie Stats
with tabs[2]:
    st.header("Goalie Overview")
    st.dataframe(flyers_goalie)

# Tab 4: Misc Stats
with tabs[3]:
    st.header("Miscellaneous Flyers Stats")
    st.dataframe(flyers_misc)
    st.subheader("Goals vs Assists")
    if {'G', 'A'}.issubset(flyers_misc.columns):
        df_long = flyers_misc.melt(id_vars=["Player"], value_vars=["G", "A"], var_name="Type", value_name="Total")
        fig6, ax6 = plt.subplots(figsize=(10, 5))
        sns.barplot(data=df_long, x="Player", y="Total", hue="Type", ax=ax6)
        ax6.set_xticklabels(ax6.get_xticklabels(), rotation=45, ha="right")
        ax6.set_title("Goals vs Assists")
        st.pyplot(fig6)

# Tab 5: Player Comparison
with tabs[4]:
    st.header("Compare Two Flyers Players")
    players = flyers_advanced['Player'].dropna().unique().tolist()
    p1 = st.selectbox("Select Player 1", players)
    p2 = st.selectbox("Select Player 2", players, index=1)
    comp = flyers_advanced[flyers_advanced['Player'].isin([p1, p2])][["Player", "CF", "FF", "PDO", "oZS%", "dZS%"]].set_index("Player")
    st.bar_chart(comp.T)