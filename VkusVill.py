import asyncio, warnings
import pandas as pd, numpy as np
from Handlers.YDBPriceHandler import YDB
from Handlers.Logger import AsyncLogger
from collectors import *
from datetime import date
import cookies
from curl_cffi.requests import AsyncSession
from os import system

async def collect_good(session, good_id):
    page_link = f"https://vkusvill.ru/goods/xmlid/{good_id}"

    page_response = await session.get(page_link)
    page_text = page_response.text
    page_soup = BeautifulSoup(page_text, 'lxml')
    # print(page_text)

    good = await collect_from_vkusvill(page_soup, good_id)
    return good

async def collect_purchases(session, logger):
        page_link = "https://vkusvill.ru/personal/istoriya-pokupok"

        page_response = await session.get(page_link)
        page_text = page_response.text
        soup = BeautifulSoup(page_text, 'lxml')

        purchases = soup.find_all("div", {"class": "ProductCards__item"})
        #print(page_text)
        goods_list = dict()
        for purchase in purchases:
            try:
                product_name = purchase.find('a', class_='ProductCard__link')['title'].replace('&nbsp;', ' ').replace('\xa0', ' ')
                product_id = int(purchase.find('div', class_='ProductCard')['data-id'])

                goods_list[product_id] = product_name
            except Exception as E:
                print(E)
                print(purchase)

        #goods_list[74206] = "Сэндвич с беконом и скрэмблом на хлебе с отрубями, кафе"
        await logger.log(level="INFO", message=f"Список из покупок: {goods_list}")

        return goods_list

async def collect_personal_discounts(session, logger):
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://vkusvill.ru/personal/",
            "Content-Type": "application/x-www-form-urlencoded",  # важно!
        }

        url = "https://vkusvill.ru/ajax/user_v2/cabinet/inshop_load_shop_new.php"
        payload = {
            "USER_ID": "4958379",
        }
        response = await session.post(url, data=payload, headers=headers)
        data = response.text  # Если ответ в JSON
        warnings.filterwarnings("ignore", category=DeprecationWarning, message="invalid escape sequence")
        #print(data)
        html = bytes(data, 'utf-8').decode('unicode_escape')
        soup = BeautifulSoup(html, 'lxml')

        discount = soup.find_all('div', {"class": 'VV_GoodsFootenote'})
        goods_list = dict()
        for good in discount:
            try:
                product_name = good.find('a', class_='VV_GoodsFootenote__Title').get('title').strip()
                product_id = good.get('data-id')
            except:
                print(good)
                print('\n\n\n\n\n\n\n\n')
                print("Не смог найти данные по продукту")
            else:
                goods_list[int(product_id)] = product_name

        await logger.log(level="INFO", message=f"Список 6 скидок: {goods_list}")

        return goods_list

async def check_value(df: pd.DataFrame, column_name, value):
    result = df.query(f"{column_name} == {value}")
    return result.empty

async def append_new_purchases(ydb: YDB, logger: AsyncLogger):
    jar = await cookies.get_jar(brand='vkusvill')
    async with await cookies.get_session(jar, brand='vkusvill') as session:
        #session = await cookies.get_session(jar)
        goods_from_purchases = await collect_purchases(session, logger)
        goods_from_discounts = await collect_personal_discounts(session, logger)

        new_goods = {id: "new" for id in [21270, ]}
        goods_to_inspect = {**goods_from_discounts, **goods_from_purchases, **new_goods}
        await logger.log(level="INFO", message=f"Общий список: {goods_to_inspect}")

        goods = ydb.get_goods(shop='vkusvill')

        for good in goods_to_inspect.keys():
            in_db = await check_value(goods, 'product_id', good)
            if not in_db:
                await logger.log(level="WARN", message=f"Товар {good} уже есть в картотеке")
            else:
                await logger.log(level="INFO", message=f"Приступил к добавлению товара {good}")
                good1 = await collect_good(session, good)
                res = ydb.vv_append_good(good1)
                if res == True:
                    await logger.log(level="INFO", message=f"Товар {good} успешно добавлен")
                else:
                    await logger.log(level="WARN", message=f"Ошибка при добавлении товара {good}")
                await asyncio.sleep(1)

async def append_good(ydb: YDB, good_id):
    jar = await cookies.get_jar(brand='vkusvill')
    session = await cookies.get_session(jar)

    goods = ydb.get_goods(shop='vkusvill')

    in_db = await check_value(goods, 'product_id', good_id)
    if not in_db:
        print(f"Товар {good_id} уже существует в карточке")
        return

    good = await collect_good(jar, good_id)
    res = ydb.vv_append_good(good)
    if res==True:
        print(f"Товар {good_id} успешно добавлен")
    else:
        print(f"Ошибка при добавлении товара {good_id}")

async def update_price(ydb: YDB, good: Good = None, logger: AsyncLogger = None, final_insert: bool = False):
    if not final_insert:
        with open('buckets/vkusvill.txt', 'a') as vv_bucket:
            str_ = f"({good.id}, DATE('{date.today().strftime('%Y-%m-%d')}'), {good.full_cost}, {good.has_discount}, {good.discount_cost if good.has_discount else 'NULL'})\n"
            vv_bucket.write(str_)
            vv_bucket.close()
    with open('buckets/vv_counter.txt', 'r') as vv_counter:
        goods_ = vv_counter.read()
        goods_count = int(goods_)
        print(f"В файле counter {goods_count+1} товаров")
    if goods_count >= 29 or (goods_count > 0 and final_insert):
        with open('buckets/vkusvill.txt', 'r') as vv_bucket:
            goods = vv_bucket.read()
            goods = goods.replace('\n', ',')
            res = ydb.update_list_prices_story(goods_info = goods[:-1], shop='vkusvill', logger=logger)
            if res==True:
                print(f"Данные {goods_count+1} товаров были успешно обновлены")
            else:
                print("Ошибка при добавлении товаров")
            vv_bucket.close()
        with open('buckets/vkusvill.txt', 'w') as vv_bucket:
            vv_bucket.close()
    with open('buckets/vv_counter.txt', 'w') as yp_counter:
        if goods_count >= 29 or final_insert:
            yp_counter.write(str(0))
        else:
            yp_counter.write(str(goods_count + 1))
        yp_counter.close()

async def update_old_prices(ydb, logger):
    jar = await cookies.get_jar(brand='vkusvill')
    async with await cookies.get_session(jar, brand='vkusvill') as session:
        goods_to_update = ydb.get_goods_to_update_price(shop='vkusvill', interval=2)
        #goods = ydb.get_goods(shop='vkusvill')['product_id'].tolist()

        for good in goods_to_update: #[:goods.index(62309)]:
            await logger.log(message=f"Работаю с товаром {good}")
            good_data = await collect_good(session, good)
            if good_data == None:
                await logger.log(level="WARN", message=f"Товар {good} удалён из каталога")
                system('afplay /System/Library/Sounds/Sosumi.aiff')
                if input(f"Перевести в неактивные? https://vkusvill.ru/goods/xmlid/{good} ? (Y/N) ").lower() != "n":
                    res = ydb.change_activity(status=False, good_id = good, shop='vkusvill')
                    await logger.log(level="WARN", message=f"Товар {good} переведён в неактивные")
            else:
                await update_price(ydb, good_data, logger)
                #res = ydb.update_price_story(good = good_data, interval=5, shop='vkusvill', logger=logger, check=False)

        await update_price(ydb, logger=logger, final_insert=True)

async def main(ydb, logger, update=False):
    if update: await update_old_prices(ydb, logger)
    await append_new_purchases(ydb, logger)

if __name__ == '__main__':
    ydb = YDB()
    logger = AsyncLogger()
    asyncio.run(main(ydb, logger))