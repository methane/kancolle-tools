# coding: utf-8
from __future__ import print_function

import sys
import random
import requests
import json
import time

class NotExpectedResult(Exception):
    pass


class Client(object):
    prefix = 'http://203.104.105.167/kcsapi'

    def __init__(self, token):
        self.session = requests.session()
        self.session.headers.update({
            'Uesr-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36',
            'Origin': 'http://203.104.105.167',
            'Referer': 'http://203.104.105.167/kcs/port.swf?version=1.2.0',})
        self.base_data = {'api_verno': 1, 'api_token': token}

    def call(self, path, data=None):
        if data is None:
            data = {}
        data.update(self.base_data)
        res = self.session.post(self.prefix + path, data)
        res.raise_for_status()
        resdata = res.text
        if not resdata.startswith('svdata='):
            raise NotExpectedResult(resdata)
        resjson = json.loads(resdata[7:])
        if resjson['api_result'] != 1:
            raise NotExpectedResult(resdata)
        return resjson


def find_free_dock(docks):
    for d in docks:
        if d['api_state'] == 0:
            return d['api_id']
    return None


def find_repairable(member, decks, docks):
    cant_repair = set()

    # 編成されてる艦を入渠するとバレるのでしない.
    for deck in decks:
        cant_repair.update(deck['api_ship'])

    # 修理中の艦ももちろん入渠しない.
    for dock in docks:
        cant_repair.add(dock['api_ship_id'])

    # ランダムで入渠させる.
    # TODO: luckey が高いやつ優先とかしたい
    random.shuffle(member)
    for ship in member:
        #print(ship)
        if ship['api_nowhp'] >= ship['api_maxhp']:
            continue
        ship_id = ship['api_id']
        if ship_id in cant_repair:
            continue
        return ship_id
    return None


def repair(client):
    ndock = client.call('/api_get_member/ndock')
    ship2 = client.call('/api_get_member/ship2',
                        {'api_sort_order': 2, 'api_sort_key': 1})

    dock_no = find_free_dock(ndock['api_data'])
    ship_id = find_repairable(ship2['api_data'], ship2['api_data_deck'], ndock['api_data'])
    print('dock_no=', dock_no, ' ship_id=', ship_id)
    if ship_id is None:
        sys.exit()

    if dock_no and ship_id:
        # TODO: 修理時間が8時間超える場合は高速修理アイテム使う
        client.call('/api_req_nyukyo/start',
                    {'api_ship_id': ship_id,
                     'api_ndock_id': dock_no,
                     'api_highspeed': 0})

def main():
    client = Client(sys.argv[1])
    while True:
        repair(client)
        time.sleep(123)


if __name__ == '__main__':
    main()
