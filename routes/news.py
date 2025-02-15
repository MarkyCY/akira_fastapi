import ast
from fastapi import APIRouter, Depends
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from funcs.users import get_current_active_user
from pydantic import BaseModel
from typing import Annotated
from models.users import User

import json
import re
import requests
import xml.etree.ElementTree as ET

load_dotenv()

News = APIRouter()

class New(BaseModel):
    id: int
    ttl: str
    lnk: str
    publ: str
    updt: str
    summ: str
    catgy: list

@News.get("/news", response_model=list[New])
def get_news(current_user: Annotated[User, Depends(get_current_active_user)]):
    response = requests.get("https://www.animenewsnetwork.com/news/atom.xml?ann-edition=w")
    xml_data = response.text
    
    root = ET.fromstring(xml_data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    translator = GoogleTranslator(source='en', target='es')

    entries = []
    all_entries = root.findall('atom:entry', ns)
    for entry in all_entries[:10]:
        id = entry.find('atom:id', ns).text
        id_clean = int(re.sub(r"https://www.animenewsnetwork.com/cms/.", "", id))

        title = entry.find('atom:title', ns).text
        title_clean = re.sub(r"This Week in Anime - ", "", title)

        link = entry.find('atom:link', ns).attrib['href']
        summary = entry.find('atom:summary', ns).text

        published = entry.find('atom:published', ns).text
        updated = entry.find('atom:updated', ns).text
        categories = entry.findall('atom:category', ns) 
        category_terms = [category.attrib['term'] for category in categories]

        entries.append({
            'id': id_clean,
            'ttl': title_clean.replace('"', "").replace("'", ""),
            'lnk': link,
            'publ': published,
            'updt': updated,
            'summ': summary.replace('"', "").replace("'", ""),
            'catgy': category_terms
        })
    
    texts_to_translate = [f"{entry['ttl']}|||{entry['summ']}|||{'|'.join(entry['catgy'])}" for entry in entries]
    combined_text = ';;;'.join(texts_to_translate)
    translated_text = translator.translate(combined_text)
    translated_entries = [entry.strip("; ") for entry in translated_text.split(';;;')]
    
    for i, translated_entry in enumerate(translated_entries):
        parts = translated_entry.split('|||')
        if len(parts) == 3:
            ttl, summ, catgy = parts
        elif len(parts) == 2:
            ttl, summ, catgy = parts[0], parts[1], ""
        elif len(parts) == 1:
            ttl, summ, catgy = parts[0], "", ""
        else:
            ttl, summ, catgy = "", "", ""
        
        entries[i]['ttl'] = ttl
        entries[i]['summ'] = summ
        #entries[i]['catgy'] = catgy.split('|') if catgy else []
    
    return entries