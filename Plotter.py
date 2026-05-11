import pandas as pd
import math 
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import requests
from io import StringIO
import os
"""""
Ivan (Statistician): The Mathematical Proof
Load Liam’s CSV into your own Kaggle notebook(with Liam’s help) using pandas and seaborn.
Step 1 (The Scope): We are looking at gas giants. Filter your dataframe so it only includes planets with a mass greater than 50 Earths (df[df['pl_bmasse'] > 50]).
Step 2 (Visualizing): Create a scatter plot of st_metfe (x-axis) vs. pl_bmasse (y-axis).
Step 3 (The Math): Run a linear regression using scipy.stats. Extract the R^2 value and the p-value.
Action Item: We need that p-value under 0.05. If you have it, you have mathematically proven the theory.
"""""

debug = True;


file_id = '1vEqyft83eOYNNn9VWypSLnIcPTDCgoFZkXiurXBEqfc' ## this is technically incorrect but I guess it works given I copied the sheet so...
url = f'https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&sheet=Sheet1'
local_csv = 'data.csv'

print("Loading data, please wait one moment...")
df = None

# Attempts to find local CSV file first. If not found, go to web query function
if os.path.exists(local_csv):
    print(f"Local file found, skipping web query: {local_csv}")
    df = pd.read_csv(local_csv)
else:
    if debug:
        print(f"Attempting to load data from URL: {url}")
    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"Error loading data from Google Sheets: {e}")
        print(f"Given the sheet doesn't load, please download the sheet as '{local_csv}' and place it in the root folder.")
        exit(1)

if debug:
    print(df.head())
    print("\n\nThese were the first few columns. Proceeding with graphing...\n")

# Step 1: Filters for all gas giants with mass > 50 Earths (0.157 Jupiter masses)
df_filtered = df[df['pl_massj'] > 0.157]  # 0.157 Jupiter masses ≈ 50 Earth masses

if debug:
    print(f"Filtered to {len(df_filtered)} gas giants with mass > 50 Earths")

# Step 2: Creates our scatter plot of st_met (x-axis) vs. pl_massj (y-axis)
plt.figure(figsize=(10, 6))
plt.scatter(df_filtered['st_met'], df_filtered['pl_massj'])
plt.xlabel('st_met')
plt.ylabel('pl_massj')
plt.title('Host Star Metallicity vs Planet Mass (Gas Giants)')
plt.savefig('metallicity_vs_mass.png', dpi=150, bbox_inches='tight') ## Saves this plot as a PNG file in root dir. dpi is 150 for balanced quality, change if u want.
print("Plot saved to metallicity_vs_mass.png")
plt.close()

# Step 3: Linear regression using scipy.stats. 
slope, intercept, r_value, p_value, std_err = stats.linregress(df_filtered['st_met'], df_filtered['pl_massj'])
r_squared = r_value ** 2


if debug:
    print(f"Linear Regression Results:")
## Extracts the R^2 value and the p-value.
    print(f"R² = {r_squared:.4f}")
    print(f"p-value = {p_value:.6f}")
    if p_value < 0.05:
        print("✓ p-value < 0.05: Theory mathematically proven!")
    else:
        print("✗ p-value >= 0.05: Theory not statistically significant.")
        
## saves the results, with mathematical explanation in a text file in the root dir.
with open('regression_results.txt', 'w') as f:
    f.write("Linear Regression Results:\n")
    f.write(f"R² = {r_squared:.4f}\n")
    f.write(f"p-value = {p_value:.6f}\n")
    if p_value < 0.05:
        f.write("✓ p-value < 0.05: Theory mathematically proven!\n")
    else:
        f.write("✗ p-value >= 0.05: Theory not statistically significant.\n")
print("Regression results saved to regression_results.txt")
exit(0); 


