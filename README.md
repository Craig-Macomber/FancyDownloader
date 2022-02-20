# Setup

Use / install newish python (I used 3.8.10)

## Optional (Recommended): python virtual environment

Setup a venv: https://docs.python.org/3/tutorial/venv.html

`python3 -m venv .venv`
`source .venv/bin/activate`

## Enable API access

On the sites admin module, enable API access: see \_admin: Admin Panel » Security » API access

Ensure at least read permissions (recommended read only to reduce risk).

Some docs at http://developer.wikidot.com/i-want-api-access

Then for the wikidot account, get the keys: My Account » Settings » API access

Copy your read-only key.

Create `apikey.txt` containing the wikidot api key.

## Setup other config

Set `siteName` in FancyDownloader.py

Files will be saved in `f'../{siteName}'`

## Large file support

wikidot API seems to have issues with large files.

Downloader uses urllib to downlod them from the wdfiles url.

This may have issues with private sites/pages.

## Run downloader

`python3 FancyDownloader.py`
