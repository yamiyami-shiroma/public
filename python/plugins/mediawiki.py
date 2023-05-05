# -*- coding: utf-8 -*-

import datetime
import requests
import json
import html
import re
import random

def GetDayEvents(datetime):
    response = requests.get('https://ja.wikipedia.org/w/api.php?format=json&utf8&action=query&prop=revisions&rvprop=content&titles='+datetime)
    response_dict = json.loads(response.text)
    page_id = "0"
    response_pages = response_dict["query"]["pages"]
    for id in response_pages.keys():
        page_id = id
        break
    
    revisions_txt = response_pages[page_id]["revisions"][0]["*"].replace('[','').replace(']','').replace('（','').replace('）','')
    #result = re.sub(r'<ref.*?</ref>', '', revisions_txt, flags=re.DOTALL)  # タグを削除
    #revisions_txt = result
	
    dekigoto = re.search(r'== 記念日・年中行事 ==[\s\S]*== フィクションのできごと ==', revisions_txt)
    events = re.findall(r'\*.+\n', re.sub(r'<ref.*?</ref>', '', dekigoto.group(), flags=re.DOTALL) .replace("\n*:","[D]"))

    response_event_list = []
    for event in events:
        if '{{JPN}}' in event and 'の日' in event and '[D]' in event and 'ref' not in event:
            response_event_list.append(event.replace("*","").replace("{{JPN}}",""))

    if len(response_event_list) == 0:
        response_event_list.append("なんの日か[D]分からないのだ")
    
    response = random.sample(response_event_list, len(response_event_list))[0]
    
    return response


