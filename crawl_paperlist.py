import os
import time
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

id = "NeurIPS" # ICLR
year = 2021
file_name = f"paperlist_{id}_{year}.tsv"
driver = webdriver.Chrome('/opt/homebrew/bin/chromedriver')
driver.get(f'https://openreview.net/group?id={id}.cc/{year}/Conference')

# get presentation tab names 
ul_container = driver.find_element_by_xpath('//ul[@class="nav nav-tabs"]')
tabs = ul_container.find_elements_by_tag_name('a')
tab_names = [tab.get_attribute('href').split('#')[-1] for tab in tabs]
print(tab_names)

cond = EC.presence_of_element_located((By.XPATH, '//*[@id="notes"]/div'))
WebDriverWait(driver, 60).until(cond)

with open(file_name, 'w', encoding='utf8') as f:
    f.write('\t'.join(['paper_id', 'title', 'link', 'keywords', 'abstract'])+'\n')

# tab_range: 
# NIPS: 2022: range(1,2) only accepted paper 
#       2021: [range(1,4): oral (1), spotlight (2) and poster (3)]
# ICLR: 2019 - 2023: [range(1,4): oral (1), spotlight (2) and poster (3)]
#       2019: [range(1,3), only spotlight and poster]
for k in range(1, 4):
    tab = tab_names[k]
    text = ''

    # loop until no next page
    last_page_num = 1  # Store the last page number visited
    while True:
        ul_element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, f'//*[@id="{tab}"]/ul')))
        elems = ul_element.find_elements_by_xpath('./li')
        for i, elem in enumerate(elems):
            try:
                # parse title
                title = elem.find_element_by_xpath('./h4/a[1]')
                link = title.get_attribute('href')
                paper_id = link.split('=')[-1]
                title = title.text.strip().replace('\t', ' ').replace('\n', ' ')
                # show details
                elem.find_element_by_xpath('./a').click()
                time.sleep(0.2)
                # parse keywords & abstract
                items = elem.find_elements_by_xpath('.//li')
                keyword = ''.join([x.text for x in items if 'Keywords' in x.text])
                abstract = ''.join([x.text for x in items if 'Abstract' in x.text])
                keyword = keyword.strip().replace('\t', ' ').replace('\n', ' ').replace('Keywords: ', '')
                abstract = abstract.strip().replace('\t', ' ').replace('\n', ' ').replace('Abstract: ', '')
                text += paper_id+'\t'+title+'\t'+link+'\t'+keyword+'\t'+abstract+'\n'
            except Exception as e:
                print(f'tab {tab}, # {i}:', e)
                continue
        # click next 
        try:
            # Check if the next page button (›) is clickable
            next_button = driver.find_element_by_xpath('//li[contains(@class, "right-arrow") and not(contains(@class, "disabled"))][1]/a')
            next_button.click()
            time.sleep(2)
            last_page_num += 1

        except Exception as e:
            # If next button is disabled, this will raise an exception and break the loop
            print(f"Last page reached, {tab}, P{last_page_num}, error encountered: {e}")
            break
        
        
    with open(file_name, 'a', encoding='utf8') as f:
        f.write(text)
    try:
        header = ul_element.find_element_by_xpath(f'//*[@id="header"]')
        driver.execute_script("arguments[0].scrollIntoView(true);", header)
        if k < 4: # make sure we only click oral, spotlight and poster
            tab_element = ul_element.find_element_by_xpath(f'//*[@id="notes"]/div/div[1]/ul/li[{(k+1)+1}]/a')
            tab_element.click()
        time.sleep(2) # NOTE: increase sleep time if needed
    except Exception as e:
        print(tab_element)
        print('no next page, exit.', e)
        break
    