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

    response = requests.get("https://www.animenewsnetwork.com/this-week-in-anime/atom.xml?ann-edition=w")
    xml_data = response.text
    
    root = ET.fromstring(xml_data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    translator = GoogleTranslator(source='en', target='es')

    entries = []
    # Obtén todos los elementos 'atom:entry'
    all_entries = root.findall('atom:entry', ns)
    # Itera desde el final hacia el principio, tomando los últimos 10 elementos
    for entry in all_entries[-10:]:
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
            'ttl': title_clean.replace('"', "'"),
            'lnk': link,
            'publ': published,
            'updt': updated,
            'summ': summary.replace('"', "'"),
            'catgy': category_terms
        })

    # Serializa las entradas a JSON
    data_json = json.dumps(entries, ensure_ascii=False)
    # Traduce el JSON serializado
    translated_json = translator.translate(data_json)
    # Deserializa el JSON traducido
    data_list = json.loads(translated_json)
    return data_list
