import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.colors as mcolors

# Load and clean data
df = pd.read_csv("flyers_standard_2024.csv")
players = df[['Unnamed: 1', 'Unnamed: 3', 'Scoring']].copy()
players.columns = ['Player', 'Pos', 'G']
players = players[players['G'] != 'G']
players.dropna(subset=['Player', 'Pos', 'G'], inplace=True)
players = players[players['Player'].str.strip() != '']
players['G'] = pd.to_numeric(players['G'], errors='coerce').fillna(0)

# Assign D1/D2 positions
def assign_defense(index, pos):
    if pos == 'D':
        return 'D1' if index % 2 == 0 else 'D2'
    return pos
players['PosMapped'] = [assign_defense(i, p) for i, p in enumerate(players['Pos'])]

# Position coordinates (goalie on right)
position_coords = {
    'C': (60, 21), 'LW': (50, 30), 'RW': (50, 12),
    'D1': (75, 15), 'D2': (75, 27), 'G': (90, 21)
}

# Sidebar filters
st.sidebar.header("Filters")

# Dropdown to filter by position
available_positions = list(position_coords.keys())
selected_positions = st.sidebar.multiselect("Select Positions", available_positions, default=available_positions)

# Slider for goal range
min_goals = int(players['G'].min())
max_goals = int(players['G'].max())
goal_range = st.sidebar.slider("Select Goal Range", min_value=min_goals, max_value=max_goals, value=(min_goals, max_goals))

# Filter data
filtered = players[
    (players['PosMapped'].isin(selected_positions)) &
    (players['G'] >= goal_range[0]) &
    (players['G'] <= goal_range[1])
]

# Normalize colors
norm = mcolors.Normalize(vmin=players['G'].min(), vmax=players['G'].max())
colors = px.colors.sequential.Hot
position_counts = filtered['PosMapped'].value_counts().to_dict()
offsets = {k: 0 for k in position_coords}
offset_step = 3

# Build Plotly data
x_vals, y_vals, labels, hovers, marker_colors = [], [], [], [], []
for _, row in filtered.iterrows():
    pos = row['PosMapped']
    if pos in position_coords:
        base_x, base_y = position_coords[pos]
        offset = offsets[pos]
        y_offset = base_y + (offset - (position_counts[pos] - 1) / 2) * offset_step
        x_vals.append(base_x)
        y_vals.append(y_offset)
        labels.append(f"{row['Player']} ({int(row['G'])})")
        hovers.append(f"{row['Player']}<br>Goals: {int(row['G'])}<br>Position: {row['Pos']}")
        color_index = int(norm(row['G']) * (len(colors) - 1))
        marker_colors.append(colors[color_index])
        offsets[pos] += 1

# Create plot
fig = go.Figure(go.Scatter(
    x=x_vals,
    y=y_vals,
    mode='markers',
    marker=dict(size=14, color=marker_colors),
    hovertext=hovers,
    hoverinfo="text"
))


import base64

# Convert image to base64
with open("ice hockey rink.jpg", "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode()

# Update Plotly layout to include the image
fig.update_layout(
    title="Flyers Player Interactive Heatmap",
    xaxis=dict(range=[0, 100], showgrid=False, visible=False),
    yaxis=dict(range=[0, 42], showgrid=False, visible=False),
    images=[dict(
        source=f"data:image/jpg;base64,{encoded_image}",
        xref="x", yref="y",
        x=0, y=42,  # top-left corner of image
        sizex=100, sizey=42,
        sizing="stretch",
        opacity=1.0,
        layer="below"
    )],
    plot_bgcolor='white',
    width=1000,
    height=500
)

# Show chart
st.title("Interactive Flyers Player Heatmap")
st.plotly_chart(fig, use_container_width=False)