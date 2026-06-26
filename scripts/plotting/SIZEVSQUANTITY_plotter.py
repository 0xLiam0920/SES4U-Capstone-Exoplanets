"""
Additional analyses for the SES4U capstone:
1) Star size vs quantity of exoplanets.
2) Same stellar mass, low-iron vs high-iron comparison.
"""

## ----------- imports ----------- ##
from sys import prefix

import pandas as pd
import plotly.graph_objects as go
from scipy import stats


#------------ File definitions (within root) -----------##
RAW_STAR_CSV = "star_analysis_data.csv"
IRON_COMPARISON_CSV = "same_mass_iron_comparison.csv"
STATS_OUTPUT = "regression_results.txt"
SECTION_START = "--- Additional Trend Results (interactive_plot_2.py) ---"
SECTION_END = "--- End Additional Trend Results ---"
URL = "https://docs.google.com/spreadsheets/d/1BkaT7wcZjGbm1lEvqtXyWPfayDh4kdFiEyKJEZQrlsM/gviz/tq?tqx=out:csv&gid=1962503937"
DEBUG = False ## off by default, enable if you want to troubleshoot better


# ----------- functions ----------- ##

## Purpose: load data from URL if available, otherwise local CSV like a sensible backup plan.
def load_data(url: str = None) -> pd.DataFrame:
	"""Load stellar dataset prepared by dataquery.py or from a provided URL."""
	try:
		if url:
			print(f"Using query output from URL: {url}")
			return pd.read_csv(url)
		else:
			print(f"URL not found; falling back to local output for now: {RAW_STAR_CSV}")
			return pd.read_csv(RAW_STAR_CSV)
	except FileNotFoundError as exc:
		if DEBUG:
			print("DEBUG: URL not found, using local CSV fallback.")
			print(f"ERROR CODE FOUND: {exc}")
		raise FileNotFoundError(
			"Missing star_analysis_data.csv. Run dataquery.py first to fetch NASA data."
		) from exc

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
	"""Validate that the dataframe is not empty and contains expected columns."""
	if df.empty:
		raise ValueError("ERROR: Query returned empty dataset. Check Google Sheets URL and permissions.")
	if len(df.columns) == 0:
		raise ValueError("ERROR: Query returned no columns. Verify Google Sheets URL is accessible.")
	return df
def clean_star_level_table(df: pd.DataFrame) -> pd.DataFrame:
	"""One row is made per host star with its planet count and stellar properties."""
	keep_cols = [
		"hostname",
		"pl_name",
		"st_mass",
		"st_rad",
		"st_met",
		"st_masslim",
		"st_radlim",
		"st_metlim",
	]
	df = df[[c for c in keep_cols if c in df.columns]].copy()

	for lim_col in ["st_masslim", "st_radlim", "st_metlim"]:
		if lim_col in df.columns:
			df = df[~df[lim_col].isin([1, -1])]

	df = df.dropna(subset=["hostname", "pl_name", "st_mass", "st_rad", "st_met"]).copy()

	# Note: Planet quantity comes from unique planet names per host.
	star_summary = (
		df.groupby("hostname", as_index=False)
		.agg(
			planet_count=("pl_name", "nunique"),
			st_mass=("st_mass", "median"),
			st_rad=("st_rad", "median"),
			st_met=("st_met", "median"),
		)
	)
	starSummary = star_summary  
	if DEBUG:
			print("DEBUG: Sample of cleaned star-level table:")
			print(starSummary.head())
	
	print(f"Prepared star-level table in memory ({len(starSummary)} stars)")
	return starSummary


def plot_star_size_vs_planet_count(star_summary: pd.DataFrame):
	"""Create plot and stats for stellar radius vs number of exoplanets."""
	# Plotly call chain ahead. It is long, but at least it's readable-ish.
	slope, intercept, r_value, p_value, _ = stats.linregress(
		star_summary["st_rad"], star_summary["planet_count"]
	)
	r_squared = r_value ** 2

	x_range = [star_summary["st_rad"].min(), star_summary["st_rad"].max()]
	y_fit = [slope * x + intercept for x in x_range]

	fig = go.Figure()
	fig.add_trace(
		go.Scatter(
			x=star_summary["st_rad"],
			y=star_summary["planet_count"],
			mode="markers",
			name="Host stars",
			marker=dict(
				size=8,
				color=star_summary["st_mass"],
				colorscale="Viridis",
				opacity=0.75,
				colorbar=dict(
					title="Stellar Mass (M_sun)",
					x=1.08,
					y=0.5,
					len=0.88,
					thickness=24,
				),
			),
			text=star_summary["hostname"],
			hovertemplate=(
				"<b>%{text}</b><br>"
				"Stellar Radius: %{x:.3f} R_sun<br>"
				"Exoplanets: %{y}<br>"
				"<extra></extra>"
			),
		)
	)
	fig.add_trace(
		go.Scatter(
			x=x_range,
			y=y_fit,
			mode="lines",
			name=f"Linear fit (R^2={r_squared:.4f}, p={p_value:.3e})",
			line=dict(color="crimson", dash="dash", width=2),
			hoverinfo="skip",
		)
	)
	fig.update_layout(
		title=dict(text="Star Size vs Quantity of Exoplanets", x=0.02, xanchor="left"),
		xaxis_title="Stellar Radius (R_sun)",
		yaxis_title="Number of Confirmed Exoplanets (per host star)",
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
	)
	fig.write_html("star_size_vs_exoplanet_count.html", include_plotlyjs="cdn")

	return {
		"slope": slope,
		"p_value": p_value,
		"r_squared": r_squared,
		"n_stars": len(star_summary),
	}


def build_mass_bin_comparison(star_summary: pd.DataFrame):
	"""Compare low-iron vs high-iron stars at similar masses."""
	# Build mass bins so each bin has a reasonable number of stars. Yes, this is a bit arbitrary, but it is a reasonable approach for proper analysis.
	n_bins = 8
	mass_binned = star_summary.copy()
	mass_binned["mass_bin"] = pd.qcut(
		mass_binned["st_mass"],
		q=n_bins,
		duplicates="drop",
	)

	rows = []
	for mass_bin, g in mass_binned.groupby("mass_bin"):
		if len(g) < 10:
			continue

		median_iron = g["st_met"].median()
		low_iron = g[g["st_met"] <= median_iron]["planet_count"]
		high_iron = g[g["st_met"] > median_iron]["planet_count"]

		if len(low_iron) < 3 or len(high_iron) < 3:
			continue

		rows.append(
			{
				"mass_bin": str(mass_bin),
				"stars_in_bin": len(g),
				"median_mass": g["st_mass"].median(),
				"iron_split": median_iron,
				"low_iron_mean_planets": low_iron.mean(),
				"high_iron_mean_planets": high_iron.mean(),
				"difference_high_minus_low": high_iron.mean() - low_iron.mean(),
			}
		)

	comparison = pd.DataFrame(rows)
	comparison.to_csv(IRON_COMPARISON_CSV, index=False)

	if comparison.empty:
		return comparison, None

	# Statistical tests on per-bin paired differences (because eyeballing bars is not science).
	diffs = comparison["difference_high_minus_low"]
	t_stat, t_p_value = stats.ttest_1samp(diffs, popmean=0.0)
	positive_bins = int((diffs > 0).sum())
	sign_test = stats.binomtest(positive_bins, n=len(diffs), p=0.5, alternative="greater")

	return comparison, {
		"paired_t_stat": t_stat,
		"paired_t_p_value": t_p_value,
		"positive_bins": positive_bins,
		"total_bins": len(diffs),
		"sign_test_p_value": sign_test.pvalue,
		"avg_difference": diffs.mean(),
	}


def plot_same_mass_iron_comparison(comparison: pd.DataFrame):
	"""Create bar chart for low/high iron groups at similar stellar masses."""
	fig = go.Figure()
	fig.add_trace(
		go.Bar(
			x=comparison["mass_bin"],
			y=comparison["low_iron_mean_planets"],
			name="Low iron (<= median [Fe/H])",
			marker_color="#4C78A8",
		)
	)
	fig.add_trace(
		go.Bar(
			x=comparison["mass_bin"],
			y=comparison["high_iron_mean_planets"],
			name="High iron (> median [Fe/H])",
			marker_color="#E45756",
		)
	) # this adds the second bar trace for high iron group with a different color to avoid general confusion
	fig.update_layout(
		barmode="group",
		title="Same Stellar-Mass Bins: Low-Iron vs High-Iron Exoplanet Counts",
		xaxis_title="Stellar Mass Bin (M_sun)",
		yaxis_title="Average Number of Exoplanets per Star",
		plot_bgcolor="#f8f9fa",
		paper_bgcolor="white",
	)
	fig.write_html("same_mass_iron_comparison.html", include_plotlyjs="cdn")


def write_stats_file(size_stats, iron_stats):
	"""Write or replace the extra results section in regression_results.txt."""
	lines = [
		SECTION_START,
		"",
		"1) Size of stars vs quantity of exoplanets",
		f"N stars = {size_stats['n_stars']}",
		f"Slope (planet_count vs st_rad) = {size_stats['slope']:.6f}",
		f"R^2 = {size_stats['r_squared']:.6f}",
		f"p-value = {size_stats['p_value']:.6e}",
		"",
		"2) Same stellar mass, low iron vs high iron",
	]

	if iron_stats is None:
		lines.append("Not enough bins after filtering to run comparison.")
	else:
		lines.extend(
			[
				f"Average (high - low) planets per star across bins = {iron_stats['avg_difference']:.6f}",
				f"Paired t-test t = {iron_stats['paired_t_stat']:.6f}",
				f"Paired t-test p-value = {iron_stats['paired_t_p_value']:.6e}",
				f"Positive bins (high iron > low iron) = {iron_stats['positive_bins']} / {iron_stats['total_bins']}",
				f"Sign test p-value = {iron_stats['sign_test_p_value']:.6e}",
			]
		)

	lines.append("")
	lines.append(SECTION_END)

	new_section = "\n".join(lines) + "\n"

	if not pd.io.common.file_exists(STATS_OUTPUT):
		with open(STATS_OUTPUT, "w", encoding="utf-8") as f:
			f.write(new_section)
		return

	with open(STATS_OUTPUT, "r", encoding="utf-8") as f:
		existing = f.read()

	start_idx = existing.find(SECTION_START)
	end_idx = existing.find(SECTION_END)

	if start_idx != -1 and end_idx != -1 and end_idx > start_idx: ## if the section exists, replace it. Simple as.
		end_idx = end_idx + len(SECTION_END)
		suffix = existing[end_idx:].lstrip()
		if prefix and suffix:
			rebuilt = (prefix + "\n\n" + new_section + "\n" + suffix).strip() + "\n"
		elif prefix:
			rebuilt = (prefix + "\n\n" + new_section).strip() + "\n"
		elif suffix:
			rebuilt = (new_section + "\n" + suffix).strip() + "\n"
		else:
			rebuilt = new_section
	else:
		rebuilt = (existing.rstrip() + "\n\n" + new_section).strip() + "\n"

	with open(STATS_OUTPUT, "w", encoding="utf-8") as f:
		f.write(rebuilt)

## --------- main function definition --------- ##
def main():
	raw_df = load_data()
	star_summary = clean_star_level_table(raw_df)

	size_stats = plot_star_size_vs_planet_count(star_summary)
	comparison, iron_stats = build_mass_bin_comparison(star_summary)

	if not comparison.empty:
		plot_same_mass_iron_comparison(comparison)
		print("Saved: same_mass_iron_comparison.html")
	else:
		print("Could not produce same-mass iron comparison plot (insufficient filtered data).")

	write_stats_file(size_stats, iron_stats)

	print("Saved: star_size_vs_exoplanet_count.html")
	print(f"Saved: {IRON_COMPARISON_CSV}")
	print(f"Updated: {STATS_OUTPUT}")


if __name__ == "__main__":
	main()
