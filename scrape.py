import requests
from bs4 import BeautifulSoup as bsp

import re
import os
import math

# g
BASE_URL = 'https://www.literotica.com/stories/'
HTML_HEADER = '<head><link rel = "stylesheet" href="style/style.css" type="text/css" /></head>'
HTML_FOOTER = '<div class="footer">'


class Story(object):

    def __init__(self, tag):
        self.tag = tag
        self.meta = tag.find('span',{'class' : 'b-sli-meta'})
        self.desc_prefix = '\xa0-\xa0'
        # title
        self.title = self.tag.find('h3').string.replace('/','')
        # author
        self.author = self.meta.find('span',{'class' : 'b-sli-author'}).find('a').string
        # description
        self.description = self.tag.find('span',{'class' : 'b-sli-description'}).text.replace(self.desc_prefix,'')
        # date
        self.date = self.meta.find('span',{'class' : 'b-sli-date'}).string
        # rating
        rating = self.meta.find('span',{'class' : 'b-sli-rating'})
        if rating:
            self.rating = rating.string
        else:
            self.rating = '0'
        # link
        self.link = self.tag.find('h3').find('a')['href']
        # author_home
        self.author_home = self.meta.find('span',{'class' : 'b-sli-author'}).find('a')['href']
        # number of pages
        self.page_count = get_max_pages(self.link,suffix='')
        # rating as float
        self.rating_as_float = 0.5 * math.ceil(2.0 * float(self.rating))
        # fetch content
        self.fetch_content()

    def __str__(self):
        return '{0} by {1} posted on {2}, rated {3}'.format(self.title,self.author,self.date,self.rating)

    def fetch_content(self):
        # init content string
        _content = ''
        # for each page
        for i in range(1,self.page_count+1):
            # get soup of each page
            soup = get_soup(self.link + '?page={}'.format(i))
            # get content
            content  = soup.find('div',{ 'class' : 'b-story-body-x'})
            # add content to _content
            _content += str(content)
        # add content to object
        self.content = _content

    def write(self,prefix,rel_path):
        # open a file with title as name
        with open('{0}/{1}_{2}.html'.format(rel_path,prefix,self.title),'w') as f:
            f.write(HTML_HEADER)
            # writer heading
            f.write('<h1>{}</h1>\n'.format(self.title))
            f.write('<span class="info"><span class="rating-static rating-{}"></span>'.format(int(self.rating_as_float * 10)) )
            f.write('by <a href={0}>{1}</a> &nbsp;on &nbsp;{2}</span>'.format(self.author_home,self.author,self.date))
            # rating
            f.write('<br><br>{}\n'.format(self.content))
            f.write('{0}<a href="{1}">Read at literotica</a></div><br><br>&nbsp;'.format(HTML_FOOTER,self.link))


def get_soup(url=BASE_URL):
    # raw content
    content = requests.get(url).content
    # soup
    return bsp(content,"lxml")

# Get all categories
def get_categ_links(url=BASE_URL):
    soup =  get_soup(url=BASE_URL)
    links = []
    names = []
    for item in soup.find_all('a'):
        if '/c/' in item.get('href'):
            links.append(item.get('href'))
            names.append(item.text)

    return links, names

# For each category, find max number of pages
#   CATE_BASE_URL
def get_max_pages(url,suffix='/1-page'):
    soup = get_soup(url + suffix)
    links = soup.find_all('div', {'class': 'b-pager-pages'})
    if 'option' in str(links):
        return int(re.findall(r'<option[^>]*>([^<]+)</option>',str(links))[-1])
    else:
        return int(1)

# Get page links in each category
def util_get_pages(url, max_page):
    return ['{}/{}-page'.format(url,i) for i in range(1,max_page+1)]

# Get Story objects
def get_stories(page_links):
    stories = []
    i = 1
    # for each page link
    for link in page_links:
        soup = get_soup(link)
        # find all matching tags
        tags = soup.findAll('div', { 'class' : 'b-sl-item-r'})
        for tag in tags:
            # create object
            story = Story(tag)
            print('[{0}] {1}'.format(i,story))
            # append to list
            stories.append(story)
            i += 1
    return stories

# Get story links from each page in each category
def get_story_links(page_links):
    links = []
    i = 1
    for page in page_links:
        soup = get_soup(page)
        for item in soup.find_all('a'):
            _href = item.get('href')
            if '/s/' in _href and _href not in links:
                links.append(_href)
                print('[{0}] {1}'.format(i,_href))
                i += 1
    return links

def util_get_tag(item_as_str,tag):
    return re.findall(r'<{0}[^>]*>([^<]+)</{0}>'.format(tag),item_as_str)

def util_get_href(item_as_str):
    return re.findall(r'<a href="([^<]+)">',item_as_str)
    
# Get title, content, author name, author link and TODO(comments) of a story
def get_contents(story):
    soup = get_soup(story)
    header = str(soup.find_all('div',{'class' : 'b-story-header'})[0])
    _heading = str(util_get_tag(header,'h1')[0]).replace('/','')
    _author  = str(util_get_tag(header,'a')[0])
    _author_home  = str(util_get_href(header)[0])

    # get contents from all pages
    max_pages = get_max_pages(story,suffix='')
    _content = ''
    for i in range(1,max_pages+1):
        soup = get_soup(story + '?page={}'.format(i))
        content  = soup.find_all('div',{ 'class' : 'b-story-body-x'})[0]
        # inplace sort
        _content += str(content)

    return Story(_heading, _content, _author, _author_home)

# write story to file
def util_write_story(story,rel_path):
    with open('{0}/{1}.html'.format(rel_path,story.title),'w') as f:
        f.write('<h1>{}</h1>\n'.format(story.title))
        f.write('<i><a href={0}>{1}</a></i>\n'.format(story.author_home,story.author))
        f.write('{}\n'.format(story.content))

def get_batch_prefixes(stories):
    prefixes = []
    prefix = 1
    count = 0
    # page counts of all stories
    page_counts = [story.page_count for story in stories]
    for i in range(len(page_counts)):
        count += page_counts[i]
        prefixes.append(prefix)
        if count > 150:
            count = 0
            prefix += 1
    return prefixes

def util_write_stories(stories,prefixes,category):
    for story,prefix in zip(stories,prefixes):
        story.write(prefix,category)
    

# MAIN
if __name__ == '__main__':
    categories, category_names = get_categ_links()
    # create folders for each category
    print('Getting directories for categories')
    '''
    for item in category_names:
        if not os.path.exists(item):
            os.makedirs(item)
    '''
    category = categories[0]
    # get count of pages
    max_page = get_max_pages(categories[0])
    # get links to all pages
    print('Getting links to all pages')
    page_links = util_get_pages(categories[0],max_page)
    # get all Story objects
    stories = get_stories(page_links)
    # separate stories into batches based on page count
    batches = get_batches(stories)
    print('Len : {}'.format(len(stories)))
    print('Batches : {}'.format(batches))

    '''
    # get links to all stories
    print('Getting links to all stories')
    story_links = get_story_links(page_links)

    print('Acquiring stories')
    i = 1
    # for each story
    for story in story_links:
        # get contents
        _story = get_contents(story)
        print('[{0}] {1}'.format(i,_story.title))
        # write contents to file
        util_write_story(_story,category_names[0])
        i += 1
    '''
