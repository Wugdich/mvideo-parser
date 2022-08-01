import requests
import json
from datetime import datetime
import os
import math
import pandas as pd

from config import cookies, headers


class ProductNotFoundError(Exception):
    """
    Raise when product id didn't find in json data.
    """
    def __init__(self, product_id: str, 
            message='Product id didnt found in json data'):
        self._product_id = product_id
        self._message = f'{message} (id - {self._product_id}).'
        super().__init__(self._message)


class NoItemsError(Exception):
    """
    Raise when total count of items equal zero.
    """
    def __init__(self, message='No items.'):
        self._message = message
        super().__init__(self._message)


def get_data() -> None:


    params = {
        'categoryId': '205',
        'offset': '0',
        'limit': '24',
        'filterParams': [
            'WyJza2lka2EiLCIiLCJkYSJd',
            'WyJ0b2xrby12LW5hbGljaGlpIiwiIiwiZGEiXQ==',
        ],
        'doTranslit': 'true',
    }

    if not os.path.exists('data'):
        os.mkdir('data')

    session = requests.Session()
    response = session.get('https://www.mvideo.ru/bff/products/listing', params=params, cookies=cookies, headers=headers).json()

    # Get items counts to calculate page numbers.
    total_items = response.get('body').get('total')
    if total_items is None:
        raise NoItemsError()
    pages_count = math.ceil(total_items / 24)
    print(f'[INFO] Total positions - {total_items}. Total pages - {pages_count}.')
    
    products_ids = {}
    products_description = {}
    products_prices = {}

    for i in range(pages_count):
        offset = f'{i * 24}'

        params = {
            'categoryId': '205',
            'offset': offset,
            'limit': '24',
            'filterParams': [
                'WyJza2lka2EiLCIiLCJkYSJd',
                'WyJ0b2xrby12LW5hbGljaGlpIiwiIiwiZGEiXQ==',
            ],
            'doTranslit': 'true',
        }

        response = session.get('https://www.mvideo.ru/bff/products/listing', params=params, cookies=cookies, headers=headers).json()
        products_ids_list = response.get('body').get('products')
        products_ids[i] = products_ids_list

        json_data = {
            'productIds': products_ids_list,
            'mediaTypes': [
                'images',
            ],
            'category': True,
            'status': True,
            'brand': True,
            'propertyTypes': [
                'KEY',
            ],
            'propertiesConfig': {
                'propertiesPortionSize': 5,
            },
            'multioffer': False,
        }

        response = session.post('https://www.mvideo.ru/bff/product-details/list', 
                cookies=cookies, headers=headers, json=json_data).json()
        products_description[i] = response

        products_ids_str = ','.join(products_ids_list)
        params = {
            'productIds': products_ids_str,
            'addBonusRubles': 'true',
            'isPromoApplied': 'true',
        }

        response = session.get('https://www.mvideo.ru/bff/products/prices', 
                params=params, cookies=cookies, headers=headers).json()
        material_prices = response.get('body').get('materialPrices')

        for item in material_prices:
            item_id = item.get('productId')
            item_base_price = item.get('price').get('basePrice')
            item_sale_price = item.get('price').get('salePrice')
            item_bonus = item.get('bonusRubles').get('total')

            products_prices[item_id] = {
                    'item_basePrice': item_base_price,
                    'item_salePrice': item_sale_price,
                    'item_bonus': item_bonus
                    }

        print(f'[+] Finished {i + 1} of the {pages_count} pages.')

    with open('data/product_ids.json', 'w') as file:
        json.dump(products_ids, file, indent=4, ensure_ascii=False)

    with open('data/product_description.json', 'w') as file:
        json.dump(products_description, file, indent=4, ensure_ascii=False)

    with open('data/product_prices.json', 'w') as file:
        json.dump(products_prices, file, indent=4, ensure_ascii=False)


def get_result() -> None:
    with open('data/product_description.json') as file:
        products_data = json.load(file)

    with open('data/product_prices.json') as file:
        products_prices = json.load(file)

    for items in products_data.values():
        products = items.get('body').get('products')

        for item in products:
            product_id = item.get('productId')

            if product_id in products_prices:
                prices = products_prices[product_id]
            else:
                raise ProductNotFoundError(product_id)

            item['item_basePrice'] = prices.get('item_basePrice')
            item['item_salePrice'] = prices.get('item_salePrice')
            item['item_bonus'] = prices.get('item_bonus')
            product_name = item.get('nameTranslit')
            item['item_link'] = ('https://www.mvideo.ru/products/'
                    f'{product_name}-{product_id}')

    with open('data/result.json', 'w') as file:
        json.dump(products_data, file, indent=4, ensure_ascii=False)


def to_excel() -> None:
    with open('data/result.json') as file:
        json_result = json.load(file)
    df_result = pd.DataFrame()
    keys = ['productId', 'modelName', 'brandName', 'item_basePrices', 
            'item_salePrice', 'item_bonus', 'item_link']

    for i in range(len(json_result)):
        for product in json_result.get(f'{i}').get('body').get('products'):
            tmp_df = pd.DataFrame.from_dict(
                    {key: [product[key]] for key in keys})
            df_result = pd.concat([df_result, tmp_df], ignore_index=True)
    df_result.to_excel('./data/result.xlsx')



def main() -> None:
#    cur_time = datetime.now().strftime('%H:%M:%S') 
#    print(f'>> {cur_time}. Start parsing.')
#    get_data()
#    get_result()
#    cur_time = datetime.now().strftime('%H:%M:%S') 
#    print(f'>> {cur_time}. Parsing is finished.')
    to_excel()
    print(f'>> Parsed data transfer to xlsx file.')


if __name__ == '__main__':
    main()

