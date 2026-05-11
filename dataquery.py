import pandas as pd

# 1. Verification of the full NASA TAP endpoint
# 2. Corrected column: st_metlim
base_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
query = "select pl_name,pl_massj,st_met,pl_massjlim,st_metlim from pscomppars"

# Formulate the URL using simple replacements to avoid standard library over-encoding
# NASA's TAP service specifically likes '+' for spaces and literal commas
encoded_query = query.replace(" ", "+")
url = f"{base_url}?query={encoded_query}&format=csv"

print(f"Connecting to NASA Exoplanet Archive...")

try:
    # Use pandas to read directly from the URL
    df = pd.read_csv(url)

    if df.empty:
        print("The server returned an empty file. Check your query parameters.")
    else:
        # Column definitions - what we wanna keep and clean.
        keep_cols = ["pl_name", "pl_massj", "st_met", "pl_massjlim", "st_metlim"]
        
        # Filter and clean
        df = df[[c for c in keep_cols if c in df.columns]]
        
        # Gets rid of any data that shows the metlim value between 1 and -1, since this indicates the value is a limit and not an actual measurement. Same for massjlim.
        for col in ["pl_massjlim", "st_metlim"]:
            if col in df.columns:
                df = df[~df[col].isin([1, -1])]

        # Remove rows missing our two primary variables
        df = df.dropna(subset=["pl_massj", "st_met"])
        
        df.to_csv("cleaned_data.csv", index=False)
        print(f"Success! Saved {len(df)} rows to cleaned_data.csv.")
        print(df.head())

except Exception as e:
    print(f"Failed to retrieve data: {e}") ## had to do this after it queried fine but forgot the metallic (met) data because of a bloody typo. 
