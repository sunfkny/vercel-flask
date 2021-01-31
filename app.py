from flask import Flask, render_template, request
import markdown
import requests
import json
import urllib

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, world"


@app.route("/gge")
def test():
    url = str(request.args.get("url"))
    return render_template("gge.html", url=url)


# @app.route("/result")
# def result():
#     dict = {"phy": 50, "che": 60, "maths": 70}
#     return render_template("result.html", result=dict)


@app.route("/ggeapi")
def ggeapi():
    def getGachaTypes():
        r = requests.get(url.replace("getGachaLog", "getConfigList"))
        s = r.content.decode("utf-8")
        configList = json.loads(s)
        gachaTypeLists = []
        return configList["data"]["gacha_type_list"]

    def getGachaLogs(gachaTypeId):
        size = "20"
        # api限制一页最大20
        gachaList = []
        for page in range(1, 9999):
            api = getApi(gachaTypeId, size, page)
            r = requests.get(api)
            s = r.content.decode("utf-8")
            j = json.loads(s)

            gacha = j["data"]["list"]
            if not len(gacha):
                break
            for i in gacha:
                gachaList.append(i)
        return gachaList

    def getApi(gachaType, size, page):
        parsed = urllib.parse.urlparse(url)
        querys = urllib.parse.parse_qsl(parsed.query)
        param_dict = dict(querys)
        param_dict["size"] = size
        param_dict["gacha_type"] = gachaType
        param_dict["page"] = page
        param = urllib.parse.urlencode(param_dict)
        path = url.split("?")[0]
        api = path + "?" + param
        return api

    def getQueryVariable(variable):
        query = url.split("?")[1]
        vars = query.split("&")
        for v in vars:
            if v.split("=")[0] == variable:
                return v.split("=")[1]
        return ""

    def getGachaInfo():
        region = getQueryVariable("region")
        lang = getQueryVariable("lang")
        gachaInfoUrl = "https://webstatic.mihoyo.com/hk4e/gacha_info/{}/items/{}.json".format(region, lang)
        r = requests.get(gachaInfoUrl)
        s = r.content.decode("utf-8")
        gachaInfo = json.loads(s)
        return gachaInfo

    def getInfoByItemId(item_id, gachaInfo):
        for info in gachaInfo:
            if item_id == info["item_id"]:
                return info["name"], info["item_type"], info["rank_type"]
        return

    url = str(request.values.get("url"))
    if "getGachaLog" not in url:
        return {"message": "no getGachaLog in url", "url": url}
    try:
        r = requests.get(url)
        s = r.content.decode("utf-8")
        j = json.loads(s)
        if not j["data"]:
            return {"message": j["message"], "url": url}
    except Exception as e:
        return {"message": str(e), "url": url}
    gachaInfo = getGachaInfo()
    gachaTypes = getGachaTypes()
    gachaTypeIds = [banner["key"] for banner in gachaTypes]
    gachaTypeNames = [banner["name"] for banner in gachaTypes]
    gachaTypeDict = dict(zip(gachaTypeIds, gachaTypeNames))
    gachaData = {}
    gachaData["gachaType"] = gachaTypes
    gachaData["gachaInfo"] = gachaInfo
    gachaData["gachaLog"] = {}
    for gachaTypeId in gachaTypeIds:
        gachaLog = getGachaLogs(gachaTypeId)
        gachaData["gachaLog"][gachaTypeId] = gachaLog

    uid_flag = 1
    for gachaType in gachaData["gachaLog"]:
        for log in gachaData["gachaLog"][gachaType]:
            if uid_flag and log["uid"]:
                gachaData["uid"] = log["uid"]
                uid_flag = 0
            # del log["uid"]
            # del log["count"]
            # del log["gacha_type"]

    uid = gachaData["uid"]
    gachaInfo = gachaData["gachaInfo"]
    gachaTypes = gachaData["gachaType"]
    gachaLog = gachaData["gachaLog"]
    gachaTypeIds = [banner["key"] for banner in gachaTypes]
    gachaTypeNames = [key["name"] for key in gachaTypes]
    gachaTypeDict = dict(zip(gachaTypeIds, gachaTypeNames))
    gachaTypeReverseDict = dict(zip(gachaTypeNames, gachaTypeIds))

    markdown_body = f"""# UID: {uid} 的抽卡报告"""
    for gechaType in gachaTypeIds:
        gachaS5Data = []
        gachaS4Data = []
        gachaS3Data = []
        for gacha in gachaLog[gechaType]:
            item_id = gacha["item_id"]
            time = gacha["time"]
            name, item_type, rank_type = getInfoByItemId(item_id, gachaInfo)
            if rank_type == "5":
                gachaS5Data.append([time, item_id, name, item_type, rank_type])
            if rank_type == "4":
                gachaS4Data.append([time, item_id, name, item_type, rank_type])
            if rank_type == "3":
                gachaS3Data.append([time, item_id, name, item_type, rank_type])
        numS5 = len(gachaS5Data)
        numS4 = len(gachaS4Data)
        numS3 = len(gachaS3Data)
        if not (numS5 + numS4 + numS3):
            continue
        total = len(gachaLog[gechaType])
        gachaS5DataStatistics = {}
        for i in gachaInfo:
            gachaS5DataStatistics[i["item_id"]] = 0
        for s in gachaS5Data:
            gachaS5DataStatistics[s[1]] += 1
        gachaS4DataStatistics = {}
        for i in gachaInfo:
            gachaS4DataStatistics[i["item_id"]] = 0
        for s in gachaS4Data:
            gachaS4DataStatistics[s[1]] += 1
        gachaS3DataStatistics = {}
        for i in gachaInfo:
            gachaS3DataStatistics[i["item_id"]] = 0
        for s in gachaS3Data:
            gachaS3DataStatistics[s[1]] += 1

        gachaName = gachaTypeDict[gechaType]
        gachaS5Info = ""
        gachaS4Info = ""
        gachaS3Info = ""
        for k, v in gachaS5DataStatistics.items():
            if v:
                name, item_type, rank_type = getInfoByItemId(k, gachaInfo)
                gachaS5Info += f"  {rank_type}星{item_type}  {name}  数量:{v}\n"
        for k, v in gachaS4DataStatistics.items():
            if v:
                name, item_type, rank_type = getInfoByItemId(k, gachaInfo)
                gachaS4Info += f"  {rank_type}星{item_type}  {name}  数量:{v}\n"
        for k, v in gachaS3DataStatistics.items():
            if v:
                name, item_type, rank_type = getInfoByItemId(k, gachaInfo)
                gachaS3Info += f"  {rank_type}星{item_type}  {name}  数量:{v}\n"
        gachaTable = f"""| 星级 | 数量 | 占比   |
| ---- | ---- | -------- |
| 5星  | {numS5} | {round(numS5*100/total,2)}% |
| 4星  | {numS4} | {round(numS4*100/total,2)}% |
| 3星  |{numS3} | {round(numS3*100/total,2)}% |
| 总计 | {total} | 100.0% |"""

        gachaReport = f"""
## {gachaName}
{gachaTable}
<details>
<summary>详情</summary>
<br>
<details>
<summary>5星</summary>
```
{gachaS5Info}
```
</details>
<details>
<summary>4星</summary>
```
{gachaS4Info}
```
</details>
<details>
<summary>3星</summary>
```
{gachaS3Info}
```
</details>
</details>
"""
        markdown_body += gachaReport
    markdown_render = markdown.markdown(markdown_body, extensions=["markdown.extensions.tables", "markdown.extensions.fenced_code"])
    return markdown_render


if __name__ == '__main__':
    app.run(debug=True, threaded=True,port="8088")