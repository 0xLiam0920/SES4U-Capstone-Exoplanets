import io
import pandas as pd
import urllib.error
import urllib.parse
import urllib.request
import time

BASE_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"


def run_tap_query(query: str) -> pd.DataFrame:
    params = urllib.parse.urlencode({"query": query, "format": "csv"})
    url = f"{BASE_URL}?{params}"

    last_error = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                raw = resp.read()
            return pd.read_csv(io.BytesIO(raw))
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 3:
                wait_s = 2 * attempt
                print(f"TAP request attempt {attempt} failed, retrying in {wait_s}s...")
                time.sleep(wait_s)

    raise RuntimeError(f"NASA TAP query failed after 3 attempts: {last_error}")


def build_mass_metallicity_dataset() -> None:
    """Build dataset used by MAINDATASET_plotter.py and OCCURRENCE_plotter.py."""
    query = (
        "select hostname,pl_name,pl_massj,st_met,pl_massjlim,st_metlim "
        "from pscomppars "
        "where pl_massj is not null and st_met is not null "
        "and (pl_massjlim is null or pl_massjlim not in (-1,1)) "
        "and (st_metlim is null or st_metlim not in (-1,1))"
    )
    df = run_tap_query(query)

    keep_cols = ["hostname", "pl_name", "pl_massj", "st_met", "pl_massjlim", "st_metlim"]
    df = df[[c for c in keep_cols if c in df.columns]]

    for col in ["pl_massjlim", "st_metlim"]:
        if col in df.columns:
            df = df[~df[col].isin([1, -1])]

    df = df.dropna(subset=["pl_massj", "st_met"])
    df.to_csv("cleaned_data.csv", index=False)
    print(f"Saved {len(df)} rows to cleaned_data.csv")


def build_star_trend_dataset() -> None:
    """Build dataset used by SIZEVSQUANTITY_plotter.py (star size analyses)."""
    query = (
        "select hostname,pl_name,st_mass,st_rad,st_met,st_masslim,st_radlim,st_metlim "
        "from pscomppars "
        "where hostname is not null and pl_name is not null "
        "and st_mass is not null and st_rad is not null and st_met is not null "
        "and (st_masslim is null or st_masslim not in (-1,1)) "
        "and (st_radlim is null or st_radlim not in (-1,1)) "
        "and (st_metlim is null or st_metlim not in (-1,1))"
    )
    df = run_tap_query(query)

    keep_cols = [
        "hostname", "pl_name", "st_mass", "st_rad", "st_met",
        "st_masslim", "st_radlim", "st_metlim",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]

    for col in ["st_masslim", "st_radlim", "st_metlim"]:
        if col in df.columns:
            df = df[~df[col].isin([1, -1])]

    df = df.dropna(subset=["hostname", "pl_name", "st_mass", "st_rad", "st_met"])
    df.to_csv("star_analysis_data.csv", index=False)
    print(f"Saved {len(df)} rows to star_analysis_data.csv")


def main() -> None:
    print("Connecting to NASA Exoplanet Archive...")
    try:
        build_mass_metallicity_dataset()
        build_star_trend_dataset()
        print("Data query complete.")
    except Exception as e:
        print(f"Failed to retrieve data: {e}")


if __name__ == "__main__":
    main()