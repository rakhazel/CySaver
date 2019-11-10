from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

from Post import Post

import configparser
import datetime
import time


# get login info from settings.txt

config = configparser.ConfigParser()
config.read('settings.txt')
id = config['LOGIN']['id']
pwd = config['LOGIN']['password']


# open browser

driver = webdriver.Chrome(executable_path=r"C:\Path\chromedriver.exe")


# connect to cyworld

driver.get("https://cy.cyworld.com/cyMain")
assert "cyworld" in driver.title


# remove popup

try:
    elem = driver.find_element_by_css_selector("#coverstory > div.coverstory.coverstory--show > div.coverstory__btns > a.coverstory__close.coverstory__close--today")
    elem.send_keys(Keys.RETURN)
except:
    print("no popup")


# login 

elem = driver.find_element_by_css_selector("#email")
elem.clear()
elem.send_keys(id)

elem = driver.find_element_by_css_selector("#passwd")
elem.clear()
elem.send_keys(pwd)
elem.send_keys(Keys.RETURN)


# go to my page

ignored_exceptions=(StaleElementReferenceException,)
wait = WebDriverWait(driver, 30, ignored_exceptions=ignored_exceptions)
elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'body > div.wrapper.view_page_vers.view_page_vers2 > header > div > a.freak1')))
elem.send_keys(Keys.RETURN)


# prepare list to store posts
postlist = []


# get start date and end date of search
# TODO - get user setting for search duration period (it's hard-coded at the moment)

from_date=config['HISTORY']['from']
until_date=config['HISTORY']['until']

now = datetime.datetime.now()
syyyy = now.year
smm = now.month
eyyyy = syyyy
emm = smm + 1
if emm == 13:
    emm = 1
    eyyyy += 1

# wait for date search button to be ready
elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#all')))


# loop monthes - start from now and go back until 1998-12

while syyyy >= 2018 and smm >= 9:
    print('searching %d-%2d-02 to %d-%2d-01' % (syyyy, smm, eyyyy, emm) )

    # open date search
    driver.find_element_by_css_selector('#all').send_keys(Keys.RETURN)
    elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#allArea > div > ul > li:nth-child(2) > label > span')))
    elem.click()
    
    # from
    elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#sDate')))
    elem.click()
    elem.send_keys(syyyy)
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys('02')
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(smm)

    # to
    elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#eDate')))
    elem.click()
    elem.send_keys(eyyyy)
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys('01')
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(emm)

    # search and close 
    driver.find_element_by_css_selector('#allArea > div > div > button').send_keys(Keys.RETURN)
    driver.find_element_by_css_selector('#all').send_keys(Keys.RETURN) 
    
    # wait for result
    elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.wrapper > article.container > div > section > p.txt_depthgh')))
    print(elem.text)


    # get number of posts to save
    # returning from each post makes the list stale, so we only get the total count for for loop
    count = len(driver.find_element_by_class_name('list_timeline').find_elements_by_tag_name('li'))
    
    #for post in posts:
    for i in range(count):
        # click each post
        # watch out! it's <html> inside an <iframe> element!  switch frames!
        driver.find_element_by_class_name('list_timeline').find_elements_by_tag_name('li')[i].click()
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.wrapper > article.container2.for_homenew_listgh > iframe')))
        driver.switch_to.frame(iframe)

        # saving page source directly isn't quite working.. 
        #with open('page.html', 'w', encoding='utf-8') as f:
        #    f.write(driver.page_source)

        # get content
        datestr = driver.find_element_by_css_selector('body > div.content2 > section > div.view1 > p').text
        post_year = datestr[4:8]
        post_mon = datestr[9:11]
        post_day = datestr[12:14]
        post_hour = datestr[15:17]
        post_min = datestr[18:20]
        post_dtm = datetime.datetime(int(post_year), int(post_mon), int(post_day), int(post_hour), int(post_min))
        print(post_dtm)

        title = driver.find_element_by_id('cyco-post-title').text
        text = driver.find_element_by_css_selector('body > div.content2 > section > div.dscr > section > div').text
        try:
            img = driver.find_element_by_css_selector('body > div.content2 > section > div.dscr > section.post.imageBox.cyco-imagelet > figure > img')
            #img.screenshot('{:%Y-%m-%d_%H:%M}.png'.format(post_dtm) )
            #urllib.urlretrieve(img.get_attribute('src'), "test.png")
        except:
            img = "no image"

        #print('%d (%s-%s-%s %s:%s) [%s] {%s} <%s>\n' % (i, post_year, post_mon, post_day, post_hour, post_min, title, text, img.get_attribute('src')))

        # save post
        postlist.append( Post(post_dtm, title, text, img) )

        # go back to post list
        driver.switch_to.parent_frame()
        time.sleep(1)
        driver.find_element_by_class_name('btn_bigclose').click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.wrapper > article.container > div > section > p.txt_depthgh')))



    # prev month
    eyyyy = syyyy
    emm = smm

    smm -= 1
    if smm == 0:
        smm = 12
        syyyy -= 1

    break


# TODO save posts in postlist to appropriate format


assert "No results found." not in driver.page_source
#driver.close()

