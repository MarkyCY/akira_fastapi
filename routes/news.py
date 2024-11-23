import ast
from fastapi import APIRouter, Depends
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from funcs.users import get_current_active_user
from pydantic import BaseModel
from typing import Annotated
from models.users import User

import re
import requests
import xml.etree.ElementTree as ET

load_dotenv()

News = APIRouter()

class New(BaseModel):
    id: int
    title: str
    link: str
    publ: str
    updt: str
    summary: str
    category: list


@News.get("/news", response_model=list[New])
def get_news(current_user: Annotated[User, Depends(get_current_active_user)],):

    response = requests.get("https://www.animenewsnetwork.com/this-week-in-anime/atom.xml?ann-edition=w")
    xml_data = response.text
    
    root = ET.fromstring(xml_data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    translator = GoogleTranslator(source='en', target='es')

    entries = []
    for i, entry in enumerate(root.findall('atom:entry', ns)):
        id = entry.find('atom:id', ns).text
        id_clean = int(re.sub("https://www.animenewsnetwork.com/cms/.", "", id))

        title = entry.find('atom:title', ns).text
        title_clean = re.sub("This Week in Anime - ", "", title)

        link = entry.find('atom:link', ns).attrib['href'] 
        summary = entry.find('atom:summary', ns).text 

        published = entry.find('atom:published', ns).text
        updated = entry.find('atom:updated', ns).text
        categories = entry.findall('atom:category', ns) 
        category_terms = [category.attrib['term'] for category in categories]
        entries.append({
            'id': id_clean,
            'title': title_clean,
            'link': link,
            'publ': published,
            'updt': updated,
            'summary': summary,
            'category': category_terms
        })
        if i >= 9:
            break

    data_string = translator.translate(text=str(entries))
    data_list = ast.literal_eval(data_string)
    return data_list