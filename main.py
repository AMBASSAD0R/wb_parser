import logging
import collections
import csv

import bs4 as bs4
import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wb_parser')

ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'brand_name',
        'goods_name',
        'price',
        'url'
    )
)

HEADERS = (
    'Бренд',
    'Товар',
    'Цена',
    'Ссылка'
)


class Client:
    def __init__(self, url: str):
        self.session = requests.Session()
        self.session.headers = {
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
        }
        self.url = url
        self.products = []

    def load_page(self):
        res = self.session.get(url=self.url)
        res.raise_for_status()
        return res.text

    def parse_page(self, text):
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('div.dtList.i-dtList.j-card-item')
        for product in container:
            self.parse_product(product=product)

    def parse_product(self, product: bs4.BeautifulSoup):

        url_block = product.select_one('a.ref_goods_n_p')
        if not url_block:
            logger.error('no url_block')
            return

        url = 'https://www.wildberries.ru'
        url += url_block.get('href')
        if not url:
            logger.error('no href')
            return

        name_block = product.select_one('div.dtlist-inner-brand-name')
        if not name_block:
            logger.error('no name_block')
            return

        brand_name = name_block.select_one('strong.brand-name')
        if not brand_name:
            logger.error(f'no brand name in {url}')
            return

        goods_name = name_block.select_one('span.goods-name')
        if not goods_name:
            logger.error(f'no goods-name')
            return

        price_block = product.select_one('span.price')
        price = price_block.select_one('ins.lower-price')
        if not price:
            logger.error(f'no such price in https://www.wildberries.ru{url}')
            return

        # Wrangler /
        brand_name = brand_name.text
        brand_name = brand_name.replace('/', '').strip()

        goods_name = goods_name.text
        goods_name = goods_name.replace('/', '').strip()
        if goods_name[-2:] == 'да':
            goods_name = goods_name[:-2]

        price = price.text
        price = price.replace(' ', ' ').strip()[:-2]

        self.products.append(ParseResult(
            brand_name=brand_name,
            goods_name=goods_name,
            price=price,
            url=url,
        ))

        logger.debug(f'https://www.wildberries.ru{url}, {brand_name}, {goods_name}, {price}')
        logger.debug('-' * 100)

    def save_results(self):
        path = 'C:/Users/User/PycharmProjects/wb_parser/result.csv'
        with open(path, mode='w', encoding='utf-8') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(HEADERS)
            for item in self.products:
                writer.writerow(item)

    def run(self):
        text = self.load_page()
        self.parse_page(text=text)
        logger.info(f'Count results: {len(self.products)}')

        self.save_results()


if __name__ == '__main__':
    parser = Client('https://www.wildberries.ru/catalog/elektronika/tv-audio-foto-video-tehnika/televizory/televizory')
    parser.run()
