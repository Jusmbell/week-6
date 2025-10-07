"""Utility module implementing a simple Genius API wrapper for exercises.

Exercises implemented:
1. Genius class initializer stores access token.
2. get_artist(search_term): returns dict with artist JSON for best match.
3. get_artists(search_terms): returns DataFrame with summary rows.

Keep it simple / concise as requested.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

import requests
import pandas as pd
from dotenv import load_dotenv

# Load .env if present so ACCESS_TOKEN can be stored there (not in code)
load_dotenv()


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
		# NEVER hard‑code your token in source. Read from argument or env var.
		self.access_token = access_token or os.environ.get("ACCESS_TOKEN")
		if not self.access_token:
			raise ValueError("Genius access token not provided and ACCESS_TOKEN env var not set.")
		self.base_url = base_url.rstrip("/")
		self._session = requests.Session()
		self._session.headers.update({"Authorization": f"Bearer {self.access_token}"})

	# -------------------------
	# Internal helpers
	# -------------------------
	def _get(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
		"""Internal GET wrapper returning parsed JSON; raises for HTTP errors."""
		url = path if path.startswith("http") else f"{self.base_url}{path}"
		resp = self._session.get(url, params=params, timeout=10)
		resp.raise_for_status()
		return resp.json()

	def _search(self, search_term: str, per_page: int = 1) -> List[Dict[str, Any]]:
		data = self._get("/search", params={"q": search_term, "per_page": per_page})
		return data.get("response", {}).get("hits", [])

	# -------------------------
	# Public API (Exercises)
	# -------------------------
	def get_artist(self, search_term: str) -> Dict[str, Any]:
		"""Return JSON dict for the best-matching artist.

		Steps:
		1. Search term -> first hit primary artist id.
		2. Fetch /artists/<id> endpoint.
		3. Return artist dictionary (empty dict if not found).
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
		"""Return DataFrame with one row per search term.

		Columns:
		- search_term
		- artist_name
		- artist_id
		- followers_count (may be None)
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


if __name__ == "__main__":  # simple manual test (optional)
	token = os.environ.get("ACCESS_TOKEN")
	if not token:
		print("(Skip manual test) Define ACCESS_TOKEN env var to run example.")
	else:
		g = Genius(token)
		example = g.get_artist("Radiohead")
		print("Artist name:", example.get("name"), "Followers:", example.get("followers_count"))
		print(g.get_artists(["Rihanna", "Tycho", "Seal", "U2"]))

