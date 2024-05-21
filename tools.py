import os
import json
import requests
from bs4 import BeautifulSoup

SERPER_API_KEY = os.getenv('SERPER_API_KEY')

def scrape_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    body_text = soup.body.get_text(separator=' ', strip=True)

    return body_text

def request_serper_api(topic: str) -> str:
  url = "https://google.serper.dev/search"
  params = json.dumps({
    "q": f"{topic} news"
  })

  headers = {
    'X-API-KEY': SERPER_API_KEY,
    'Content-Type': 'application/json'
  }

  response = requests.request("POST", url, headers=headers, data=params)
  data = response.json()

  top_stories = {"top_stories": data.get("topStories")}
  # top_stories_json = json.dumps(top_stories, indent=4)

  retrieved_lst = []
  for entry in top_stories['top_stories']:
      title = entry['title']
      url = entry['link']

      article_text = scrape_data(url)

      article = {
        "title": title,
        "source": url.split('.com')[0] + '.com',
        "text": article_text[max(0, len(article_text) // 2 - 500):][:1000]
      }

      retrieved_lst.append(article)

  top_stories_json = json.dumps({"top_stories": retrieved_lst}, indent=4)

  return top_stories_json