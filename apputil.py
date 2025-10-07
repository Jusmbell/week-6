"""Utility module: minimal Genius API wrapper used for the Week 6 exercises.

Exercises implemented:
1. Genius class initializer stores access token.
2. get_artist(search_term): returns dict with artist JSON for best match.
3. get_artists(search_terms): returns DataFrame with summary rows."""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

import requests
import pandas as pd
from dotenv import load_dotenv

# Load a .env file (if present) so you can keep secrets out of source.
# This *still* allows a static fallback for simplicity while learning.
load_dotenv()

# Optional static fallback. For production code you would normally *not* hard
# code API tokens. Here it keeps the focus on learning classes / API calls.
STATIC_TOKEN = "iLgX5KDPdNtFbilnP8qVKY_d7CcESB-6p-aL9a8c0JkM3MNDtW5GnkZY54a8GHp-"


class Genius:
	"""Minimal Genius API client.

	Parameters
	----------
	access_token : str | None
		If None, attempts to read ACCESS_TOKEN from environment.
	base_url : str
		Base API URL (override for testing if needed).
	"""

	def __init__(self, access_token: Optional[str] = None, *, base_url: str = "https://api.genius.com") -> None:
		"""Store / prepare everything needed for subsequent API calls.

		Resolution order for the token (first non-empty wins):
		1. Explicit ``access_token`` argument.
		2. Environment variable ``ACCESS_TOKEN`` (via .env or shell export).
		3. ``STATIC_TOKEN`` constant above (learning convenience only).
		"""
		self.access_token = access_token or os.environ.get("ACCESS_TOKEN") or STATIC_TOKEN
		if not self.access_token:
			raise ValueError("No access token. Set ACCESS_TOKEN env var or put it in STATIC_TOKEN.")
		# Normalize base URL once so helper methods can build endpoints reliably.
		self.base_url = base_url.rstrip("/")
		# Session object lets us reuse HTTP connection + keep auth header in one place.
		self._session = requests.Session()
		self._session.headers.update({"Authorization": f"Bearer {self.access_token}"})

	# -------------------------
	# Internal helpers
	# -------------------------
	def _get(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
		"""Low-level GET request wrapper. Returns the parsed JSON response."""
		url = path if path.startswith("http") else f"{self.base_url}{path}"
		resp = self._session.get(url, params=params, timeout=10)
		resp.raise_for_status()
		return resp.json()

	def _search(self, search_term: str, per_page: int = 1) -> List[Dict[str, Any]]:
		"""Low-level wrapper around the public Genius search endpoint."""
		data = self._get("/search", params={"q": search_term, "per_page": per_page})
		# The API nests hits under response -> hits. Provide a safe fallback.
		return data.get("response", {}).get("hits", [])

	# -------------------------
	# Public API (Exercises)
	# -------------------------
	def get_artist(self, search_term: str) -> Dict[str, Any]:
		"""Return a dictionary describing the *primary* artist for the first hit.

		Algorithm (simple, deterministic):
		1. Use the search endpoint (per_page=1) to get the top result.
		2. Pull the ``primary_artist.id`` from that hit.
		3. Call ``/artists/<id>`` for richer metadata.
		4. Return the nested ``artist`` dict; return ``{}`` if anything is missing.
		"""
		hits = self._search(search_term, per_page=1)
		if not hits:
			return {}

		# Grab primary artist id robustly.
		primary = hits[0].get("result", {}).get("primary_artist", {})
		artist_id = primary.get("id")
		if artist_id is None:
			return {}

		artist_json = self._get(f"/artists/{artist_id}")
		return artist_json.get("response", {}).get("artist", {})

	def get_artists(self, search_terms: List[str]) -> pd.DataFrame:
		"""Vectorized convenience: run ``get_artist`` for each term and tabulate.

		Returned DataFrame columns:
		- ``search_term``: the input search text.
		- ``artist_name``: canonical name returned by Genius.
		- ``artist_id``: unique artist identifier.
		- ``followers_count``: may be ``None`` if the API omits it.
		"""
		rows = []
		for term in search_terms:
			artist = self.get_artist(term)
			rows.append(
				{
					"search_term": term,
					"artist_name": artist.get("name"),
					"artist_id": artist.get("id"),
					"followers_count": artist.get("followers_count"),
				}
			)
		return pd.DataFrame(rows)


if __name__ == "__main__":
	# Simple smoke test so you can "python apputil.py" and see real output.
	try:
		g = Genius()
		print("Token loaded. Running sample calls...")
		example = g.get_artist("Radiohead")
		print("Artist name:", example.get("name"), "Followers:", example.get("followers_count"))
		print(g.get_artists(["Rihanna", "Tycho", "Seal", "U2"]))
	except ValueError as e:
		print(e)
		print("Add your token to .env as ACCESS_TOKEN=... OR assign it to STATIC_TOKEN above.")

