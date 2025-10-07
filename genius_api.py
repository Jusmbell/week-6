# built-in / stdlib imports
import requests
import os
from multiprocessing import Pool
from time import sleep

# third-party imports
import pandas as pd
from tqdm import tqdm
from numpy.random import uniform
from dotenv import load_dotenv

load_dotenv()

# constants
# STATIC TOKEN (per user request). In real projects prefer environment vars.
ACCESS_TOKEN = "iLgX5KDPdNtFbilnP8qVKY_d7CcESB-6p-aL9a8c0JkM3MNDtW5GnkZY54a8GHp-"
NAME_DEMO = __name__

def genius(search_term, per_page=15):
    """Search Genius for a term and return the raw ``hits`` list.

    This mirrors the class method logic but keeps things inline. We construct
    the URL manually instead of using a Session object for simplicity here.
    """
    genius_search_url = f"http://api.genius.com/search?q={search_term}&" + \
                        f"access_token={ACCESS_TOKEN}&per_page={per_page}"
    
    response = requests.get(genius_search_url)
    json_data = response.json()
    
    return json_data['response']['hits']

def genius_to_df(search_term, n_results_per_term=10, verbose=True, savepath=None):
    """Return a flattened DataFrame for one search term.

    Steps:
    1. Call :func:`genius` to get raw hits JSON.
    2. Pull the nested ``result`` dict for each hit.
    3. Expand the nested ``stats`` and ``primary_artist`` sub-dicts into columns.
    4. Optionally save to disk.
    """
    json_data = genius(search_term, per_page=n_results_per_term)
    hits = [hit['result'] for hit in json_data]
    df = pd.DataFrame(hits)

    # Expand nested dictionaries into top-level columns (wide format).
    df_stats = df['stats'].apply(pd.Series)
    df_stats.rename(columns={c: 'stat_' + c for c in df_stats.columns}, inplace=True)

    df_primary = df['primary_artist'].apply(pd.Series)
    df_primary.rename(columns={c: 'primary_artist_' + c for c in df_primary.columns}, inplace=True)

    df = pd.concat((df, df_stats, df_primary), axis=1)

    if verbose:
        print(f'PID: {os.getpid()} ... search_term:', search_term)
        print(f"Data gathered for {search_term}.")

    if savepath:
        df.to_csv(f"{savepath}/genius-{search_term}.csv", index=False)

    return df

def genius_to_dfs(search_terms, **kwargs):
    """Loop over many terms and concatenate their per-term DataFrames.

    Accepts the same keyword arguments as :func:`genius_to_df` (forwarded).
    """

    dfs = []

    # loop through search_terms in question
    for search_term in tqdm(search_terms):
        df = genius_to_df(search_term, **kwargs)
        
        # add to list of DataFrames
        dfs.append(df)

    return pd.concat(dfs)

def testing():
    """Tiny smoke test to show the module executed."""
    print('Testing 1, 2, 3 ...')
    return None

def job_test(num, mult=2):
    """Example function for demonstrating multiprocessing patterns."""
    print(f'PID: {os.getpid()} ... num:', num)
    sleep(uniform(0.5, 1.5))
    return num * mult

