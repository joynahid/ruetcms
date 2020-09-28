from datetime import datetime
import sys, os, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from bs4 import BeautifulSoup

chrome_driver_path = os.environ['CHROME_DRIVER_PATH']
chrome_bin_path = os.environ['CHROME_BIN']

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.binary_location = chrome_bin_path

webdriver = webdriver.Chrome(
  executable_path=chrome_driver_path, options=chrome_options
)

def insert(contest_id, db):
    try:
        wait = WebDriverWait(webdriver, 10)

        contest_id = str(contest_id)
        selfid = ''
        for i in contest_id:
            if i.isdigit():
                selfid+=i

        selfid = int(selfid)
        uri = 'https://vjudge.net/contest/{}#rank'.format(selfid)

        webdriver.get(uri)

        source = webdriver.page_source
        
        soup = BeautifulSoup(source, 'html.parser')

        webdriver.close()

        title = soup.select('title')[0].text
        author = soup.select('#contest-manager > a')[0].text
        query = '#contest-rank-table > thead:nth-child(2) > tr:nth-child(1) > th'
        numOfProblems = len(soup.select(query)) - 4

        fetchRank = soup.find_all("td", class_=["meta"])
        ranks = []

        for i in range(0,len(fetchRank),4):
            p = []
            
            for j in range(4):
                p.append(fetchRank[i].text)
                i+=1

            # print(p)

            data = {
                'serial' : int(p[0]),
                'vj' : p[1].split(' ')[0],
                'solved' : int(p[2]),
                'penalty' : int(p[3].split(' ')[1].strip())
            }

            ranks.append(data)
        
        ret = {
            'title' : title,
            'author' : author,
            'numOfProblems': numOfProblems,
            'ranks' : ranks
        }

        db.collection('vjudgeContests').document(str(selfid)).set(ret)
    except Exception as e:
        print(e.message)

# insert(376797,4)

def vjInfoQuery(db):
    docs = db.collection('vjudgeContests').limit(5).stream()

    contestInfo = []

    for doc in docs:
        d = doc.to_dict()

        info = {
            'id' : doc.id,
            'title' : d['title'],
            'author' : d['author'],
            'numOfProblems' : d['numOfProblems'],
            'top' : d['ranks'][0]['vj']
        }

        contestInfo.append(info)

    return contestInfo