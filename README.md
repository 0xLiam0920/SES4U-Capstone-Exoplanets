# SES4U Capstone: Stellar Metallicity and Gas Giant Occurrence

> A replication and extension of Fischer & Valenti (2005) and Buchhave et al. (2012) using live data from the NASA Exoplanet Archive.  
> *Submitted to the Journal of Emerging Investigators (JEI): SES4U, Holy Trinity School, 2026*

---

## Research Question

Do stars with higher iron content ([Fe/H]) preferentially host gas giant planets, consistent with the Core Accretion Model of planetary formation?

---

## Findings

The initial OLS regression of planet mass against stellar metallicity (only including gas giants larger than 50 M⊕) found a statistically significant but negligible result (R² = 0.0211, p = 2.17 × 10⁻⁶) and a weakly negative slope showing that once formed, metallicity is not a predictor of giant mass. As the Core Accretion Model predicts an eventual impact on occurrence and not final mass, the analysis was restructured into the following two complementary tests:

| Analysis | Result |
|---|---|
| OLS regression (mass vs. metallicity) | R² = 0.0211, p = 2.17 × 10⁻⁶ (negligible, negative slope) |
| Fischer power-law occurrence fit | R² = 0.865, p = 9.57 × 10⁻⁵ (monotonic rise with metallicity) |
| Two-sample KS test (giant vs. small-only hosts) | D = 0.252, p = 8.89 × 10⁻¹⁷ (distributions distinct) |

Giant hosts have a mean metallicity of +0.098 dex; small-planet-only hosts average −0.005 dex. Both the occurrence-rate and KS results support the Core Accretion Model: metallicity acts as a threshold catalyst for giant formation, not a determinant of final giant mass.

---

## Dataset

| Property | Value |
|---|---|
| Source | [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) |
| Table | `pscomppars` (Planetary Systems Composite Parameters) |
| Access method | Table Access Protocol (TAP) via ADQL |
| Access date | May 2026 |
| Final sample | 1,776 confirmed planets across 1,418 unique host stars |
| Gas-giant subsample | 1,053 planets (M > 50 M⊕) |

`pscomppars` was chosen over the standard `ps` table because NASA's pipeline selects one composite, best-precision row per confirmed planet, preventing the duplicate-entry inflation that affects `ps`.

---

## Repository Structure

```
.
├── data/
│   ├── processed/
│   │   ├── hertzsprung_russel/
│   │   │   └── HR_dataset.csv
│   │   ├── cleaned_data.csv
│   │   ├── hosts_classified.csv
│   │   └── star_analysis_data.csv
│   └── raw/
├── figures/
│   ├── interactive/
│   │   ├── interactive_plot.html
│   │   ├── same_mass_iron_comparison.html
│   │   └── star_size_vs_exoplanet_count.html
│   ├── main/
│   │   ├── fig_buchhave_ks.jpg / .tiff
│   │   ├── fig_metallicity_vs_mass.jpg / .tiff
│   │   └── fig_occurrence_rate.jpg / .tiff
│   └── supplementary/hertzsprung_russel/
│       └── HR_plot.html
├── results/
│   ├── statistics/
│   │   └── regression_results.txt
│   └── tables/
│       ├── hertzsprung_russel/
│       │   └── massplot.csv
│       ├── occurrence_bins.csv
│       └── same_mass_iron_comparison.csv
├── scripts/
│   ├── analysis/
│   ├── data_processing/
│   │   └── dataquery.py
│   └── plotting/
│       ├── hertzsprung_russel/
│       ├── MAINDATASET_plotter.py
│       ├── OCCURRENCE_plotter.py
│       └── SIZEVSQUANTITY_plotter.py
└── README.md
```

---

## Reproducing the Analysis

**Requirements:** Python 3.x, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`

```bash
# 1. Clone the repository
git clone https://github.com/0xLiam0920/SES4U-Capstone-Exoplanets.git
cd SES4U-Capstone-Exoplanets

# 2. Query NASA and build the cleaned dataset (requires internet access)
python scripts/data_processing/dataquery.py

# 3. Generate the mass-metallicity regression figure (Figure 1)
python scripts/plotting/MAINDATASET_plotter.py

# 4. Generate the occurrence-rate and KS figures (Figures 2 & 3)
python scripts/plotting/OCCURRENCE_plotter.py
```

Because `dataquery.py` queries the NASA TAP endpoint live, results will reflect the current state of `pscomppars` at the time of execution. Minor variation in sample size from the values reported in the paper is expected as the archive is updated continuously.

---

## Foundational Literature

- Fischer, D. A., & Valenti, J. (2005). The planet-metallicity correlation. *The Astrophysical Journal, 622*(2), 1102–1117.
- Buchhave, L. A., et al. (2012). An abundance of small exoplanets around stars with a wide range of metallicities. *Nature, 486*, 375–377.
- Pollack, J. B., et al. (1996). Formation of the giant planets by concurrent accretion of solids and gas. *Icarus, 124*(1), 62–85.
- Schlaufman, K. C. (2018). Evidence of an upper bound on the masses of planets and its implications for giant planet formation. *The Astrophysical Journal, 853*(1), 37.

---

## Team

| Role | Name |
|---|---|
| Data Engineer / Methods Lead | Liam Nayyer |
| Results & Statistical Analysis | Ivan Wang |
| Principal Investigator / Literature Review | Desmond Li |

*Supervisor: Mr. Hodaei — SES4U, Holy Trinity School, 2026*
