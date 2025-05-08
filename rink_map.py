def render_rink_tab():  
    import streamlit as st
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    import pandas as pd

    st.header("This map shows the top goal scorer for each position on the Philadelphia Flyers")

    # Load your image
    rink_img = mpimg.imread("ice hockey rink.jpg")
    shape = rink_img.shape
    height, width = shape[:2]

    # Load player data
    df = pd.read_csv("flyers_standard_2024.csv", skiprows=1)
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    df = df[['Player', 'Pos', 'G']].dropna()
    df['G'] = pd.to_numeric(df['G'], errors='coerce')
    df = df.dropna(subset=['G'])
    df = df[~df['Pos'].str.contains("G")]

    # Select top per position
    forwards = df[df['Pos'].isin(['LW', 'C', 'RW'])].sort_values("G", ascending=False).drop_duplicates(subset=["Pos"])
    defensemen = df[df['Pos'].str.startswith("D")].sort_values("G", ascending=False).head(2).copy()
    defensemen['Pos'] = ['LD', 'RD']
    top_by_position = pd.concat([forwards, defensemen])

    # Coordinates in pixel space
    position_coords = {
        'LW': (int(width * 0.50), int(height * 0.35)),
        'C':  (int(width * 0.50), int(height * 0.50)),
        'RW': (int(width * 0.50), int(height * 0.65)),
        'LD': (int(width * 0.60), int(height * 0.35)),
        'RD': (int(width * 0.60), int(height * 0.65)),
    }

    # Create clean white canvas
    fig, ax = plt.subplots(figsize=(width / 60, height / 60), dpi=100)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.imshow(rink_img)
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Plot players
    for _, row in top_by_position.iterrows():
        pos = row['Pos']
        if pos in position_coords:
            x, y = position_coords[pos]
            ax.scatter(x, y, s=350, color='orange', edgecolors='black', zorder=3)
            label = f"{row['Player']}\nGoals: {int(row['G'])}"
            ax.text(x, y - 20, label, color='black', fontsize=8, ha='center', va='bottom', weight='bold', zorder=4)

    # Display
    st.pyplot(fig)
