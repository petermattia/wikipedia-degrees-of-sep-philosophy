#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 13:38:17 2017

@author: peter

Wiki-philosophy.py is a script to 

TODO:
    Looping: return to original: Finite set -> mathematics
"""
def main():
    import matplotlib.pyplot as plt 
    
    # Random pages
    df = randomPageAnalysis()
    histogram(df.Degrees)
    plt.xlabel('Degrees from ''/wiki/Philosophy''')
    plt.ylabel('Count')
    
    # Top 100 pages
    top100dist = top100PageAnalysis();
    plt.figure()
    plt.plot(top100dist.Rank,top100dist.Degrees)

def randomPageAnalysis():
    """
    Analyzes the degrees of seperation for 'num' random pages
    """
    import pandas as pd
    
    # Num repetitions
    num = 2
    
    # Create array for distribution
    df = pd.DataFrame(columns=('Text','Degrees'))
    
    # repeat 100 times
    for x in range(0, num):
        degrees, firstPage = crawlWikiPageWrapper()
        # Exclude errors
        if degrees>0:
            df.loc[len(df)] = [firstPage, degrees]
    
    return df
    
def top100PageAnalysis():
    """
    Analyzes the degrees of seperation for the top 100 pages
    """
    df = getTop100Pages()
    
    degree = []
    
    for l in df.Link:
        degree.append(crawlWikiPageWrapper(l[6:])[0])
    
    df = df.assign(Degrees = degree)
    df.to_csv('top100.csv')

def crawlWikiPageWrapper(article='Special:Random'):
    import sys
    
    try:
        x, firstPage = crawlWikiPage(article)
        return x, firstPage
    except UnboundLocalError:
        print('Bad page: no links in paragraphs')
        return -1
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return -1
        
def crawlWikiPage(article='Special:Random'):
    import requests
    from bs4 import BeautifulSoup
     
    # Get a random page and its soup
    req = requests.get('https://en.wikipedia.org/wiki/' + article)
    soup = BeautifulSoup(req.text, 'lxml')
    firstPage = soup.title.text
    
    # Initialize counter & article list, and display first article
    i = 0;
    articles = []
    print('-------------------------------------')
    print('0. ' + firstPage)
    
    # Begin looping
    while soup.title.text != 'Philosophy - Wikipedia' and i < 50:        
        # Get main text (always in the 'mw-parser-output' class in Wikipedia pages)
        main_text = soup.body.find('div', {'class':'mw-parser-output'})
        
        # Get all href_tags (links) in main_text.contents
        # Break nested loop if we find a good tag
        flag = False
        for content in main_text.contents:
            # Test content to make sure it is <p>, not sidebar, etc
            if isGoodContent(content):
                # Get all <a> tags (links) in content
                links_in_content = content.find_all('a',href=True)
                for l in links_in_content:
                    if isLinkGood(l,content, articles):
                        print('  Good link: '+ l['href'])
                        flag = True
                        break
                    else:
                        print('  Bad link: ' + l['href'])
                if flag:
                    # Break out of double loop
                    break
        
        # Increment counter & list
        i += 1
        articles.append(l['href'])
                
        # Submit new request
        link = 'https://en.wikipedia.org' + l['href']
        req = requests.get(link)
        soup = BeautifulSoup(req.text, 'lxml')
        print(str(i) + '. ' + soup.title.text)
        
    return i, firstPage

def isGoodContent(content):
    """
    isGoodContent(content) makes sure content is a <p> tag and not 
    geographic coordinates (see top of wiki/Canada)
    """
    # All main-text content is in <p> tags. 
    # This line primarily excludes sidebar content
    if not content.name == 'p':
        return False
    # Geotags for geographic places are bad
    if content.text.startswith('Coordinates: '):
        return False
    return True

def isLinkGood(l, content, articles):
    """
    isLinkGood(l,content) performs three tests on a link:
        1. isGoodReference - in-page citations, meta pages, external links, etc
        2. isLinkInParentheses - 
        3. isLinkLooping - 
    
    Think of the boolean logic as:
        "Is the link reference good, not in parentheses, and not in a loop?"
    """
    return isGoodReference(l) and not isLinkInParentheses(l,content) and not isLinkLooping(l, articles)

def isGoodReference(l):
    """ 
    isGoodReference(l) identifies if a link reference is 'good', meaning it 
    links to a "valid" (i.e. non-'meta') Wikipedia entry.
    """          
    tag = l['href']
    # First line gets in-page citations (start with #)
    # or external links (start with 'https://' or '//upload.wikipedia.org')
    if not tag.startswith('/wiki/'):
        return False
    
    # Pages that contain a colon are "meta" pages, like
    # '/wiki/Help:', '/wiki/File', or '/wiki/Wikipedia:'
    if ':' in tag:
        return False
    
    return True

def isLinkInParentheses(t, content):
    """
    Finds if link is in parentheses (excluded content, typically languages)
    """
    txt = str(content)
    idx = txt.index(str(t))
    
    l = txt[0:idx].count('(')
    r = txt[0:idx].count(')')
    return l>r

def isLinkLooping(l, articles):
    """
    Finds if we've already crawled this link before
    """
    tag = l['href']
    for a in articles:
        if tag == a:
            return True
    return False

def histogram(dist):
    """
    Wrapper function to get histogram() functionality in MATLAB
    """
    import numpy as np
    import matplotlib.pyplot as plt 
    plt.hist(dist, bins=np.arange(min(dist)-0.5, max(dist)+1.5, 1))
    
def getTop100Pages():
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    
    article = 'Wikipedia:Multiyear_ranking_of_most_viewed_pages'
    req = requests.get('https://en.wikipedia.org/wiki/' + article)
    soup = BeautifulSoup(req.text, 'lxml')
    main_text = soup.body.find('div', {'class':'mw-parser-output'})
    table = main_text.find('table',{'class':'wikitable'}).contents
    
    df = pd.DataFrame(columns=('Rank','Text','Link','Popularity'))
    
    for row in table:
        if isGoodRow(row):
            rank = int(row.contents[1].text)
            text = row.contents[3].find('a').text
            link = row.contents[3].find('a')['href']
            pop = float(row.contents[5].text)
            df.loc[len(df)] = [rank, text, link, pop]
    
    return df
        
def isGoodRow(row):
    if not row.name == 'tr':
        return False
    # Geotags for geographic places are bad
    try:
        int(row.contents[1].text)
        return True
    except:
        return False

if __name__ == "__main__":
    main()