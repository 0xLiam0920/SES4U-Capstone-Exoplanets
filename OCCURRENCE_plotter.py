"""
OCCURRENCE_plotter.py
---------------------
Replication of the Fischer (2005) and Buchhave (2012) results using the
NASA Exoplanet Archive pscomppars table.

Two analyses, both run on UNIQUE HOST STARS (not planets):
  (A) Binned occurrence rate:  fraction of hosts that harbour at least one
      gas giant (Mp > 50 ME), in 0.1-dex [Fe/H] bins, fit with Fischer's
      power-law  P = a * 10^(b * [Fe/H])
  (B) Two-sample Kolmogorov-Smirnov test on the metallicity distributions
      of giant-hosts vs small-planet-only hosts (Buchhave style).

Inputs expected (created by dataquery.py):
    - cleaned_data.csv  (pl_name, pl_massj, st_met, pl_massjlim, st_metlim)
      NOTE: must also contain 'hostname'. If your current cleaned_data.csv
      lacks hostname, re-pull with the query at the bottom of this file.
"""
import os
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

# ----------------- Config -----------------
CLEANED_CSV   = "cleaned_data.csv"
GIANT_MJ      = 50/317.8        # 50 Earth masses, in Jupiter masses (matches paper)
BIN_EDGES     = np.arange(-1.0, 0.85, 0.1)
MIN_BIN_COUNT = 10               # bins below this are shown but excluded from the fit

# ----------------- Load & classify hosts -----------------
df = pd.read_csv(CLEANED_CSV)
if "hostname" not in df.columns:
    raise SystemExit(
        "cleaned_data.csv has no 'hostname' column. Re-run dataquery.py with\n"
        "the updated query (see bottom of this file) that includes hostname."
    )

hosts = df.groupby("hostname").agg(
    max_massj = ("pl_massj", "max"),
    st_met    = ("st_met",   "first"),
    n_planets = ("pl_name",  "count"),
).reset_index()
hosts["has_giant"] = hosts["max_massj"] > GIANT_MJ

giants = hosts.loc[ hosts["has_giant"], "st_met"].values
smalls = hosts.loc[~hosts["has_giant"], "st_met"].values

print(f"Hosts total:          {len(hosts)}")
print(f"  Giant hosts:        {len(giants)}  (max planet > 50 ME)")
print(f"  Small-only hosts:   {len(smalls)}")

# ----------------- (B) Buchhave-style KS test -----------------
ks = stats.ks_2samp(giants, smalls)
print(f"\nKS test:  D = {ks.statistic:.4f},  p = {ks.pvalue:.4e}")
print(f"  Mean [Fe/H] giants:     {giants.mean():+.4f}")
print(f"  Mean [Fe/H] small-only: {smalls.mean():+.4f}")
print(f"  Difference in means:    {giants.mean()-smalls.mean():+.4f} dex")

# ----------------- (A) Fischer-style binned occurrence rate -----------------
hosts["bin"] = pd.cut(hosts["st_met"], bins=BIN_EDGES)
grp = hosts.groupby("bin", observed=True).agg(
    n_total=("has_giant","count"),
    n_giant=("has_giant","sum"),
).reset_index()
grp["frac"] = grp["n_giant"]/grp["n_total"]
ci_lo, ci_hi = proportion_confint(grp["n_giant"], grp["n_total"], alpha=0.05, method="wilson")
grp["ci_lo"], grp["ci_hi"] = ci_lo, ci_hi
grp["center"] = grp["bin"].apply(lambda iv: (iv.left + iv.right)/2)

qual = grp[(grp["n_total"] >= MIN_BIN_COUNT) & (grp["frac"] > 0)].copy()
slope, intercept, r, p_pwr, _ = stats.linregress(qual["center"], np.log10(qual["frac"]))
print(f"\nFischer power law:  P(giant) = a * 10^(b * [Fe/H])")
print(f"  a  = {10**intercept:.4f}")
print(f"  b  = {slope:.4f}     (Fischer 2005 reported b ~ 2.0)")
print(f"  R² = {r**2:.4f},  p = {p_pwr:.4e}")

grp.to_csv("occurrence_bins.csv", index=False)

# ============================ FIGURES ============================
# --- Figure 1: Occurrence rate ---
fig, ax = plt.subplots(figsize=(8, 5.5), dpi=130)
ax.errorbar(qual["center"], qual["frac"],
            yerr=[qual["frac"]-qual["ci_lo"], qual["ci_hi"]-qual["frac"]],
            fmt='o', color='#1a1a2e', markersize=8, capsize=4, lw=1.5,
            label='Binned occurrence (95% Wilson CI)')
for _, row in qual.iterrows():
    ax.annotate(f"n={row['n_total']}", (row["center"], row["frac"]),
                textcoords="offset points", xytext=(0, 8), ha='center',
                fontsize=7, color='#666')
xfit = np.linspace(qual["center"].min(), qual["center"].max(), 100)
yfit = 10**(intercept + slope*xfit)
ax.plot(xfit, yfit, '--', color='crimson', lw=2,
        label=f"Power law:  P = {10**intercept:.3f} × 10$^{{{slope:.3f}[Fe/H]}}$\n"
              f"  R² = {r**2:.3f},  p = {p_pwr:.2e}")
ax.set_xlabel('Host Star Metallicity  [Fe/H]  (dex)', fontsize=11)
ax.set_ylabel(r'Fraction of Hosts with a Gas Giant ($M_p$ > 50 $M_\oplus$)', fontsize=11)
ax.set_title('Gas Giant Occurrence Rate vs Stellar Metallicity', fontsize=13)
ax.set_ylim(0, 1.05); ax.grid(alpha=0.3); ax.legend(loc='lower right', fontsize=10)
plt.tight_layout()
plt.savefig('fig_occurrence_rate.png', dpi=150, bbox_inches='tight')
plt.close()

# --- Figure 2: KS test (hist + CDF) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=130)
edges = np.arange(-1.0, 0.85, 0.075)
ax1.hist(smalls, bins=edges, alpha=0.55, color='#4a90d9', density=True,
         label=f'Small-only hosts (n={len(smalls)})')
ax1.hist(giants, bins=edges, alpha=0.55, color='#d9534f', density=True,
         label=f'Giant hosts (n={len(giants)})')
ax1.axvline(smalls.mean(), color='#1a4f8a', ls='--', lw=1.5,
            label=f'small-only mean = {smalls.mean():+.3f}')
ax1.axvline(giants.mean(), color='#8b0000', ls='--', lw=1.5,
            label=f'giant mean = {giants.mean():+.3f}')
ax1.set_xlabel('Host Star Metallicity  [Fe/H]  (dex)', fontsize=11)
ax1.set_ylabel('Probability Density', fontsize=11)
ax1.set_title('Metallicity Distributions: Giant vs Small-only Hosts', fontsize=12)
ax1.legend(loc='upper left', fontsize=9); ax1.grid(alpha=0.3)

xs = np.sort(np.concatenate([giants, smalls]))
def ecdf(a, x): return np.searchsorted(np.sort(a), x, side='right')/len(a)
ax2.plot(xs, ecdf(smalls, xs), color='#4a90d9', lw=2.2, label='Small-only hosts')
ax2.plot(xs, ecdf(giants, xs), color='#d9534f', lw=2.2, label='Giant hosts')
diff = np.abs(ecdf(smalls, xs) - ecdf(giants, xs))
imax = np.argmax(diff)
ax2.vlines(xs[imax], ecdf(giants, xs)[imax], ecdf(smalls, xs)[imax],
           color='black', lw=1.5)
ax2.annotate(f'D = {ks.statistic:.3f}',
             (xs[imax], (ecdf(smalls, xs)[imax] + ecdf(giants, xs)[imax])/2),
             textcoords="offset points", xytext=(10, 0),
             fontsize=11, fontweight='bold')
ax2.set_xlabel('Host Star Metallicity  [Fe/H]  (dex)', fontsize=11)
ax2.set_ylabel('Empirical CDF', fontsize=11)
ax2.set_title(f'KS Test:  D = {ks.statistic:.4f},  p = {ks.pvalue:.2e}', fontsize=12)
ax2.legend(loc='lower right', fontsize=10); ax2.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('fig_buchhave_ks.png', dpi=150, bbox_inches='tight')
plt.close()

print("\nSaved: fig_occurrence_rate.png, fig_buchhave_ks.png, occurrence_bins.csv")

# ----------------- UPDATED dataquery.py SNIPPET -----------------
UPDATED_QUERY = """
-- Add 'hostname' to your existing build_mass_metallicity_dataset() query:
select hostname, pl_name, pl_massj, st_met, pl_massjlim, st_metlim
from pscomppars
where pl_massj is not null and st_met is not null
  and (pl_massjlim is null or pl_massjlim not in (-1,1))
  and (st_metlim  is null or st_metlim  not in (-1,1))
"""
