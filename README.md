# Overview

Program to download an entire wiki (except for history) from Wikidot and then to keep it synchronized.
The wiki is downloaded to a directory. Each wiki page generates two files and possibly a directory:

```
<page>.txt containing the source of the page
<page>.xml containing the metadata of the page
<page> a directory containing the attached files (created only if there are attached files)
```

The basic scheme is to create a list of all pages in the wiki sorted from most-recently-updated to least-recently-updated.
The downloader then walks the list, downloading new copies of each page which is newer on the wiki than in the local copy.
It stops when it finds a page where the local copy is up-to-date
(Note that this leave it vulnerable to a case where the downloader fails partway through and updates some pages nd not others.
The next time it is run, if any pages have been updated in the mean time, the massed pages won;t be noticed.
Since the alternative is to check every page every time, and since this was written to deal with a wiki with >20K ages, it is an accepted issue to be dea;lt with by hand.)

The next step is to compare the list of all local .txt files with the list of all pages, and to download any which are missing.
(Note that this does not deal with deleted .xml files or deleted attached files. This fairly cheap to check, so t might be a useful enhancement.)

The final step is to look for local .txt files which are not on the wiki. These will typically be files which have been deleted on the wiki. They are deleted locally.

# Setup

Use / install newish python (I used 3.8.10)

## API access

On the sites admin module, enable API access: see \_admin: Admin Panel » Security » API access

Ensure at least read permissions (recommended read only to reduce risk).

Some docs at http://developer.wikidot.com/i-want-api-access

Then for the wikidot account, get the keys: My Account » Settings » API access

Copy your read-only key.

Create `apikey.txt` containing the wikidot api key.

## Run downloader

`python3 FancyDownloader.py --site your-wikidot-site-name`

Files will be saved in `../site/your-wikidot-site-name`.
