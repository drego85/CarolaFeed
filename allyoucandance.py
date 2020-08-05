#!/usr/bin/python
# This file is part of RSS Generator Feed.
#
# Copyright(c) 2017 Andrea Draghetti
# https://www.andreadraghetti.it
#
# This file may be licensed under the terms of of the
# GNU General Public License Version 3 (the ``GPL'').
#
# Software distributed under the License is distributed
# on an ``AS IS'' basis, WITHOUT WARRANTY OF ANY KIND, either
# express or implied. See the GPL for the specific language
# governing rights and limitations.
#
# You should have received a copy of the GPL along with this
# program. If not, go to http://www.gnu.org/licenses/gpl.html
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import sys
import pytz
import Config
import pickle
import hashlib
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
from podgen import Podcast, Episode, Media

# User Agent MSIE 11.0 (Win 10)
headerdesktop = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; MATBJS; rv:11.0) like Gecko",
                 "Accept-Language": "it"}

headerdesktopsavelink = {"User-Agent": "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:79.0) Gecko/20100101 Firefox/79.0",
                        "Accept-Language": "it,en-US;q=0.7,en;q=0.3",
                         "Content-Type": "application/x-www-form-urlencoded",
                         "X-Requested-With": "XMLHttpRequest",
                         "Origin": "https://www.savelink.info",
                         "Referer": "https://www.savelink.info/sites/mixcloud"}


timeoutconnection = 120
risorseaudioarray = []

rssfile = Config.outputpath + "allyoucandance.xml"


def load_analyzed_case():
    try:
        with open("allyoucandance_analyzed.txt", "rb") as fp:
            if fp:
                episodesList = pickle.load(fp)

        return episodesList

    except IOError as e:
        print(e)
        sys.exit()
    except Exception:
        return []


def save_analyzed_case(episodesList):
    try:
        with open("allyoucandance_analyzed.txt", "wb") as fp:
            pickle.dump(episodesList, fp)
    except IOError as e:
        print(e)
        sys.exit()
    except Exception as e:
        print(e)
        raise


def genero_feed(episodesList):
    if episodesList:
        # Creo un nuovo podcast
        p = Podcast()

        p.name = "All You Can Dance by Dino Brawn"
        p.description = "Feed Podcast non ufficiale di All You Can Dance by Dino Brown - Powered By Andrea Draghetti"
        p.website = "https://onedance.fm/"
        p.explicit = True
        p.image = "https://rss.draghetti.it/allyoucandance_image.jpg"
        p.feed_url = "https://rss.draghetti.it/allyoucandance.xml"
        p.copyright = "One Dance"
        p.language = "it-IT"

        for episodedetails in episodesList:
            episode = Episode()

            episode.title = episodedetails[1].encode("ascii", "ignore")
            episode.link = episodedetails[2].encode("ascii", "ignore")

            # La dimensione e statistica in base alle puntante analizzate
            episode.media = Media(episodedetails[3], 30000000, type="audio/x-m4a", duration=None)
            episode.publication_date = episodedetails[4]

            p.episodes.append(episode)

        # Print to stdout, just as an example
        p.rss_file(rssfile, minimize=False)


def main():
    # Ottengo la lista delle puntante gia analizzate
    episodesList = load_analyzed_case()

    # Estrapolo dalla lista appena ottenuta i soli Hash delle puntate precedenti
    episodesHash = []
    for episodes in episodesList:
        episodesHash.append(episodes[0])

    # Analizzo tutte le puntante pubblicate sul sito per individuarne di nuove
    urlmixcloud = "https://www.mixcloud.com/onedance/"
    urlmixcloudrss = "https://rssbox.herokuapp.com/mixcloud/onedance/One%20Dance"

    feed = feedparser.parse(urlmixcloudrss)

    for post in feed.entries:
        episodeLink = post.link
        episodeLinkHash = hashlib.sha1(episodeLink.encode("ascii", "ignore")).hexdigest()
        episodeTitle = post.title
        episodeTitleLower = post.title.lower()

        if episodeLinkHash not in episodesHash and "all you can dance" in episodeTitleLower:

            # Ottengo l'URL della nuova risorsa audio
            mixclouddownloader = "https://www.savelink.info/input"
            data = {"url": episodeLink}
            response = requests.post(mixclouddownloader, data=data, headers=headerdesktopsavelink, timeout=timeoutconnection)

            episodeAudio = response.json()["link"]

            # Aggiungo alla lista la nuova puntanta
            if episodeAudio:
                episodeDate = pytz.utc.localize(datetime.datetime.utcnow())
                episodesList.insert(0, [episodeLinkHash, episodeTitle, episodeLink, episodeAudio, episodeDate])

    # Salvo la lista delle puntante
    save_analyzed_case(episodesList)

    # Genero il Feed XML
    genero_feed(episodesList)


if __name__ == "__main__":
    main()
