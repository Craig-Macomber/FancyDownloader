# Setup

Use / install newish python (I used 3.8.10)

## API access

On the sites admin module, enable API access: see \_admin: Admin Panel » Security » API access

Ensure at least read permissions (recommended read only to reduce risk).

Some docs at http://developer.wikidot.com/i-want-api-access

Then for the wikidot account, get the keys: My Account » Settings » API access

Copy your read-only key.

Create `apikey.txt` containing the wikidot api key.

## Large file support

wikidot API seems to have issues with large files.

Downloader uses urllib to downlod them from the wdfiles url.

It appears this this works for private sites, despite having no authentication:
It seems like a security hole that files can be downloaded with a guessed URL, but it makes this script's job easier.

## Run downloader

`python3 FancyDownloader.py --site your-wikidot-site-name`

Files will be saved in `../site/your-wikidot-site-name`.
