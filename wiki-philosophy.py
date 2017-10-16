#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 13:38:17 2017

@author: peter

Wiki-philosophy.py is a script to analyze the degrees of seperation
of articles from Wikipedia's 'philosophy' page. 
See https://en.wikipedia.org/wiki/Wikipedia:Getting_to_Philosophy
for additional context.

"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import sys

def main():
    # Random pages
    randomPageAnalysis(500)
    
    # Top 100 pages
    top100PageAnalysis()
    
    # Top categories analysis
    topCategoriesPageAnalysis()

def randomPageAnalysis(num=500):
    """
    Analyzes the degrees of seperation for 'num' random pages
    """
    # Create array for distribution
    df = pd.DataFrame(columns=('Text','Degrees'))
    
    # repeat 100 times
    for _ in range(0, num):
        degrees, firstPage = crawlWikiPageWrapper()
        # Exclude errors
        if degrees>0:
            df.loc[len(df)] = [firstPage, degrees]
    
    df.to_csv('random.csv', index=False)
    return df
    
def top100PageAnalysis():
    """
    Analyzes the degrees of seperation for the top 100 pages
    """
    df = getTop100Pages()
    
    degree = []
    
    # Gets the degrees of seperation for the top 100 pages
    for l in df.Link:
        degree.append(crawlWikiPageWrapper(l[6:])[0])
    
    # Append degrees column to dataframe
    df = df.assign(Degrees = degree)
    
    # Save and return
    df.to_csv('top100.csv', index=False)
    return df

def topCategoriesPageAnalysis():
    """
    Analyzes the degrees of seperation for the top 30 entries in various
    categories
    """
    df = getTopCategories()
    
    degree = []
    
    # Gets the degrees of seperation for the top pages in all categories
    for l in df.Link:
        degree.append(crawlWikiPageWrapper(l[6:])[0])
    
    # Append degrees column to dataframe
    df = df.assign(Degrees = degree)
    
    # Save and return
    df.to_csv('topcategories.csv', index=False)
    return df

def crawlWikiPageWrapper(article='Special:Random'):    
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
        # Test content to make sure it is <p>, not sidebar, etc
        content_gen = (c for c in main_text.contents if isGoodContent(c))
        for content in content_gen:
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
        
        # If we've detected a good link, get next page. Otherwise, quit
        if flag:
            # Increment counter & list
            i += 1
            articles.append(l['href'])
                    
            # Submit new request
            req = requests.get('https://en.wikipedia.org' + l['href'])
            soup = BeautifulSoup(req.text, 'lxml')
            print(str(i) + '. ' + soup.title.text)
        else:
            break
        
    return i, firstPage

def isGoodContent(content):
    """
    isGoodContent(content) makes sure content is a <p> tag and not 
    geographic coordinates (see top of wiki/Canada)
    """
    # All main-text content is in <p> or <ul> tags. 
    # This line primarily excludes sidebar content
    if content.name not in {'p','ul'}:
        return False
    # Geotags for geographic places are bad
    if content.text.startswith('Coordinates: '):
        return False
    return True

def isLinkGood(l, content, articles):
    """
    isLinkGood(l,content) performs three tests on a link:
        1. isGoodReference - in-page citations, meta pages, external links, etc
        2. isLinkInParentheses - tests if link is in parentheses
        3. isLinkLooping - tests if link is looping
    
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

def isLinkInParentheses(tag, content):
    """
    Finds if link is in parentheses (excluded content, typically languages)
    """
    idx = str(content).index(str(tag)) # find location of link in txt
    txt = str(content)[0:idx] # get text up until idx
    return txt.count('(') > txt.count(')') # count '(' vs ')'

def isLinkLooping(l, articles):
    """
    Finds if we've already crawled this link before
    """
    return l['href'] in articles
    
def getTop100Pages():
    """
    Creates a dataframe of the top 100 pages on Wikipedia. 
    See article for url
    """
    article = 'Wikipedia:Multiyear_ranking_of_most_viewed_pages'
    req = requests.get('https://en.wikipedia.org/wiki/' + article)
    soup = BeautifulSoup(req.text, 'lxml')
    main_text = soup.body.find('div', {'class':'mw-parser-output'})
    table = main_text.find('table',{'class':'wikitable'}).contents
    
    df = pd.DataFrame(columns=('Rank','Text','Link','Popularity'))
    
    row_gen = (row for row in table if isGoodRow(row))
    for row in row_gen:
        rank = int(row.contents[1].text)
        text = row.contents[3].find('a').text
        link = row.contents[3].find('a')['href']
        pop = float(row.contents[5].text)
        df.loc[len(df)] = [rank, text, link, pop]
    
    return df
        
def getTopCategories():
    """
    Creates a dataframe of the top 100 pages on Wikipedia. 
    See article for url
    """
    article = 'Wikipedia:Multiyear_ranking_of_most_viewed_pages'
    req = requests.get('https://en.wikipedia.org/wiki/' + article)
    soup = BeautifulSoup(req.text, 'lxml')
    main_text = soup.body.find('div', {'class':'mw-parser-output'})
    # tables is a list of 16 tables on the 'article' page on Wikipedia
    # exclude first table - this is the top100 table
    tables = main_text.find_all('table',{'class':'wikitable'})[1:]
    
    df = pd.DataFrame(columns=('Table','Rank','Text','Link','Popularity'))
    
    for i, table in enumerate(tables):
        row_gen = (row for row in table if isGoodRow(row))
        for row in row_gen:
            rank = int(row.contents[1].text)
            text = row.contents[3].find('a').text
            link = row.contents[3].find('a')['href']
            pop = float(row.contents[-2].text)
            df.loc[len(df)] = [i+1, rank, text, link, pop]
    
    return df

def isGoodRow(row):
    """
    Boolean for if a row in the 'Top 100 articles' table is ranked
    (some rows are unranked, for various reasons)
    """
    if not row.name == 'tr':
        return False
    # See if row has numerical ranking (no asterisk, etc)
    try:
        int(row.contents[1].text)
        return True
    except:
        return False

if __name__ == "__main__":
    main()