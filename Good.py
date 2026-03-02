from selenium.webdriver.support.expected_conditions import title_is

from bs4 import BeautifulSoup
import re

class Good:
    def __init__(self):
        self.id = 0
        self.title = ""
        self.brand = ""
        self.weight = 0
        self.weight_value = ""
        self.categories = []
        self.full_cost = 0
        self.discount_cost = None
        self.has_discount = False
        self.is_active = True
        self.categories_expected = None

    def format(self, weighted = False):
        self.is_vv = True if self.brand=="ВкусВилл" else False

        pattern = re.compile(r'[,]?\s?\d+(\.\d+)?\s?(г|мл|л|кг|мг)', re.IGNORECASE)
        cleaned_name = pattern.sub('', self.title)
        self.title = cleaned_name.replace('  ', ' ').replace('\n', '').replace('"', '').replace("'", "").strip()
        for i in range(len(self.categories)):
            self.categories[i] = self.categories[i].replace('  ', ' ').replace('\n', '').replace('"', '').replace("'", "").strip()

        if weighted: return
        else:
            pattern = re.compile(r'(\d+\s+\d+)\s+руб\/кг')
            match = pattern.search(self.weight)
            if match:
                ww = match.group(1).replace(' ', '')
                self.weight = 1000
                return

            else:
                pattern = re.compile(r'(\d+(\.\d+)?)\s?(г|мл|л|кг|шт|уп)', re.IGNORECASE)
                match = pattern.search(self.weight)

                if match:
                    weight_value = match.group(1)
                    unit = match.group(3).lower()
                    ww = float(weight_value)

                    if unit == 'л':
                        ww *= 1000  # литры в миллилитры
                    elif unit == 'кг':
                        ww *= 1000  # килограммы в граммы

                    self.weight = int(ww)

    def format_weight(self):
        self.title = self.title.replace('  ', ' ').replace('\n', '').replace('"', '').replace("'", "").replace("'", "").strip()
        self.brand = self.brand.replace('  ', ' ').replace('\n', '').replace('"', '').replace("'", "").replace("'", "").strip()
        if self.weight_value == "л" or self.weight_value == "кг":
            self.weight = int(float(self.weight)*1000)
        else:
            self.weight = int(float(self.weight)//1)

    def call_name(self):
        self.format()
        return (self.id, self.title, self.weight, self.is_active, self.brand, self.is_vv)

    def call_price(self):
        return [self.id, self.full_cost, self.has_discount, self.discount_cost]

    def call_categories(self):
        return (self.id, *self.categories)

    def __str__(self):
        return f"ID: {self.id}\nTitle: {self.title}\nBrand: {self.brand}\nWeight: {self.weight}\nCategories: {' > '.join(self.categories)}\nCost: {self.full_cost}\nDiscount: {self.has_discount} {'('+str(self.discount_cost)+')' if self.has_discount else ''}"

import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    z = ["bebra", "dura"]
    z = ' > '.join(z)
    print(z)

    q = 1.2
    print(q//1)

    pass
    # Примеры использования
    #url1 = "https://vkusvill.ru/goods/khleb-litovskiy-narezka-16536.html"
    #url2 = "https://vkusvill.ru/goods/kokteyl-vysoko-belkovyy-active-energy-so-vkusom-mango-i-marakuyi-0-5-230-ml-94678.html"

    #print(get_brand_from_vkusvill(url1))  # Должно вернуть "ВкусВилл"
    #print(get_brand_from_vkusvill(url2))  # Должно вернуть "ACTIVE ENERGY"
