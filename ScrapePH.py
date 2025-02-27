# env: zero
# edit by: Sunny
# edit at: 26/02/25

# purpose: Provide modulerized solution for scraping product infos from producthunt using selenium


import os
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from utils import random_sleep,save2json,read4json
from utils import Browser
import argparse

from time import sleep
import re 
import json
import tqdm
import random
PATH=os.path.abspath(__file__)
DIR = os.path.dirname(PATH)
print('current file path is: {0}'.format(PATH))
print('current file directory is: {0}'.format(DIR))


# Get all categories url (if 'categories.json' doesn't exit)
class CateScraper:
    def __init__(self, url, max_attempts=50, wait_time=5):
        self.url = url
        self.max_attempts = max_attempts
        self.wait_time = wait_time
        self.browser = None

    def init_browser(self, has_screen=True, agent=True):
        """初始化浏览器实例"""
        try:
            self.browser = Browser(has_screen=has_screen, agent=agent)
            self.browser.delete_all_cookies()
            return True
        except Exception as e:
            print(f"浏览器初始化失败: {str(e)}")
            return False

    def navigate_to_page(self):
        """导航到目标页面"""
        self.browser.get(self.url)
        self.browser.implicitly_wait(self.wait_time)

    def scrape_categories(self):
        """爬取分类链接的核心逻辑"""
        if not self.browser:
            raise ValueError("浏览器未初始化")

        categories = []
        base_selector = "#root-container > div.styles_container__eS_WB > main > div > div:nth-child({}) > a"

        for i in range(1, self.max_attempts + 1):
            try:
                element = self.browser.find_one(By.CSS_SELECTOR, base_selector.format(i))
                category_url = element.get_attribute('href')
                print(f"发现分类链接: {category_url}")
                categories.append(category_url)
            except:
                print(f"完成爬取，共找到 {len(categories)} 个分类")
                break

        return categories

    def run(self):
        """执行完整流程"""
        if not self.init_browser():
            return []
            
        try:
            self.navigate_to_page()
            return self.scrape_categories()
        finally:
            if self.browser:
                self.browser.quit()




# get products Info in PH
class ProductPHScraper:
    def __init__(self,
                 CATE_URL,
                 checkpoint_file,
                 selectors=None,
                 max_try=1000,
                 wait_time=20,
                 load_more_interval=10):
        
        # 初始化配置
        self.CATE_URL=CATE_URL
        self.checkpoint_file = checkpoint_file
        self.max_try = max_try
        self.wait_time = wait_time
        self.load_more_interval = load_more_interval


        # 默认CSS选择器配置
        self.selectors = selectors or {
            'product_container': '#product-feed > section:nth-child({n})',
            'name': ' > div > div.flex.flex-row.gap-4 > div > a > h3',
            'overview': ' > div > p',
            'types': ' > div > div.flex.flex-row.flex-wrap.items-center.gap-2',
            'href': ' > div > div.flex.flex-row.gap-4 > a',
            'load_more_button': '#product-feed > button',
            }

        # 运行时状态
        self.browser = None
        self.seen_urls = set()
        self.all_products = []
        self._load_checkpoint()

    def _load_checkpoint(self):
        """增强版检查点加载，处理空文件情况"""
        #path = Path(os.path.join(DIR, self.checkpoint_file))
        
        if not self.checkpoint_file.exists():
            print("⭕ 无历史检查点文件")
            return

        try:
            # 检查文件是否为空
            if self.checkpoint_file.stat().st_size == 0:
                print("⚠ 检查点文件存在但为空，跳过加载")
                return

            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("检查点文件格式错误，应为列表")

                self.all_products = data
                self.seen_urls = {p["url"] for p in self.all_products}
                print(f"✓ 已恢复检查点，加载记录数: {len(self.all_products)}")

        except json.JSONDecodeError as e:
            print(f"× 检查点文件损坏，无法解析JSON: {str(e)}")
            self._init_empty_data()
        except Exception as e:
            print(f"× 检查点加载失败: {str(e)}")
            self._init_empty_data()


    def _init_empty_data(self):
        """初始化空数据容器"""
        print("⚠ 初始化空数据容器")
        self.all_products = []
        self.seen_urls = set()


    def _save_checkpoint(self):
        """保存当前进度"""
        #path = Path(os.path.join(DIR, self.checkpoint_file))
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.all_products, f, indent=2)
            print(f"✓ 检查点已保存（当前总数: {len(self.all_products)}）")
        except Exception as e:
            print(f"× 检查点保存失败: {e}")


    def _init_browser(self,has_screen=True,agent=True):
        """初始化浏览器实例，并导航至目标页面"""
        try:
            self.browser=Browser(has_screen=has_screen,agent=agent)
            self.browser.delete_all_cookies()
            self.browser.get(self.CATE_URL)
            sleep(self.wait_time)
            return True
        except Exception as e:
            print(f'初始化浏览器失败：{str(e)}')
            return False

    def _scrape_product(self,n:int) -> dict:
        """抓取单个产品信息"""
        container = self.selectors['product_container'].format(n=n)
        try:
            name=self.browser.find_one(By.CSS_SELECTOR, f"{container}{self.selectors['name']}").text
            overview=self.browser.find_one(By.CSS_SELECTOR, f"{container}{self.selectors['overview']}").text
            type=self.browser.find_one(By.CSS_SELECTOR, f"{container}{self.selectors['types']}").text.replace('\n•\n', ',')
            url=self.browser.find_one(By.CSS_SELECTOR, f"{container}{self.selectors['href']}").get_attribute('href')

            return {
                "name": name,
                "overview": overview,
                "type": type,
                "url":url,
            }
        except Exception as e:
            print(f"× 第 {n} 个产品解析失败: {str(e)}")
            return None

    def _click_load_more(self):
        """执行分页加载操作"""
        try:
            button = self.browser.find_one(By.CSS_SELECTOR, self.selectors['load_more_button'])
            print(f"元素状态: visible={button.is_displayed()}, enabled={button.is_enabled()}")  # 新增状态检查
            button.click()
            return True
        except Exception as e:
            print(f"※ 分页加载失败，可能已达页尾: {str(e)}")
            return False
        
    def scrape(self):
        """执行抓取流程"""
        try:
            self._init_browser()
            
            for n in range(1, self.max_try + 1):
                # 分页加载
                if n % self.load_more_interval == 0:
                    self._click_load_more()
                    self._save_checkpoint()
                    # break for a while
                    sleep(self.wait_time)

                # 抓取产品信息
                product = self._scrape_product(n)
                if not product:
                    continue

                # 去重检查
                if product["url"] in self.seen_urls:
                    print(f"⏩ 已存在产品跳过: {product['url']}")
                    continue

                # 记录新数据
                self.all_products.append(product)
                self.seen_urls.add(product["url"])


        except KeyboardInterrupt:
            print("\n用户中断操作，正在保存检查点...")
        except Exception as e:
            print(f"× 发生未预期错误: {str(e)}")
        finally:
            self.close()

    def close(self):
        """安全关闭爬虫"""
        if self.browser:
            self.browser.quit()
            print("浏览器实例已关闭")
        self._save_checkpoint()
        print(f"抓取会话结束，总计获取: {len(self.all_products)} 条记录")



def main():
    # 配置命令行参数解析
    parser = argparse.ArgumentParser(description='网页分类爬取工具')
    parser.add_argument('--CATE_URL', '-u', 
                        required=True,
                        help='目标URL地址，例如 https://example.com')
    parser.add_argument('--CATE_FILE', '-o', 
                        default='./Output/categories.json',
                        help='cate_file保存地址，默认为./Output/categories.json')
    parser.add_argument('--MAX_TRY', '-m',  
                        type=int,         
                        default=50,        
                        help='每个分类所获取的产品数量')  
    args = parser.parse_args()



    # STEP1: Scrape Categories URL if 'categories.json' doesn't exist
    cate_path=Path(os.path.join(DIR,args.CATE_FILE))
    print(cate_path)
    
    if cate_path.exists() and cate_path.is_file():
        print(f"{args.CATE_FILE} 文件存在,跳过此步骤")
        cate_urls=read4json(cate_path)
    else:
        print(f"{args.CATE_FILE} 文件不存在,开始抓取...")
        CateScraper = CateScraper(
            url=args.CATE_URL,
            max_attempts=50,
            wait_time=5)
        cate_urls = CateScraper.run()
        # 保存结果（使用默认路径）
        if cate_urls:
            save2json(cate_urls,cate_path)
    
    # STEP2: Scrape Product info in PH for all cates
    for i in range(8,len(cate_urls)):
        PH_path=Path(os.path.join(DIR,f'./Output/PH_Checkpoint_{i}.json'))
        
        PHScraper=ProductPHScraper(
            CATE_URL=cate_urls[i],
            checkpoint_file=PH_path,
            max_try=args.MAX_TRY,
            load_more_interval=10,
        )
        PHScraper.scrape()


# sample usage
# ./Module_Code/ScrapePH.py --CATE_URL https://www.producthunt.com/categories --MAX_TRY 2000  

if __name__ == "__main__":
    main()
    



