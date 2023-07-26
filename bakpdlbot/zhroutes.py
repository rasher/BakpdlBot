#!/usr/bin/env python3
import sys
from pprint import pprint
from bs4 import BeautifulSoup


def route_info(route_div):
    worlds = {
            1: 'WATOPIA',
            2: 'RICHMOND',
            3: 'LONDON',
            4: 'NEWYORK',
            5: 'INNSBRUCK',
            6: 'BOLOGNATT',
            7: 'YORKSHIRE',
            8: 'CRITCITY',
            9: 'MAKURIISLANDS',
            10: 'FRANCE',
            11: 'PARIS',
            12: 'GRAVEL MOUNTAIN',
            13: 'SCOTLAND',
            }
    world_ids = {v: k for k, v in worlds.items()}

    keys = [
            ('id', int),
            ('route', str),
            ('eventonly', lambda s: s != '-'),
            ('totaldistance', int),
            ('world', str),
            ('ascent', int)
            ]
    info = {k: f(route_div.select_one('div.secret.ze-col-'+k).text.strip()) for k, f in keys}
    additional = {
        'leadindistance': int(1000*float(route_div.select_one('div.ze-col-leadindistance').attrs['data-dist-km'].replace(' km', ''))),
        'worldid': world_ids[info['world']],
    }
    additional['lapdistance'] = info['totaldistance'] - additional['leadindistance']
    #info['div'] = route_div
    info.update(additional)
    return info


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'get':
        import requests
        url = 'https://zwifthacks.com/app/routes'
        routesHtml = requests.get(url, headers={'User-agent': 'zhroutes-list'}).text
    else:
        with open('routes.html') as fp:
            routesHtml = fp.read()

    soup = BeautifulSoup(routesHtml, 'html5lib')

    route_divs = soup.select('#dataTable .item')
    routes = [route_info(route_div) for route_div in route_divs]
    routes = {r['id']: r for r in routes}

    pprint(routes)


if __name__ == "__main__":
    main()
