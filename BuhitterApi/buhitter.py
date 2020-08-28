import requests
import lxml.html
import json


class BuhitterConfig():
    BUHITTER_ENDPOINT = "https://buhitter.com"
    TAGS_ENDPOINT = f"{BUHITTER_ENDPOINT}/ja/tags"


class Buhitter(BuhitterConfig):
    def __init__(self, sessionId=None, twitterCookies=""):
        BuhitterConfig.__init__(self)
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
            "Referer": "https://buhitter.com/ja/tags"
        }
        self.cookies = {}
        if sessionId:
            self.cookies["PHPSESSID"] = sessionId
        if twitterCookies:
            self.twitterCookies = twitterCookies

    def login(self):
        # セッションID / CSRFの取得
        resp = requests.get("https://buhitter.com/login", headers=self.headers)
        page = lxml.html.fromstring(resp.text)
        csrf = page.xpath('//meta[@name="csrf-token"]/@content')[0]
        sessionId = resp.headers["Set-Cookie"].split("=")[1].split(";")[0]
        self.cookies["PHPSESSID"] = sessionId
        self.headers["Referer"] = "https://buhitter.com/login"
        resp = requests.post(
            "https://buhitter.com/twitter/login",
            data={"csrf": csrf},
            headers=self.headers,
            cookies=self.cookies
        )
        # Twitterにログイン (Buhitterのクッキーはself.cookiesに入っている)
        self.headers["Cookie"] = self.twitterCookies
        twitter_auth_address = resp.history[0].headers["Location"]
        resp = requests.get(
            twitter_auth_address,
            headers=self.headers
        )
        page = lxml.html.fromstring(resp.text)
        del self.headers["Cookie"]
        authorizated_address = page.xpath('//meta[@http-equiv="refresh"]/@content')[0].split("url=")[1]
        self.headers["Referer"] = authorizated_address.split("&")[0]
        # Buhitterにログイン
        resp = requests.get(
            authorizated_address,
            headers=self.headers,
            cookies=self.cookies
        )
        self.headers["Note"] = "I am bot. I crawl once per 1 hour. Please contact to dsgamer777@gmail.com to stop crawl."
        self.headers["User-Agent"] = "GochiiraBot/1.0.0 (mail:dsgamer777@gmail.com)"
        self.cookies["al"] = resp.headers["Set-Cookie"].split(";")[0].split("al=")[1]
        print(f"Login success: {sessionId}")
        return sessionId

    def searchIllust(self, tag, friend=0, pageID=1):
        self.headers["Referer"] = "https://buhitter.com/ka/tags"
        resp = requests.get(
            f"{self.TAGS_ENDPOINT}/{tag}?friend={friend}&offset={(pageID-1)*30}",
            headers=self.headers,
            cookies=self.cookies
        )
        if friend and "マイページ" not in resp.text:
            return {}
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

    def isLogined(self):
        resp = requests.get("https://buhitter.com/", cookies=self.cookies, headers=self.headers)
        if "マイページ" in resp.text:
            return True
        else:
            return False


if __name__ == "__main__":
    cl = Buhitter(twitterCookies='_')
    cl.login()
    print(cl.searchIllust("香風智乃",friend=1))