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


from time import sleep
import re 
import json
import tqdm
import random

#from exceptions import RetryException

def random_sleep(average=1):
    _min, _max = average * 1 / 2, average * 3 / 2
    sleep(random.uniform(_min, _max))


# save as json file
def save2json(data,path):
    with open(path,'w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    
    print('successfully saved to {}'.format(path))

    return None

def read4json(path):
    with open(path,'r',encoding='utf-8') as f:
        data=json.load(f)

    return data

class Browser:
    def __init__(self, has_screen,agent):
        #dir_path = os.path.dirname(os.path.realpath(__file__))
        service_args = ["--ignore-ssl-errors=true"]
        chrome_options = Options()
        if not has_screen:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-notifications")  # 禁用通知
        chrome_options.add_argument("--disable-popup-blocking")  # 禁用弹窗阻止
        chrome_options.add_argument("--no-sandbox")          # 禁用沙盒
        chrome_options.add_argument("--disable-dev-shm-usage") # 避免内存不足崩溃
        chrome_options.add_argument("--remote-allow-origins=*")  # 允许跨域

        # set the timeout to a big value
        caps = chrome_options.to_capabilities()
        #caps["newCommandTimeout"] =  1000000

        # set 
        if agent:
            chrome_options.add_argument(f'user-agent={UserAgent().random}')
        else:
            chrome_options.add_argument(f'user-agent={"Opera/9.25 (Macintosh; Intel Mac OS X; U; en)"}')

        #self.driver = webdriver.Chrome(
        #    executable_path="%s/bin/chromedriver" % dir_path,
        #    service_args=service_args,
        #    chrome_options=chrome_options,
        #)
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options,keep_alive=True)
        # webdriver.Chrome(ChromeDriverManager().install(),
        #                  service_args=service_args,
        #                   chrome_options=chrome_options,
        #                   desired_capabilities=caps)
        
        self.driver.implicitly_wait(5)


    @property
    def page_height(self):
        return self.driver.execute_script("return document.body.scrollHeight")

    def get(self, url):
        self.driver.get(url)

    def delete_all_cookies(self):
        self.driver.delete_all_cookies()
    
    def clear_local_storage(self):
        self.driver.execute_script("window.localStorage.clear();")

    @property
    def current_url(self):
        return self.driver.current_url

    def implicitly_wait(self, t):
        self.driver.implicitly_wait(t)

    def find_one(self,mode,name,elem=None, waittime=0):
        """
        mode: by which name to search (By.CSS_SELECTOR/By.CLASS_NAME/By.TAG_NAME)
        name: the class name/tage name/css selector name
        """
        obj = elem or self.driver

        if waittime:
            WebDriverWait(obj, waittime).until(
                EC.presence_of_element_located((mode, name))
            )

        try:
            return obj.find_element(mode, name)
        except NoSuchElementException:
            print("No such element")


    def scroll_down(self, wait=0.3):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        random_sleep(wait)

    def scroll_up(self, offset=-1, wait=2):
        if offset == -1:
            self.driver.execute_script("window.scrollTo(0, 0)")
        else:
            self.driver.execute_script("window.scrollBy(0, -%s)" % offset)
        random_sleep(wait)

    def js_click(self, elem):
        self.driver.execute_script("arguments[0].click();", elem)
    

    def open_new_tab(self, url):
        self.driver.execute_script("window.open('%s');" %url)
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.implicitly_wait(5)

    def close_current_tab(self):
        self.driver.close()
        self.driver.implicitly_wait(5)
        self.driver.switch_to.window(self.driver.window_handles[0])
    
    def quit(self):
        self.driver.quit()