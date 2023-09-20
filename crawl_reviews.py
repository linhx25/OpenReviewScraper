import os
import time
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import re

driver = webdriver.Chrome('/opt/homebrew/bin/chromedriver')

df = pd.read_csv('paperlist_nips_2021.tsv', sep='\t', index_col=0)


ratings = dict()
decisions = dict()
for paper_id, link in tqdm(list(df.link.items())):
    try:
        driver.get(link)
        xpath = '//div[@id="note_children"]//span[@class="note_content_value"]/..'
        cond = EC.presence_of_element_located((By.XPATH, xpath))
        WebDriverWait(driver, 60).until(cond)

        elems = driver.find_elements_by_xpath(xpath)
        assert len(elems), 'empty ratings'
        t = []
        for x in elems:
            match = re.search(r'(?:Rating:|Recommendation:)\s*(\d+)', x.text)
            if match: 
                t.append(match.group(1))
        ratings[paper_id] = pd.Series(t, dtype=int)
        decision = [x.text.split(': ')[1] for x in elems if x.text.startswith('Decision:')]
        decisions[paper_id] = decision[0] if decision else 'Unknown'
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(paper_id, e)
        ratings[paper_id] = pd.Series(dtype=int)
        decisions[paper_id] = 'Unknown'

df = pd.DataFrame(ratings).T
df['decision'] = pd.Series(decisions)
df.index.name = 'paper_id'
df.to_csv('ratings_nips_2021.tsv', sep='\t')
