from bs4 import BeautifulSoup
import bs4.element as element
import re
from Handlers.Good import Good

async def collect_from_vkusvill(soup: BeautifulSoup, good_id: int):
    product_container = soup.find('div', {'class': 'Product__head'})
    if not product_container: return None

    good = Good()
    good.id = good_id
    good.title = soup.find("h1", {"class": "Product__title"}).text.strip()
    try:
        good.weight = soup.find("div", {"class": "ProductCard__weight"}).text.strip().replace('&nbsp;',' ').replace('\xa0', ' ')
    except:
        good.weight = "1"

    pattern = re.compile(r'(\d+\s+\d+)\s+руб\/кг')
    match = pattern.search(good.weight)
    if match:
        weighted = True
        good.full_cost = match.group(1).replace(' ', '')
        good.weight = 1000
        good.discount_cost = None
        good.has_discount = False
    else:
        weighted = False
        try:
            full_cost_str = soup.find("span", {"class": "Price Price--lg _last"}).text.strip()
            discount_cost_str = soup.find("span", {"class": "Price--gray"}).text.strip()
            good.has_discount = True
        except Exception as E:
            # print(E)
            try:
                full_cost_str = soup.find("span", {"class": "Price--gray"}).text.strip()
            except:
                full_cost_str = soup.find("span", {"class": "Price Price--lg _last"}).text.strip()
            discount_cost_str = None
            good.has_discount = False
        finally:
            good.full_cost = re.search("\d+", full_cost_str)[0]
            good.discount_cost = re.search("\d+", discount_cost_str)[0] if discount_cost_str else None

    brands = soup.find_all(string=re.compile(r'Бренд', re.IGNORECASE))

    good.brand = brands[0].find_parents(limit=2)[1].find('div').text.strip()
    good_cats = soup.find_all("span", {"class": "Breadcrumbs__slide"})[2:]
    # for i in range(len(good_cats)): good_cats[i] = good_cats[i].text.strip()
    good.categories.append(good_cats[0].text.strip())
    if len(good_cats)>1: good.categories.append(good_cats[1].text.strip())
    else: good.categories.append('Нет')
    good.format(weighted)

    return good

async def collect_from_gold_apple(soup: BeautifulSoup, good_id: int):
    good = Good()
    good.id = good_id
    good.brand = soup.find('a', {'data-transaction-name': "ga-pdp-title"}).get('content')

    categories = soup.find_all('li', {'itemprop': "itemListElement"})
    categories_list = []
    for cat in categories[1:]:
        categories_list.append(cat.text.strip())
    if categories[0].text.strip() == "...":
        good.categories_expected.append(categories_list)
    else:
        good.categories = categories_list

    try:
        price_string = soup.find('div', {'data-test-id': 'bestLoyalty'}).text.replace('₽', '').replace('\n', '').split(' ')
        prices = [i for i in price_string if i.isdigit()]
        regular_price, discounted_price = prices[0:len(prices) // 2 + (1 if len(prices) % 2 == 1 else 0)], prices[len(prices) // 2 + (1 if len(prices) % 2 == 1 else 0):]
        regular_price = int(''.join(regular_price))
        discounted_price = int(''.join(discounted_price))
    except AttributeError:
        try:
            test = soup.find('div', {'itemtype': 'http://schema.org/Offer'}).text.replace('₽', '').replace('\n','').split(' ')
            test = [i for i in test if i.isdigit()]
            regular_price = int(''.join(test))
            discounted_price = None
        except AttributeError:
            return None

    title_lower = soup.find_all('span', {'itemprop': "name"})[-1].text.replace('\n', '').strip()
    good.title = good.brand + " " + title_lower + "\n"

    weight = 1
    weight1 = ""

    try:
        characteristics = soup.find('div', {'data-test-id': 'append'}).find('dl').find('div').find_all('div')
    except:
        pass
    else:
        for char in characteristics:
            string = char.find_all('dt')
            if string[0].text.strip() in ['объём', 'вес']:
                weight = string[1].text.strip()
                try:
                    weight, weight1 = weight.split(' ')
                except:
                    pass

    good.full_cost = regular_price
    good.discount_cost = discounted_price
    good.has_discount = True if discounted_price is not None else False
    good.weight = weight
    good.weight_value = weight1

    good.format_weight()

    return good

async def collect_from_yarche_plus(card: element.Tag, good_id: int, categories: list):
    good = Good()
    good.id = good_id

    good.title = card.find('div').find('img').get('alt').replace(' ', '').replace("'", "\\'")
    brand = re.findall('«(.+?)»', good.title)
    if brand == []: good.brand = ""
    else: good.brand = brand[0]

    good.categories = categories

    price_and_weight = card.find('div', recursive=False).find_all('div', recursive=False)[0].find_all('div', recursive=False)
    prices = price_and_weight[0].find_all('div')
    if len(prices) == 1:
        good.has_discount = False
        good.discount_cost = None
        good.full_cost = float(prices[0].get_text().replace('₽', '').replace(',', '.').replace(' ', '').strip())
    else:
        good.has_discount = True
        good.full_cost = float(prices[-1].get_text().replace('₽', '').replace(',', '.').replace(' ', '').strip())
        good.discount_cost = float(prices[0].get_text().replace('₽', '').replace(',', '.').replace(' ', '').strip())

    weight = price_and_weight[1].get_text()
    if 'шт' in weight: good.weight = 1
    elif ('кг' in weight) or ('л' in weight and 'мл' not in weight): good.weight = int(float(re.search('\d+(?:[.,]\d+)?', weight)[0].replace(',', '.'))*1000.0)
    else: good.weight = int(re.search('\d+', weight)[0])

    return good

async def collect_page_from_gold_apple(soup: BeautifulSoup):

    links_list = []
    good_cards = soup.find_all('a', {"data-transaction-name": 'ga-product-card-vertical'})
    for good_card in good_cards:
        links_list.append(good_card.get('href'))

    return links_list

