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
config.read('settings.txt',encoding='utf-8')
id = config['LOGIN']['계정']
pwd = config['LOGIN']['암호']


# open browser

driver = webdriver.Chrome(executable_path=r".\chromedriver.exe")


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

#ignored_exceptions=(StaleElementReferenceException,)
wait = WebDriverWait(driver, 30)
elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'body > div.wrapper.view_page_vers.view_page_vers2 > header > div > a.freak1')))
elem.send_keys(Keys.RETURN)


# prepare list to store posts
postlist = []


# get start date and end date of search from settings.txt

st_date=config['HISTORY']['언제부터']
en_date=config['HISTORY']['언제까지']

st_yyyy=int(st_date[0:4])
st_mm=int(st_date[5:7])
st_dd=int(st_date[8:10])
st_dtm=datetime.datetime(st_yyyy, st_mm, st_dd)
#assert st_yyyy >= '1999' and st_yyyy <= '2020' and st_mm >= '01' and st_mm <= '12'

if en_date == 'today':
    en_dtm = datetime.datetime.now()
else:
    en_yyyy=int(en_date[0:4])
    en_mm=int(en_date[5:7])
    en_dd=int(en_date[8:10])
    en_dtm=datetime.datetime(en_yyyy, en_mm, en_dd)


#assert en_yyyy >= '1999' and en_yyyy <= '2020' and en_mm >= '01' and en_mm <= '12'

print('{}년 {}월 {}일 부터 {}년 {}월 {}일까지 백업 해보도록 할게요.'.format(st_dtm.year, st_dtm.month, st_dtm.day, en_dtm.year, en_dtm.month, en_dtm.day)) 

# get range for first search
# search from first day of 언제까지 month to 언제까지 date.  if 언제까지 date is the first, then we'll just search 1 date
search_en=en_dtm
search_st=en_dtm.replace(day=1)


# wait for date search button to be ready
elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#all')))


# loop search

while search_en >= st_dtm:
    print('{}-{}-{} 부터 {}-{}-{} 까지 백업 시도 중'.format(search_st.year, search_st.month, search_st.day, search_en.year, search_en.month, search_en.day) )

    # open date search
    driver.find_element_by_css_selector('#all').send_keys(Keys.RETURN)
    elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#allArea > div > ul > li:nth-child(2) > label > span')))
    elem.click()
    
    # from
    elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#sDate')))
    elem.click()
    elem.send_keys(str(search_st.year))
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(str(search_st.day))
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(str(search_st.month))

    # to
    elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#eDate')))
    elem.click()
    elem.send_keys(str(search_en.year))
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(str(search_en.day))
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(Keys.ARROW_LEFT)
    elem.send_keys(str(search_en.month))

    # search and close 
    driver.find_element_by_css_selector('#allArea > div > div > button').send_keys(Keys.RETURN)
    driver.find_element_by_css_selector('#all').send_keys(Keys.RETURN) 
    
    # wait for result
    time.sleep(1)
    elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'body > div.wrapper > article.container > div > section > p.txt_depthgh')))
    print(elem.text)

    # TODO fix when there are no search results
    # get number of posts to save
    # returning from each post makes the list stale, so we only get the total count for for loop
    # so, if a post is made during loop, there could be unsaved posts
    count=0
    if len(driver.find_elements_by_class_name('list_timeline')) > 0:
        count = len(driver.find_element_by_class_name('list_timeline').find_elements_by_tag_name('li'))
    print('count={}'.format(count))
    
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
    # search_st day should be 1, so subtracting 1 day should get last day of prev month
    search_en = search_st - datetime.timedelta(days=1)
    search_st = search_en.replace(day=1)

    #break


# TODO save posts in postlist to appropriate format
for post in postlist:
    print('({}) [{}] {} <{}>'.format(post.dtm, post.title, post.text, post.img))


assert "No results found." not in driver.page_source
#driver.close()

