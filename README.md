# Wiki Retriever

A lightweight Python utility for pulling metadata from Wikimedia Commons category pages and exporting it as CSV/JSON.

## What it does

This project retrieves media entries from a Wikimedia Commons category, then enriches them with metadata from the Wikimedia and Wikidata APIs. The output is designed for analysis, cataloging, and dataset creation.

It currently targets categories such as:

- Art of Colombia
- Artists from Colombia
- Murals in Colombia
- Paintings from Colombia

## Features

- Fetches category members from Wikimedia Commons
- Saves raw category data as JSON
- Resolves related metadata from Wikidata
- Exports structured CSV records
- Extracts wikitext template parameters for items like Artwork templates
- Supports batch processing for a category at a time

## Project structure

- `config.py` – configuration values for the target category and Wikimedia API
- `id-list-generator.py` – fetches category members and saves them as JSON
- `api-request.py` – extracts metadata from Wikimedia/Wikidata and writes CSV
- `web-request.py` – fetches wikitext, parses template fields, and writes CSV
- `output/` – generated JSON/CSV results

## Setup

Install dependencies:

```bash
pip install requests