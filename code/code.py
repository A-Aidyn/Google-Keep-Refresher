import gkeepapi
import requests
from bs4 import BeautifulSoup
import json

values = {'login_page': 'L_P_COMMON'}

needed_cookies = {}

def getParams(url):
    params = url.split("?")[1]
    params = params.split('&')
    answer = {}
    for param in params:
        k, v = param.split('=')[0], param.split('=')[1]
        answer[k] = v
    return answer

def login(s, username, password):
    url = 'http://klms.kaist.ac.kr'
    r = s.get(url, allow_redirects=False)
    needed_cookies.update(r.cookies)

    url = 'http://klms.kaist.ac.kr/sso2/login.php'
    r = s.get(url, cookies=needed_cookies)
    params = getParams(r.url)
    values['user_id'] = username
    values['pw'] = password
    values['param_id'] = params.get('param_id', '')

    url = 'https://iam2.kaist.ac.kr/api/sso/login'
    r = s.post(url, params=values, cookies=needed_cookies)
    needed_cookies.update(r.cookies)
    data = json.loads(r.content)

    url = 'http://klms.kaist.ac.kr/sso2/ssoreturn.php'
    data = {
        'result': r.content,
        'success': "true",
        'user_id': data.get("dataMap", "").get("USER_INFO", "").get("uid", ""),
        'k_uid': data.get("dataMap", "").get("USER_INFO", "").get("kaist_uid", ""),
        'state': data.get("dataMap", "").get("state", "")
    }
    r = requests.post(url, data=data, cookies=needed_cookies, allow_redirects=False)

    needed_cookies['MoodleSession'] = r.cookies.get('MoodleSession', '')
    soup = BeautifulSoup(r.text, 'html.parser')
    ssid_params = {}
    try:
        ssid_params['ssid'] = soup.find("input", {'name': 'ssid'}).get('value')
        ssid_params['zxcv'] = soup.find("input", {'name': 'zxcv'}).get('value')
        ssid_params['url'] = soup.find("input", {'name': 'url'}).get('value')
    except:
        pass

    url = 'http://klms.kaist.ac.kr/local/ubion/sso/sso_login.php'
    r = s.post(url, data=ssid_params, cookies=needed_cookies, allow_redirects=False)
    needed_cookies['MoodleSession'] = r.cookies.get('MoodleSession', '')




def writeNote(keep, content):
    glist = list(keep.find(query='KAIST Homework'))
    if len(glist) == 0:
        glist = keep.createList('KAIST Homework', [])
    else:
        glist = list(glist)[0]
    add = 1
    for item in glist.items:
        if content == item.text:
            add = 0
            break
    if add:
        glist.add(content, False, gkeepapi.node.NewListItemPlacementValue.Top)
    keep.sync()


keep = gkeepapi.Keep()

gusername = input("Please enter your google login: ")
gpassword = input("Please enter your password: ")

print("Logging into google keep")
keep.login(username=gusername, password=gpassword)
print("Success!")


kusername = input("Please enter your kaist username: ")
kpassword = input("Please enter your password: ")

with requests.Session() as s:
    print("Logging into klms")
    login(s, kusername, kpassword)
    print("Success!")

    assignments = []
    announcements = []

    ptr = 0
    params = {'page': '0'}
    changed = 1
    while changed and ptr <= 10:
        print(ptr)
        ptr += 1
        params['page'] = str(ptr)

        url = 'http://klms.kaist.ac.kr/local/ubnotification/index.php'
        r = s.get(url, params=params, cookies=needed_cookies)

        soup = BeautifulSoup(r.content, 'html.parser')

        changed = 0

        for tag in soup.find_all('div', class_='media'):
            try:
                url = tag.find('a').get('href')
                if ('assign' in url) and (url not in assignments):
                    assignments.append(url)
                    changed = 1
                if ('ubboard' in url) and (url not in announcements):
                    announcements.append(url)
                    changed = 1
            except:
                pass

    for url in assignments:
        r = s.get(url, cookies=needed_cookies)
        soup = BeautifulSoup(r.content, 'html.parser')
        try:
            course = soup.find('div', class_='course_name').find('h1').get('title')
            title = soup.find('div').find('h2', class_='main').get_text()

            submission_status_box = soup.find('td', class_='cell c1 lastcol')
            deadline = submission_status_box.find_next('td', class_='cell c1 lastcol').get_text()
        except:
            pass
        writeNote(keep, course + '\n' + title + '\n' + deadline)
    # print("ANNOUNCEMENTS:\n")
    # print([obj for obj in announcements])
print("DONE!!!")

exit()
