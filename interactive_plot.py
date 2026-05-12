import pandas as pd
import os
from scipy import stats
import plotly.graph_objects as go

# ── Data loading (mirrors Plotter.py logic) ──────────────────────────────────
file_id = '1vEqyft83eOYNNn9VWypSLnIcPTDCgoFZkXiurXBEqfc'
url = f'https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&sheet=Sheet1'
local_csv = 'data.csv'
cleaned_csv = 'cleaned_data.csv'

print("Loading data...")
df = None

# Prefer the cleaned NASA dataset if available, then fall back to the Google Sheet CSV
if os.path.exists(cleaned_csv):
    print(f"Using cleaned dataset: {cleaned_csv}")
    df = pd.read_csv(cleaned_csv)
elif os.path.exists(local_csv):
    print(f"Using local file: {local_csv}")
    df = pd.read_csv(local_csv)
else:
    print(f"Fetching data from Google Sheets...")
    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"Error loading data: {e}")
        print(f"Please download the sheet as '{local_csv}' and place it in the root folder.")
        exit(1)

# ── Filtering (gas giants > 50 Earth masses ≈ 0.157 Jupiter masses) ──────────
mass_col  = 'pl_massj'
metal_col = 'st_met'
name_col  = 'pl_name'

df_filtered = df[df[mass_col] > 0.157].dropna(subset=[mass_col, metal_col]).copy()
print(f"Plotting {len(df_filtered)} gas giants")

# ── Linear regression ─────────────────────────────────────────────────────────
slope, intercept, r_value, p_value, std_err = stats.linregress(
    df_filtered[metal_col], df_filtered[mass_col]
)
r_squared = r_value ** 2

x_range = [df_filtered[metal_col].min(), df_filtered[metal_col].max()]
y_reg   = [slope * x + intercept for x in x_range]

# ── Build hover text ──────────────────────────────────────────────────────────
def make_hover(row):
    name = row.get(name_col, "Unknown") if name_col in row.index else "Unknown"
    mass = row[mass_col]
    met  = row[metal_col]
    return (
        f"<b>{name}</b><br>"
        f"Mass: {mass:.3f} M<sub>Jup</sub><br>"
        f"Metallicity [Fe/H]: {met:+.3f}"
    )

hover_texts = df_filtered.apply(make_hover, axis=1).tolist()

# Custom data attached to each point (used by the JS click panel)
custom_data = list(zip(
    df_filtered.get(name_col, ["Unknown"] * len(df_filtered)),
    df_filtered[mass_col].round(4),
    df_filtered[metal_col].round(4),
))

# ----------------- Creating the plotly figure with scatter points and regression line ----------------- #
fig = go.Figure()

# Scatter points
fig.add_trace(go.Scatter(
    x=df_filtered[metal_col],
    y=df_filtered[mass_col],
    mode='markers',
    name='Gas Giants',
    marker=dict(
        color=df_filtered[mass_col],
        colorscale='Viridis',
        size=7,
        opacity=0.8,
        colorbar=dict(title='Mass (M<sub>Jup</sub>)'),
        line=dict(width=0.5, color='white'),
    ),
    text=hover_texts,
    hovertemplate='%{text}<extra></extra>',
    customdata=custom_data,
))

# Regression line
fig.add_trace(go.Scatter(
    x=x_range,
    y=y_reg,
    mode='lines',
    name=f'Linear Fit  R²={r_squared:.4f}  p={p_value:.4f}',
    line=dict(color='crimson', width=2, dash='dash'),
    hoverinfo='skip',
))

fig.update_layout(
    title=dict(
        text='Host Star Metallicity vs Planet Mass (Gas Giants)',
        font=dict(size=20),
    ),
    xaxis=dict(title='Host Star Metallicity [Fe/H]', zeroline=True, zerolinewidth=1),
    yaxis=dict(title='Planet Mass (M<sub>Jup</sub>)', zeroline=True, zerolinewidth=1),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    plot_bgcolor='#f8f9fa',
    paper_bgcolor='white',
    hoverlabel=dict(bgcolor='white', font_size=13),
)

# ----------------- Export to HTML with injected click-panel JavaScript ----------------- #
html_path = 'interactive_plot.html'

# Generate base Plotly HTML
raw_html = fig.to_html(full_html=True, include_plotlyjs='cdn')

# JavaScript that listens for click events and shows a floating detail panel
click_js = """
<style>
  #planet-panel { 
    display: none;
    position: fixed;
    top: 60px;
    right: 24px;
    width: 280px;
    background: #ffffff; 
    border: 1px solid #d0d7de;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    font-family: 'Segoe UI', sans-serif;
    z-index: 9999;
    overflow: hidden;
  }
  #planet-panel-header {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    color: white;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  #planet-panel-header h3 { margin: 0; font-size: 15px; }
  #panel-close {
    cursor: pointer;
    font-size: 18px;
    line-height: 1;
    opacity: 0.8;
    background: none;
    border: none;
    color: white;
    padding: 0 2px;
  }
  #panel-close:hover { opacity: 1; }
  #planet-panel-body {
    padding: 14px 16px;
  }
  .panel-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #f0f0f0;
    font-size: 13px;
  }
  .panel-row:last-child { border-bottom: none; }
  .panel-label { color: #666; }
  .panel-value { font-weight: 600; color: #1a1a2e; }
  #planet-panel-hint {
    font-size: 11px;
    color: #aaa;
    text-align: center;
    padding-bottom: 8px;
  }
</style>

<div id="planet-panel">
  <div id="planet-panel-header">
    <h3 id="panel-name">Planet Name</h3>
    <button id="panel-close" title="Close">&#x2715;</button>
  </div>
  <div id="planet-panel-body">
    <div class="panel-row">
      <span class="panel-label">Mass</span>
      <span class="panel-value" id="panel-mass">—</span>
    </div>
    <div class="panel-row">
      <span class="panel-label">Host Star Metallicity [Fe/H]</span>
      <span class="panel-value" id="panel-met">—</span>
    </div>
    <div class="panel-row">
      <span class="panel-label">Data Source</span>
      <span class="panel-value">NASA Exoplanet Archive</span>
    </div>
  </div>
  <div id="planet-panel-hint">Click another point to update</div>
</div>

<script>
(function () {
  document.getElementById('panel-close').addEventListener('click', function () {
    document.getElementById('planet-panel').style.display = 'none';
  });

  // Wait for Plotly to finish rendering before attaching the listener
  var attempt = 0;
  var interval = setInterval(function () {
    attempt++;
    var gd = document.querySelector('.js-plotly-plot');
    if (!gd && attempt < 50) return;
    clearInterval(interval);

    gd.on('plotly_click', function (data) {
      var pt = data.points[0];
      if (!pt || !pt.customdata) return;

      var name = pt.customdata[0];
      var mass = pt.customdata[1];
      var met  = pt.customdata[2];

      document.getElementById('panel-name').textContent = name;
      document.getElementById('panel-mass').textContent = mass + ' M\\u2059';
      document.getElementById('panel-met').textContent  = (met >= 0 ? '+' : '') + met;
      document.getElementById('planet-panel').style.display = 'block';
    });
  }, 100);
})();
</script>
"""

# Inject the panel just before </body>
final_html = raw_html.replace('</body>', click_js + '\n</body>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(final_html)

print(f"Interactive plot saved to: {html_path}")
print(f"  R² = {r_squared:.4f}   p = {p_value:.6f}")
print("Please open the HTML file in a web browser that supports JavaScript to view the interactive plot and detailing.")

