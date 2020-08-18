import requests
import lxml.html
import json


class BuhitterConfig():
    BUHITTER_ENDPOINT = "https://buhitter.com"
    TAGS_ENDPOINT = f"{BUHITTER_ENDPOINT}/ja/tags"


class Buhitter(BuhitterConfig):
    def __init__(self, sessionId):
        BuhitterConfig.__init__(self)
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "User-Agent": "GochiiraBot/1.0.0 (mail:dsgamer777@gmail.com)",
            "Note": "I am bot. I crawl once per 1 hour. Please contact to dsgamer777@gmail.com to stop crawl.",
            "Referer": "https://buhitter.com/ja/tags"
        }
        self.cookies = {
            "PHPSESSID": sessionId
        }

    def searchIllust(self, tag, friend=0, pageID=1):
        resp = requests.get(
            f"{self.TAGS_ENDPOINT}/{tag}?friend={friend}&offset={(pageID-1)*30}",
            headers=self.headers,
            cookies=self.cookies
        )
        page = lxml.html.fromstring(resp.text)
        tweet_titles = page.xpath(
            '//div[@class="card-body"]/p[1]'
        )
        tweet_titles = [
            t.text_content()
            for t in tweet_titles
        ]
        tweet_links = page.xpath(
            '//div[@class="imagesContainer"]/div[1]/a/@href'
        )
        tweet_usernames = page.xpath(
            '//a[@class="account-link username"]/text()'
        )
        return [
            {
                "tweet_id": tweet_links[i].split("/")[-1],
                "user_id": tweet_links[i].split("/")[3],
                "user_name": tweet_usernames[i],
                "text": tweet_titles[i],
                "link": tweet_links[i]
            }
            for i in range(len(tweet_links))
        ]


if __name__ == "__main__":
    cl = Buhitter("t0j758p4pc0jtqn48roq9q8vjg")
    print(cl.searchIllust("ごちうさ", friend=1))
