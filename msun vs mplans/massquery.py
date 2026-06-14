## ----------- imports ----------- ##
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go


## ----------- file definitions ----------- ##
HERE = os.path.dirname(os.path.abspath(__file__))
MP_CSV = os.path.join(HERE, "massplot.csv")
MP_HTML = os.path.join(HERE, "massplot.html")
DEBUG = False ## off by default, enable if you want to troubleshoot/see full output.

## ----------- column names from massplot.csv ----------- ##
COL_HOST   = "hostname"
COL_STMASS = "st_mass (unit: M☉)"
COL_PLMASS = "SUM of pl_bmasse (unit: M🜨)"


def load_data():
    if DEBUG:
        print(f"Loading data from {MP_CSV}...")
    df = pd.read_csv(MP_CSV)
    df = df.dropna(subset=[COL_STMASS, COL_PLMASS])
    if DEBUG:
        print(f"Data loaded, {len(df)} rows after dropping NaNs.")
    return df


def line_of_best_fit(x, y):
    ## calculate the line of best fit using numpy
    coeffs = np.polyfit(x, y, 1)
    return coeffs


def create_scatter_plot(df):
    x = df[COL_STMASS].values
    y = df[COL_PLMASS].values
    labels = df[COL_HOST].values

    ## line of best fit
    coeffs = line_of_best_fit(x, y)
    x_line = np.linspace(x.min(), x.max(), 300)
    y_line = np.polyval(coeffs, x_line)

    fig = go.Figure()

    ## scatter points
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker=dict(size=7, color="steelblue", opacity=0.8),
        text=labels,
        hovertemplate="<b>%{text}</b><br>Star mass: %{x:.3f} M☉<br>Planet mass sum: %{y:.2f} M🜨<extra></extra>",
        name="Planetary systems",
    ))

    ## line of best fit
    fig.add_trace(go.Scatter(
        x=x_line,
        y=y_line,
        mode="lines",
        line=dict(color="crimson", width=2, dash="dash"),
        name=f"Best fit  (slope={coeffs[0]:.2f})",
    ))

    fig.update_layout(
        title="Host Star Mass vs. Total Exoplanet Mass per System",
        xaxis_title="Host Star Mass (M☉)",
        yaxis_title="Sum of Exoplanet Masses (M🜨)",
        legend=dict(x=0.02, y=0.98),
        template="plotly_white",
    )

    fig.write_html(MP_HTML)
    print(f"Scatter plot saved to {MP_HTML}")


def main():
    df = load_data()
    create_scatter_plot(df)


if __name__ == "__main__":
    main()