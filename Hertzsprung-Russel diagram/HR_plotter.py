## ----------- imports ----------- ##
import os
import re
import pandas as pd
import plotly.graph_objects as go






## ----------- file definitions ----------- ##
HERE = os.path.dirname(os.path.abspath(__file__))
HR_CSV  = os.path.join(HERE, "HR_dataset.csv")
HR_HTML = os.path.join(HERE, "HR_plot.html")
STAR_CSV = os.path.join(os.path.dirname(HERE), "star_analysis_data.csv")


## ----------- helpers ----------- ##
def extract_hostname(pl_name: str) -> str:
	"""Strip the trailing planet letter (e.g. 'HD 18599 b' -> 'HD 18599')."""
	if not isinstance(pl_name, str):
		return pl_name
	return re.sub(r"\s+[A-Za-z]+$", "", pl_name).strip()


def load_hr_data(path: str = HR_CSV) -> pd.DataFrame:
	"""Load and clean the HR dataset down to one row per host star."""
	df = pd.read_csv(path)

	required = ["pl_name", "st_teff", "st_lum"]
	for col in required:
		if col not in df.columns:
			raise ValueError(f"HR_dataset.csv missing required column: {col}")

	df = df.dropna(subset=["st_teff", "st_lum", "pl_name"]).copy()
	df = df[(df["st_teff"] > 0)]

	df["hostname"] = df["pl_name"].apply(extract_hostname)

	agg = {
		"st_teff": "median",
		"st_lum": "median",
	}
	if "st_met" in df.columns:
		agg["st_met"] = "median"
	if "sy_pnum" in df.columns:
		agg["sy_pnum"] = "max"
	if "pl_bmasse" in df.columns:
		agg["pl_bmasse"] = "sum"  # total planet mass per star (Earth masses)

	stars = df.groupby("hostname", as_index=False).agg(agg)
	stars = stars.dropna(subset=["st_teff", "st_lum"])

	# ---- mass-ratio classification ----
	if "pl_bmasse" in stars.columns and os.path.exists(STAR_CSV):
		sdf = pd.read_csv(STAR_CSV)[["hostname", "st_mass"]].dropna(subset=["st_mass"])
		st_mass_med = sdf.groupby("hostname", as_index=False)["st_mass"].median()
		stars = stars.merge(st_mass_med, on="hostname", how="left")

	if "pl_bmasse" in stars.columns and "st_mass" in stars.columns:
		# Dimensionless ratio: total planet mass / star mass (both in Earth masses; 1 M_sun = 333 000 M_earth)
		stars["mass_ratio"] = stars["pl_bmasse"] / (stars["st_mass"] * 333000)
		valid = stars["mass_ratio"].notna() & (stars["mass_ratio"] > 0)
		threshold = stars.loc[valid, "mass_ratio"].quantile(0.90)
		stars["mass_class"] = "unknown"
		stars.loc[valid & (stars["mass_ratio"] >= threshold), "mass_class"] = "high"
		stars.loc[valid & (stars["mass_ratio"] < threshold),  "mass_class"] = "low"
	else:
		stars["mass_class"] = "unknown"

	return stars


## ----------- spectral-class shading ----------- ##
SPECTRAL_BANDS = [
	("O", 30000, 50000, "rgba(155, 176, 255, 0.10)"),
	("B", 10000, 30000, "rgba(170, 191, 255, 0.10)"),
	("A", 7500, 10000, "rgba(202, 215, 255, 0.10)"),
	("F", 6000, 7500, "rgba(248, 247, 255, 0.10)"),
	("G", 5200, 6000, "rgba(255, 244, 234, 0.18)"),
	("K", 3700, 5200, "rgba(255, 210, 161, 0.18)"),
	("M", 2400, 3700, "rgba(255, 169, 138, 0.20)"),
]


def add_spectral_bands(fig: go.Figure, y_min: float, y_max: float, t_min: float, t_max: float):
	"""Shade spectral-class regions across the plot background."""
	for label, lo, hi, color in SPECTRAL_BANDS:
		lo_c = max(lo, t_min)
		hi_c = min(hi, t_max)
		if lo_c >= hi_c:
			continue
		fig.add_shape(
			type="rect",
			xref="x", yref="paper",
			x0=lo_c, x1=hi_c, y0=0, y1=1,
			fillcolor=color, line=dict(width=0),
			layer="below",
		)
		fig.add_annotation(
			x=(lo_c + hi_c) / 2, y=1.0, yref="paper",
			text=f"<b>{label}</b>",
			showarrow=False, yshift=10,
			font=dict(size=11, color="#666"),
		)


## ----------- plot ----------- ##
def plot_hr_diagram(stars: pd.DataFrame):
	"""Create the HR diagram and write it to HR_plot.html."""
	# Groups: (mass_class, marker symbol, legend label)
	_GROUPS = [
		("high",    "diamond",     "High planet/star mass ratio (top 10%)"),
		("low",     "circle",      "Low planet/star mass ratio (bottom 90%)"),
		("unknown", "circle-open", "Mass ratio unavailable"),
	]

	fig = go.Figure()
	first_trace = True
	for cls, symbol, label in _GROUPS:
		if "mass_class" in stars.columns:
			sub = stars[stars["mass_class"] == cls]
		elif cls == "unknown":
			sub = stars  # fallback: no classification data
		else:
			continue
		if sub.empty:
			continue

		pc = sub["sy_pnum"] if "sy_pnum" in sub.columns else pd.Series([1] * len(sub), index=sub.index)
		sizes = (6 + 2.2 * pc.clip(lower=1, upper=10)).values

		met_str = (
			sub["st_met"].apply(lambda v: f"{v:+.3f}" if pd.notna(v) else "n/a")
			if "st_met" in sub.columns
			else pd.Series(["n/a"] * len(sub), index=sub.index)
		)
		ratio_str = (
			sub["mass_ratio"].apply(lambda v: f"{v:.3e}" if pd.notna(v) else "n/a")
			if "mass_ratio" in sub.columns
			else pd.Series(["n/a"] * len(sub), index=sub.index)
		)
		custom = list(zip(pc.fillna(1).astype(int), met_str, ratio_str))

		fig.add_trace( 
			go.Scatter(
				x=sub["st_teff"],
				y=sub["st_lum"],
				mode="markers",
				name=label,
				marker=dict(
					symbol=symbol,
					size=sizes,
					color=sub["st_teff"],
					colorscale="RdBu",
					reversescale=False,
					cmin=2500,
					cmax=10000,
					opacity=0.85,
					line=dict(width=0.4, color="white"),
					showscale=first_trace,
					colorbar=dict(title="T_eff (K)", x=1.02, y=0.5, len=0.88, thickness=22),
				),
				text=sub["hostname"],
				customdata=custom,
				hovertemplate=(
					"<b>%{text}</b><br>"
					"T_eff: %{x:.0f} K<br>"
					"log(L/L_sun): %{y:.3f}<br>"
					"Planets in system: %{customdata[0]}<br>"
					"[Fe/H]: %{customdata[1]}<br>"
					"Planet/star mass ratio: %{customdata[2]}"
					"<extra></extra>"
				),
			)
		)
		first_trace = False

	# Sun reference (T=5772 K, log L = 0)
	fig.add_trace(
		go.Scatter(
			x=[5772], y=[0],
			mode="markers+text",
			name="Sun",
			marker=dict(size=12, color="gold", line=dict(width=1.2, color="#b8860b"), symbol="star"),
			text=["Sun"],
			textposition="top center",
			textfont=dict(size=11, color="#7a6100"),
			hovertemplate="<b>Sun</b><br>T_eff: 5772 K<br>log(L/L_sun): 0<extra></extra>",
		)
	)

	t_lo = max(2000, float(stars["st_teff"].min()) - 200)
	t_hi = min(50000, float(stars["st_teff"].max()) + 200)
	y_lo = float(stars["st_lum"].min()) - 0.4
	y_hi = float(stars["st_lum"].max()) + 0.4

	add_spectral_bands(fig, y_lo, y_hi, t_lo, t_hi)

	fig.update_layout( ## this is absolute gold, everything fits perfect suprisingly.
		title=dict(text="Hertzsprung-Russell Diagram of Exoplanet Host Stars", x=0.02, xanchor="left"),
		xaxis=dict(
			title="Stellar Effective Temperature T_eff (K)",
			autorange="reversed",
			range=[t_hi, t_lo],
			zeroline=False,
		),
		yaxis=dict(
			title="Stellar Luminosity  log(L / L_sun)",
			zeroline=True,
			zerolinewidth=1,
			zerolinecolor="#cccccc",
		),
		legend=dict(
			orientation="h",
			yanchor="bottom",
			y=1.02,
			xanchor="left",
			x=0.02,
		),
		margin=dict(t=90, r=170),
		plot_bgcolor="#f8f9fa",
		paper_bgcolor="white",
		hoverlabel=dict(bgcolor="white", font_size=13),
	)

	fig.write_html(HR_HTML, include_plotlyjs="cdn")
	print(f"Saved: {HR_HTML} ({len(stars)} host stars)")


## ----------- main ----------- ##
def main():
	stars = load_hr_data()
	plot_hr_diagram(stars)


if __name__ == "__main__":
	main()
