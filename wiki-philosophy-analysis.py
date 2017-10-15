#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  7 14:00:04 2017

@author: peter

Wiki-philosophy-analysis.py is a script to analyze the degrees of seperation
of articles from Wikipedia's 'philosophy' page. 
See https://en.wikipedia.org/wiki/Wikipedia:Getting_to_Philosophy
for additional context.

It uses the CSVs created in wiki-philosophy.py
"""

import matplotlib.pyplot as plt 
import numpy as np
import pandas as pd
from collections import OrderedDict
from bokeh.plotting import figure, output_file, show
from bokeh.models import HoverTool, OpenURL, TapTool
from bokeh.resources import CDN
from bokeh.embed import file_html

def histogram(dist):
    """
    Wrapper function to get histogram() functionality in MATLAB
    """
    plt.hist(dist, bins=np.arange(min(dist)-0.5, max(dist)+1.5, 1))

plt.close("all")
randDist = pd.read_csv('random.csv')
top100Dist = pd.read_csv('top100.csv')
topCat = pd.read_csv('topcategories.csv')

## RANDOM 500 PAGES - HISTOGRAM
histogram(randDist.Degrees)
plt.xlabel('Degrees from ''/wiki/Philosophy''')
plt.ylabel('Count')
plt.title('Distribution of 500 random Wikipedia pages')
plt.savefig('random_dist.png')
plt.savefig('random_dist.svg')

## TOP 100 PAGES - HISTOGRAM
plt.figure()
histogram(top100Dist.Degrees)
plt.xlabel('Degrees from ''/wiki/Philosophy''')
plt.ylabel('Count')
plt.title('Distribution of the top 100 Wikipedia pages')
plt.savefig('top100_dist.png')
plt.savefig('top100_dist.svg')

## TOP 100 PAGES - RANK VS DEGREES
plt.figure()
plt.plot(top100Dist.Rank,top100Dist.Degrees,'o')
plt.xlabel('Page rank')
plt.ylabel('Degrees from ''/wiki/Philosophy''')
plt.title('Degrees vs page rank for the top 100 Wikipedia pages')
plt.savefig('top100_rankvsdegrees.png')
plt.savefig('top100_rankvsdegrees.svg')

## TOP 100 PAGES - RANK VS DEGREES ON BOKEH
output_file("top100.html")
source = ColumnDataSource(
    data=dict(
        x=top100Dist.index.values+1,
        y=top100Dist.Degrees,
        label=top100Dist.Text,
        link=top100Dist.Link
    )
)
p = figure(plot_height = 400, plot_width = 800, tools="tap,reset")
cr = p.circle('x', 'y', color="#2222aa", size=15, source=source,
              hover_fill_color="firebrick",line_color=None,hover_line_color="white")

# HoverTool
hover =p.select(dict(type=HoverTool))
tooltips = OrderedDict([
    ("Page", "@label"),
    ("Rank", "@x"),
    ("Degrees", "@y"),
])
p.add_tools(HoverTool(tooltips=tooltips, renderers=[cr]))

# TapTool
taptool = p.select(type=TapTool)
url = "https://en.wikipedia.org@link"
taptool.callback = OpenURL(url=url)

# Title and axes
p.title.text = 'Degrees vs page rank for the top 100 Wikipedia pages'
p.title.align = 'center'
p.title.text_font_size = '16px'
p.xaxis.axis_label = 'Page rank'
p.yaxis.axis_label = 'Degrees from ''/wiki/Philosophy'''
p.xaxis.axis_label_text_font_size = '16px'
p.yaxis.axis_label_text_font_size = '16px'

show(p)
html = file_html(p, CDN, "top100.html")

## CATEGORICAL DATA
# List of categories -did this part manually
cats = ['Countries','Cities','People','Singers','Actors','Sportsmen',
        'Modern political leaders','Pre-modern people','3rd-millenium people',
        'Music bands','Sports teams','Films and TV series','Albums',
        'Books and book series', 'Pre-modern books and texts']

# New dataframe
catsdf = pd.DataFrame(columns=('Category','Degrees','Popularity','Top_Text'))

for i in topCat.Table.unique():
    d = topCat.loc[topCat['Table'] == i].Degrees.tolist()
    p = topCat.loc[topCat['Table'] == i].Popularity.tolist()
    t = topCat.loc[topCat['Table'] == i].Text.tolist()[0]
    catsdf.loc[len(catsdf)] = [cats[i-2], d, p, t]

## BOX PLOT: DEGREES VS CATEGORY
fig = plt.figure()
ax = fig.add_subplot(111)
bp = ax.boxplot(catsdf.Degrees.tolist())
ax.set_xticklabels(cats, rotation=45,ha="right")
plt.ylabel('Degrees from ''/wiki/Philosophy''')
plt.title('Degrees from ''/wiki/Philosophy by category''')
fig.tight_layout()
plt.savefig('categories_boxplot.png')
plt.savefig('categories_boxplot.svg')

## BAR PLOT: POPULARITY VS CATEGORY
n_groups = len(catsdf.Popularity)
val1  = np.zeros((n_groups,1))
val10 = np.zeros((n_groups,1))
val30 = np.zeros((n_groups,1))
for i in np.arange(n_groups):
    val1[i]  = catsdf.Popularity[i][0]
    val10[i] = catsdf.Popularity[i][9]
    val30[i] = catsdf.Popularity[i][29]

# create plot
fig, ax = plt.subplots(figsize=(8,5))
index = np.arange(n_groups)
bar_width = 0.7
 
rects1 = plt.bar(index+bar_width, val1, bar_width,align='center',label='Most popular page')
rects2 = plt.bar(index+bar_width, val10, bar_width,align='center',label='10th-most popular page')
rects3 = plt.bar(index+bar_width, val30, bar_width,align='center',label='30th-most popular page')

for row in index:
    ax.text(index[row]+bar_width,val1[row]+2,catsdf.Top_Text[row],
            horizontalalignment='center',bbox=dict(facecolor='white', alpha=0.5))

plt.ylabel('Page popularity (millions of pageviews)')
plt.title('Page popularity by category')
plt.xticks(index + bar_width, cats)
plt.setp(plt.xticks()[1], rotation=45,ha="right")
plt.legend()
plt.tight_layout()
plt.savefig('categories_popularity.png')
plt.savefig('categories_popularity.svg')