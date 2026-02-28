#!/usr/bin/env python3

import json
import datetime
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / 'data'
KB = ROOT / 'knowledge'
CONTENT_QUEUE = ROOT / 'content' / 'queue'

def fetch_unhcr_data():
    try:
        url = 'https://data.unhcr.org/api/stats/summary'
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        return data
    except Exception as e:
        print(f'[unhcr_data_inspector] Error fetching UNHCR data: {e}')
        return None

def extract_refugee_data(data):
    try:
        refugee_data = []
        for country in data['countries']:
            refugee_data.append({
                'country': country['name'],
                'refugee_population': country['refugee_population'],
                'asylum_seekers': country['asylum_seekers'],
                'stateless_persons': country['stateless_persons']
            })
        return refugee_data
    except Exception as e:
        print(f'[unhcr_data_inspector] Error extracting refugee data: {e}')
        return None

def save_refugee_data(data):
    try:
        with open(DATA / 'unhcr_data.json', 'w') as f:
            json.dump(data, f, indent=4)
        print(f'[unhcr_data_inspector] Saved refugee data to {DATA / "unhcr_data.json"}')
    except Exception as e:
        print(f'[unhcr_data_inspector] Error saving refugee data: {e}')

def generate_refugee_insights(data):
    try:
        insights = []
        for country in data:
            insights.append(f'{country["country"]}: {country["refugee_population"]} refugees, {country["asylum_seekers"]} asylum seekers, {country["stateless_persons"]} stateless persons')
        return insights
    except Exception as e:
        print(f'[unhcr_data_inspector] Error generating refugee insights: {e}')
        return None

def save_refugee_insights(insights):
    try:
        with open(KB / 'refugee_insights.md', 'w') as f:
            for insight in insights:
                f.write(insight + '\n')
        print(f'[unhcr_data_inspector] Saved refugee insights to {KB / "refugee_insights.md"}')
    except Exception as e:
        print(f'[unhcr_data_inspector] Error saving refugee insights: {e}')

def generate_social_content(insights):
    try:
        social_content = []
        for insight in insights:
            social_content.append({
                'platform': 'all',
                'type': 'text',
                'text': insight
            })
        return social_content
    except Exception as e:
        print(f'[unhcr_data_inspector] Error generating social content: {e}')
        return None

def save_social_content(content):
    try:
        with open(CONTENT_QUEUE / 'refugee_posts.json', 'w') as f:
            json.dump(content, f, indent=4)
        print(f'[unhcr_data_inspector] Saved social content to {CONTENT_QUEUE / "refugee_posts.json"}')
    except Exception as e:
        print(f'[unhcr_data_inspector] Error saving social content: {e}')

def run():
    print(f'[unhcr_data_inspector] Running UNHCR Data Inspector')
    data = fetch_unhcr_data()
    if data:
        refugee_data = extract_refugee_data(data)
        if refugee_data:
            save_refugee_data(refugee_data)
            insights = generate_refugee_insights(refugee_data)
            if insights:
                save_refugee_insights(insights)
                social_content = generate_social_content(insights)
                if social_content:
                    save_social_content(social_content)

if __name__ == '__main__':
    run()