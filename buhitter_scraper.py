from BuhitterApi.buhitter import Buhitter
from datetime import datetime
from shortid import ShortId
from random import uniform
from time import sleep
import emoji
import traceback
import requests
import os.path
import json
import re

#
# Buhitterスクレイピング
#
# 1. 最後に取得したIDを読み出す(ないなら取得したページの末尾を最後扱い)
# 2. 最後に取得したIDが見つかるまでイラスト情報を取得する
# 3. 取得したイラスト情報を元に 枚数が4枚以下のイラストのみ登録する
#    (それ以外はまとめイラストの可能性がある)
# 4. 1時間待つ
#
#


class Scrapper():
    # 設定ファイルを読み込む
    def __init__(self, file_name="settings.json"):
        try:
            with open(file_name, "r", encoding="utf8") as f:
                self.settings = json.loads(f.read())
            self.sid = ShortId()
        except IOError:
            self.settings = {
                "long_wait": {
                    "min": 60*60*1,
                    "max": 60*60*1
                },
                "short_wait": {
                    "min": 5,
                    "max": 10
                },
                "gochiira_auth": {
                    "api_key": "Bearer hoge"
                },
                "buhitter_auth": {
                    "session": "",
                    "twitter_cookie": ""
                },
                "deep_ai_auth": {
                    "api_key": ""
                },
                "search": {
                    "keyword": "ごちうさ"
                },
                "add_tags": {
                    "チノ": ['香風智乃'],
                    "シャロ": ['桐間紗路'],
                    "ココア": ['保登心愛'],
                    "リゼ": ['天々座理世'],
                    "千夜": ['宇治松千夜'],
                    "マヤ": ['条河麻耶'],
                    "メグ": ['奈津恵'],
                    "チマメ": ['チマメ隊', '条河麻耶', '奈津恵', '香風智乃'],
                    "ココチノ": ['保登心愛', '香風智乃', 'ココチノ'],
                    "チノココ": ['保登心愛', '香風智乃', 'チノココ'],
                    "クロックワーク": ['クロラビ'],
                    "クロラビ": ['クロラビ'],
                    "リプラビ": ['リプラビ'],
                    "きららファンタジア": ['きららファンタジア'],
                    "きらファン": ['きららファンタジア'],
                    "水着": ['水着'],
                    "ネコミミ": ['猫耳'],
                    "猫耳": ['猫耳'],
                    "ねこみみ": ['猫耳'],
                    "ラフ": ['ラフ'],
                    "らくがき": ['らくがき'],
                    "ラクガキ": ['らくがき'],
                    "わんどろ": ['ワンドロ'],
                    "ワンドロ": ['ワンドロ'],
                    "制服": ['制服'],
                    "アリス": ['アリス'],
                    "魔法少女": ['魔法少女'],
                    "魔法少女チノ": ['魔法少女チノ', '魔法少女'],
                    "は誕生日": ['誕生日'],
                    "生誕祭": ['誕生日'],
                    "差分": ['差分']
                },
                "remove_tags": [
                    'gochiusa',
                    'ごちうさ',
                    'ご注文はうさぎですか',
                    'ご注文はうさぎですか?',
                    'R-18',
                    'R18',
                    'チノ',
                    'チノちゃん',
                    'シャロ',
                    'ココア',
                    'リゼ',
                    '千夜',
                    'マヤ',
                    'メグ'
                ],
                "ng_artists": [],
                "last_scraped_id": 0
            }
        self.cl = Buhitter(
            sessionId=self.settings["buhitter_auth"]["session"],
            twitterCookies=self.settings["buhitter_auth"]["twitter_cookies"]
        )
        if not self.cl.isLogined():
            self.settings["buhitter_auth"]["session"] = self.cl.login()

    def uploadIllust(self, link):
        # ツイート情報が揃っていないのでAPIを呼ぶ
        illustData = requests.post(
            "https://api.gochiusa.team/scrape/twitter",
            json={
                "url": link
            },
            headers={
                "Authorization": self.settings["gochiira_auth"]["api_key"]
            }
        ).json()["data"]
        # アップロード用変数を組み立てる
        illustTitle = illustData['illust']['title']
        if illustData['illust']['title'] == "":
            illustTitle = "(無題)"
        illustCaption = illustData['illust']['caption']
        illustCount = len(illustData['illust']['imgs'])
        illustTag = illustData['illust']['tags']
        illustGroup = []
        illustNsfw = self.isNsfw(illustData['illust']['imgs'][0]["large_src"])
        artistName = illustData['user']['name']
        # 登録の終了
        if illustData['illust']['id'] == self.settings["last_scraped_id"]:
            return "end"
        # イラスト枚数は最大でも4枚なのでスキップ処理はしない
        # NGワードを削除
        ngWords = [' ', '　']
        for tag in illustTag + self.settings["remove_tags"]:
            ngWords.append('#' + tag)
            ngWords.append('＃' + tag)
        for n in ngWords:
            illustData['illust']['title'] = illustData['illust']['title'].replace(n, "")
            illustCaption = illustCaption.replace(n, "")
        # 絵師名の加工
        artistName = artistName.split('@')[0]
        artistName = artistName.split('＠')[0]
        artistName = artistName.replace('お仕事募集中', '')
        artistName = ''.join(
            c for c in artistName if c not in emoji.UNICODE_EMOJI
        )
        # タイトルが短い場合は説明文無し
        if len(illustTitle) < 20:
            illustCaption = ""
        # タイトルが長い場合は途中で切る
        # FIXME: 改行の処理が下手
        else:
            illustData['illust']['title'] = illustTitle.split("\n")[0]
            if len(illustData['illust']['title']) > 30:
                illustData['illust']['title'] = illustTitle[:27] + "..."
            else:
                illustCaption = "\n".join(illustCaption.split("\n")[1:])
            illustCaption = re.sub(r"\n+", "\n", illustCaption)
            if illustCaption[-1:] == "\n":
                illustCaption = illustCaption[:-1]
            if illustCaption[:1] == "\n":
                illustCaption = illustCaption[1:]
        # タイトルからタグ挿入
        for t in self.settings["add_tags"].keys():
            if t in illustTitle:
                illustTag.extend(self.settings["add_tags"][t])
        # 重複タグ除去
        illustTag = list(set(illustTag) - set(self.settings["remove_tags"]))
        # システムタグを挿入
        if illustCount > 1:
            illustGroup.append(self.sid.generate())
        if illustNsfw:
            illustTag.append("R18")
        illustTag.append(
            datetime.now().strftime("%Y-%m").replace('-', '年') + '月'
        )
        # イラスト枚数分繰り返す
        for i in range(illustCount):
            illustTitle = illustData['illust']['title']
            illustTitle = illustTitle if i == 0 else f"{illustTitle}({i+1})"
            illustUrl = f"{link}?page={i+1}"
            data = {
                "title": illustTitle,
                "caption": illustCaption,
                "originUrl": illustUrl,
                "originService": "Twitter",
                "imageUrl": illustUrl,
                "artist": {
                    "twitterID": illustData['user']['screen_name'],
                    "name": artistName
                },
                "tag": illustTag,
                "group": illustGroup,
                "chara": [],
                "system": [],
                "nsfw": illustNsfw
            }
            print(data)
            resp = requests.post(
                "https://api.gochiusa.team/arts",
                json=data,
                headers={
                    "Authorization": self.settings["gochiira_auth"]["api_key"]
                }
            )
            print(resp.text)
            self.waitShort()
        return True

    def isNsfw(self, twitter_thumb_url):
        try:
            r = requests.post(
                "https://api.deepai.org/api/nsfw-detector",
                data={
                    'image': twitter_thumb_url,
                },
                headers={
                    'api-key': self.settings["deep_ai_auth"]["api_key"]
                }
            ).json()
            score = r["output"]["nsfw_score"]
            if score > 0.3:
                return True
            else:
                return False
        except:
            print("WARN: API limit exceeded.")
            return True

    def waitLong(self):
        waitTime = uniform(
            self.settings["long_wait"]["min"],
            self.settings["long_wait"]["max"]
        )
        print(f"LongWait: {round(waitTime,1)}s")
        sleep(waitTime)

    def waitShort(self):
        waitTime = uniform(
            self.settings["short_wait"]["min"],
            self.settings["short_wait"]["max"]
        )
        print(f"ShortWait: {round(waitTime,1)}s")
        sleep(waitTime)

    def main(self):
        while True:
            # 初期値を入力
            pageID = 1
            loopFlag = True
            while loopFlag:
                # 検索する
                print("Fetch illusts...")
                searchResult = self.cl.searchIllust(
                    tag=self.settings["search"]["keyword"],
                    friend=1,
                    pageID=pageID
                )
                print(searchResult)
                if searchResult == {}:
                    self.settings["buhitter_auth"]["session"] = self.cl.login()
                    continue
                # 最新のイラストIDを取得
                if pageID == 1:
                    newestID = max(
                        [int(i["tweet_id"]) for i in searchResult]
                    )
                    # 最終取得IDが0ならループ強制終了
                    if self.settings["last_scraped_id"] == 0:
                        loopFlag = False
                        self.settings["last_scraped_id"] = newestID
                # 投稿する
                print("Upload illusts...")
                for illust in searchResult:
                    print(f"ID:{illust['tweet_id']}")
                    resp = self.uploadIllust(illust["link"])
                    resp = "end"
                    if resp == "skip":
                        continue
                    elif resp == "end":
                        loopFlag = False
                        self.settings["last_scraped_id"] = newestID
                        break
                # 次のページへ行く
                pageID += 1
                # 現在の状況を書き込む
                with open("settings.json", "w", encoding="utf8") as f:
                    f.write(
                        json.dumps(
                            self.settings,
                            indent=4,
                            ensure_ascii=False
                        )
                    )
            # 1時間待機する
            self.waitLong()


if __name__ == "__main__":
    s = Scrapper("settings.json")
    s.main()
