from os import close
import requests
import urllib
from requests.api import head
from bs4 import BeautifulSoup
import re
from github import Github
import sys


def onlineChannelsLinks(vgm_url):

    html_text = requests.get(vgm_url).text
    soup = BeautifulSoup(html_text, 'html.parser').find("tbody", class_="streams_table")


    trs = soup.findAll("tr", class_= lambda c: "belongs_to" in str(c) and c != None)
    tr_pairs = [(trs[i], trs[i+1]) for i in range(0, len(trs), 2)]

    online_channels = []

    for tr in tr_pairs:
        tds = tr[0].find_all("td")
        if tds[3].div['title'] == "Online":
            online_channels.append(tr[1].td.table.tr.find_all("td")[1].a["href"])

    return online_channels

def writeLink(playlistFile, ulr):
    file = urllib.request.urlopen(ulr)
    first = True
    for line in file:
        if first:
            first = False
            continue
        decoded_line = line.decode("utf-8")
        ungrouped_line = re.sub('group-title="(.*?)"', 'group-title="All"', decoded_line)
        playlistFile.write(ungrouped_line)

def get_page_count(vgm_url):
    html_text = requests.get(vgm_url).text
    ul = BeautifulSoup(html_text, 'html.parser').find("ul", class_="pagination pagination-separated pagination-xs")
    href = ul.findAll('li')[-1].find('a')["href"]
    return int(href.split("/")[-1])
    

def createFile(filename="playlist.m3u", url='https://iptvcat.com/brazil_-_-_-_-_-_-_/'):
    online_channels = []
    
    page_count = get_page_count(url)

    print("Found "+str(page_count)+" pages")

    print("Fetching online channels")

    for i in range(1, page_count+1):
        try:
            online_channels += onlineChannelsLinks(url+str(i))
        except Exception as ex:
            print("Something went wrong skipping...\nReason:"+str(ex)+"\n\n")
        print(str(round((i/page_count)*100,2))+"%")

    online_file = open("online_channels", "w")
    for channel in online_channels:
        online_file.write(channel)
        online_file.write("\n")

    print("Downloading playlist...")
    file = open(filename, "w")
    file.write("#EXTM3U\n")
    for i, channel in enumerate(online_channels):
        writeLink(file, channel)
        print(str(round((i/len(online_channels))*100,2))+"%")
    file.close()
    print("Done")

def upload_file(token, filename="playlist.m3u", repo_name="hlscat-fetcher", commit_message="updates playlist", branch_name="master"):
    g = Github(token)
    repo = g.get_user().get_repo(repo_name)
    contents = repo.get_contents(filename)
    content = open(filename).read()
    repo.update_file(contents.path, commit_message, content, contents.sha, branch=branch_name)

if __name__ == "__main__":
    createFile()
    upload_file(sys.argv[1])