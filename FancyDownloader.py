#!/usr/bin/env python3

from xmlrpc import client
import xml.etree.ElementTree as ET
import os
import datetime
import time
import urllib.request


import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--site', help='name of wikidot site')
args = parser.parse_args()

siteName = args.site


def DecodeDatetime(dtstring):
    if dtstring is None:
        return datetime.datetime(1950, 1, 1, 1, 1, 1)    # If there's no datetime, return something early
    if not dtstring.endswith("+00:00"):
        raise ValueError("Could not decode datetime: '")+dtstring+"'"
    return datetime.datetime.strptime(dtstring[:-6], '%Y-%m-%dT%H:%M:%S')

# Download a page from Wikidot and possibly store it locally.
# The page's contents are stored in their files, the source in <saveName>.txt, the rendered HTML in <saveName>..html, and all of the page meta information in <saveName>.xml
# Setting skipIfNotNewer to True allows a forced downloading of the page, reghardless of whether it is already stored locally.  This is mostly useful to overwrite the hidden consequences of old sync errors
# The return value is True when the local version of the page has been updated, and False otherwise
def DownloadPage(url, pageName, skipIfNotNewer):
    time.sleep(0.05)    # Wikidot has a limit on the number of RPC calls/second.  This is to throttle the download to stay on the safe side.

    # Download the page's data
    try:
        wikiName=pageName.replace("_", ":", 1)  # The '_' is used in  place of Wikidot's ':' in page names in non-default namespaces. Convert back to the ":" form for downloading)
        if wikiName == "con-": # "con" is a special case since that is a reserved word in Windows and may not be used as a filename.  We use "con-" which is not a possible wiki name, for the local name .
            wikiName="con"
        pageData=client.ServerProxy(url).pages.get_one({"site" : siteName, "page" : wikiName})
    except:
        print("****Failure downloading "+pageName)
        return False # Its safest on download failure to return that nothing changed

    # NOTE: This relies on the update times stored in the local file's xml and in the wiki page's updated_at metadata
    # It will not detect incompletely downloaded pages if the xml file exists
    if skipIfNotNewer:
        # Get the updated time for the local version
        localUpdatedTime=None
        if os.path.isfile(pageName+".xml"):
            tree=ET.parse(pageName+".xml")
            doc=tree.getroot()
            localUpdatedTime=doc.find("updated_at").text

        # Get the wiki page's updated time
        wikiUpdatedTime=GetPageWikiTime(pageName, pageData)
        # We return True whenever we have just downloaded a page which was already up-to-date locally
        tWiki = DecodeDatetime(wikiUpdatedTime)
        tLocal = DecodeDatetime(localUpdatedTime)

        if tWiki <= tLocal:
            return False

    # OK, we're going to download this one
    print("   Updating: '"+pageName+"'")

    # Write the page source to <pageName>.txt
    if pageData.get("content", None) is not None:
        with open(pageName+".txt", "wb") as file:
            file.write(pageData["content"].encode("utf8"))

    # Write the page's rendered HTML to <pageName>.html
    if pageData.get("html", None) is not None:
        with open(pageName+".html", "wb") as file:
            file.write(pageData["html"].encode("utf8"))

    # Write the rest of the page's data to <pageName>.xml
    SaveMetadata(pageName, pageData)

    # Check for attached files
    # If any exist, save them in a directory named <pageName>
    # If none exist, don't create the directory
    # Note that this code does not delete the directory when previously-existing files have been deleted from the wiki page
    fileNameList=client.ServerProxy(url).files.select({"site": siteName, "page": wikiName})
    if len(fileNameList) > 0:
        if not os.path.exists(pageName):
            os.mkdir(pageName)   # Create a directory for the files and metadata
            os.chmod(pageName, 0o777)
        for fileName in fileNameList:
            # Use get_meta instead of get_one since it supports files over 6mb. See http://www.wikidot.com/doc:api
            filesStuff = client.ServerProxy(url).files.get_meta({"site": siteName, "page": wikiName, "files": [fileName]})
            fileStuff = filesStuff[fileName]
            path=os.path.join(os.getcwd(), pageName, fileName)
            # Now save the file's metadata in an xml file named for the file
            SaveMetadata(os.path.join(pageName, fileName), fileStuff)
            # Download the actual file
            urllib.request.urlretrieve(fileStuff["download_url"], path)

    return True

# Save the wiki page's metadata to an xml file
def SaveMetadata(localName, pageData):
    root = ET.Element("data")
    wikiUpdatedTime = None
    for itemName in pageData:
        if itemName == "content" or itemName == "html":  # Skip: We've already dealt with this
            continue
        # Page tags get handled specially
        if itemName == "tags":
            tags = pageData["tags"]
            if len(tags) > 0:
                tagsElement = ET.SubElement(root, "tags")
                for tag in tags:
                    tagElement = ET.SubElement(tagsElement, "tag")
                    tagElement.text = tag
            continue
        if itemName == "updated_at":  # Save the updated time
            wikiUpdatedTime = pageData[itemName]
        # For all other pieces of metadata, create a subelement in the xml
        if pageData[itemName] is not None and pageData[itemName] != "None":
            element = ET.SubElement(root, itemName)
            element.text = str(pageData[itemName])

    # And write the xml out to file <localName>.xml.
    tree = ET.ElementTree(root)
    tree.write(localName + ".xml")
    return wikiUpdatedTime

# Get the wiki page's update time from the its metadata
def GetPageWikiTime(localName, pageData):
    for itemName in pageData:
        if itemName == "updated_at":  # Save the updated time
            return pageData[itemName]


# ---------------------------------------------
# Main

# Get the magic URL for api access
apiKey=open("apikey.txt").read().strip()
url = f"https://{siteName}:{apiKey}@www.wikidot.com/xml-rpc-api.php"


# Change the working directory to the destination of the downloaded wiki
cwd=os.getcwd()
path=os.path.join(cwd, f"../site/{siteName}")
os.makedirs(path, exist_ok=True)
os.chdir(path)
print(f"saving site to {path}")
del cwd, path


# Look for a file called "override.txt" -- if it exists, load those pages and do nothing else.
# Override.txt contains a list of page names, one name per line.
if os.path.exists("../../FancyDownloader/override.txt"):
    with open("../../FancyDownloader/override.txt", "r") as file:
        override=file.readlines()
    override=[x.strip() for x in override]  # Remove trailing '\n'
    # Remove duplicates;
    nodupes=[]
    for x in override:
        if x not in nodupes:
            nodupes.append(x)
    override=nodupes
    del nodupes, x
    print("Downloading override pages...")
    countDownloadedPages=0
    for pageName in override:
        if DownloadPage(url, pageName, False):
            countDownloadedPages+=1
    exit()

# Now, get list of recently modified pages.  It will be ordered from most-recently-updated to least.
# (We're using composition, here.)
print("Get list of all pages from Wikidot, sorted from most- to least-recently-updated")
listOfAllWikiPages=client.ServerProxy(url).pages.select({"site" : siteName, "order": "updated_at desc"})
listOfAllWikiPages=[name.replace(":", "_", 1) for name in listOfAllWikiPages]   # ':' is used for non-standard namespaces on wiki. Replace the first ":" with "_" in all page names because ':' is invalid in Windows file names
listOfAllWikiPages=[name if name != "con" else "con-" for name in listOfAllWikiPages]   # Handle the "con" special case

# Download the recently updated pages until we start finding pages we already have the most recent version of
#
# stoppingCriterion controls how long the update runs
# stoppingCriterion:
#   >0 --> Run until we have encountered stoppingCriterion consecutive pages that don't need updates
#   =0 --> Run through all pages (this is slow and resource-intensive)
# This is used to handle cases where the downloading and comparison process has been interrupted before updating all changed pages.
# In that case there will be a wodge of up-to-date recently-changed pages before the pages that were past the interruption.
# StoppingCriterion needs to be big enough to get past that wodge.
stoppingCriterion=100
print("Downloading recently updated pages...")
countUpToDatePages=0
countDownloadedPages=0
for pageName in listOfAllWikiPages:
    if DownloadPage(url, pageName, True):
        countDownloadedPages+=1
    else:
        countUpToDatePages+=1
        if stoppingCriterion > 0 and countUpToDatePages > stoppingCriterion:
            print("      "+str(countDownloadedPages)+" pages downloaded")
            print("      Ending downloads. " + str(stoppingCriterion) + " up-to-date pages found")
            break

# Get the page list from the local directory and use that to create lists of missing pages and deleted pages
print("Creating list of local files")
# Since all local copies of pages have a .txt file, listOfAllDirPages will contain the file name of each page (less the extension)
# So we want a list of just those names stripped of the extension
listOfAllDirPages=[p[:-4] for p in os.listdir(".") if p.endswith(".txt")]

# Now figure out what pages are missing and download them.
print("Downloading missing pages...")
listOfAllMissingPages = [val for val in listOfAllWikiPages if val not in listOfAllDirPages]  # Create a list of pages which are in the wiki and not downloaded
if len(listOfAllMissingPages) == 0:
    print("   There are no missing pages")
for pageName in listOfAllMissingPages:
    DownloadPage(url, pageName, True)

# And delete local copies of pages which have disappeared from the wiki
# Note that we don't detect and delete local copies of attached files which have been removed from the wiki where the wiki page remains.
print("Removing deleted pages...")
listOfAllDeletedPages = [val for val in listOfAllDirPages if val not in listOfAllWikiPages]  # Create a list of pages which exist locally, but not in the wiki
if len(listOfAllDeletedPages) == 0:
    print("   There are no pages to delete")
for pageName in listOfAllDeletedPages:
    print("   Removing: " + pageName)
    if os.path.isfile(pageName + ".xml"):
        os.remove(pageName + ".xml")
    if os.path.isfile(pageName + ".html"):
        os.remove(pageName + ".html")
    if os.path.isfile(pageName + ".txt"):
        os.remove(pageName + ".txt")

print("Done")

