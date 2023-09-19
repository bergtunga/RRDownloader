
import os
import string
import re
import requests
from bs4 import BeautifulSoup as bs
from source.epub_writer import EpubWriter

def _from_file(name):
    result = None
    with open('./assets/' + name, mode='r', encoding='UTF-8') as stream:
        result = stream.read()
    return result

def scrape(url):
    return requests.get(url, timeout=30)

class Chapter:
    '''Functional class. Total garbage'''
    _id_list = []

    @staticmethod
    def reset_class():
        Chapter._id_list = []

    def __init__(self, name, url):
        self.url = 'https://www.royalroad.com' + url
        self.name = str(name).strip()
        self.sanitized_name = sanitized_name_temp = re.sub(r'[\W]+', '_', self.name)
        # It was a huge pain to try to sanitize appropiately using
        #  escape from xml.sax.saxutils, so a simpler way was simply
        #  to replace all non alpha-numeric characters (regex: \W)
        i = 2
        while self.sanitized_name in Chapter._id_list:
            self.sanitized_name = sanitized_name_temp+'_' + str(i)
        Chapter._id_list.append(self.sanitized_name)
        # Then ensure no conficts for internal IDs.
        self.soup = None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'Chapter ' + self.name + ' @ ' + str(self.url)

    def get_author_info(self):
        if self.data_soup is None:
            raise Exception('Data not yet retrieved')
        soup = self.data_soup
        tag = soup.find('i', class_='fa fa-info-circle')
        #This finds the information circle icon that preceeds the bio.
        bio = tag.parent.text.strip()
        if bio == 'Bio:' :
            bio = None
        img = soup.find('div', class_='avatar-container-general').img.attrs['src']
        return (bio, img)

    def get_data(self):
        data = scrape(self.url)
        soup = self.data_soup = bs(data.text, 'html.parser')
        #   Retrieve webpage & make soup

        content = soup.find('div', class_='chapter-inner chapter-content')
        notes = soup.find_all('div', class_='portlet-body author-note')
        #   Get chapter contents
        #TODO: Fix 'spoilers' in notes, content

        soup = self.soup = bs(_from_file('basic.xhtml'),'html.parser')
        #   Once contents are isolated, get the template xhtml document

        if len(notes) == 0:
            soup.div.replace_with(content)
        elif len(notes) == 1:
            tag = soup.new_tag('div')
            # Make a new tag for the chapter content and both author's notes

            test = notes[0].parent.next_sibling
            while test != content and test is not None:
                test = test.next_sibling
            # Determine if the author's note comes before chapter content

            if test == content:
                tag.append(notes[0])
                tag.append(content)
                # If the note comes before the content, add it before the content.
            else:
                tag.append(content)
                tag.append(notes[0])
                # Otherwise, add the note after the chapter content.

            soup.div.replace_with(tag)
            # Add the tag with the chapter data.
        else: #elif len(notes) == 2
            tag = soup.new_tag('div')
            tag.append(notes[0])
            tag.append(content)
            tag.append(notes[1])
            soup.div.replace_with(tag)

        soup.title.string = self.name
        #   Substitute the content and name into the template

        #   Now the content of the chapter can be accessed from chapter.soup

    def write_data(self):
        if self.soup is None:
            raise Exception('Data not yet retrieved')
        with open(
            self.sanitized_name + '.xhtml',
            mode='w',
            encoding='utf-8'
        ) as file:
            file.write(self.soup.prettify())
            #print(self.soup.prettify())

        print(self.name + '.xhtml written')

class BookDownloader:
    '''Another garbage functional class'''
    _BROKEN_IMAGE_TEXT_START = '<?xml version="1.0" encoding="UTF-8"?><Error><Code>NoSuchBucket'
    _brokenImage = None
    with open('./assets/brokenImage.jpg', 'rb') as image:
        _brokenImage = image.read()

    def __init__(self, book_num, single_chapter = -1):
        print('Finding', book_num)
        url = 'https://www.royalroad.com/fiction/' + str(book_num)
        page = None
        try:
            page = scrape(url)
        except:
            pass
        if page is None:
            raise ConnectionError(
                'Unable to connect to server.\nCheck your internet connection and try again.'
            )
        if page.status_code == 404:
            raise RuntimeError('Story '+book_num+' does not exist.')
        if page.status_code == 522:
            raise ConnectionError('Royal Road is down')


        Chapter.reset_class()

        self.single_chapter = single_chapter
        # Integers initialized

        title_soup = bs(page.text, 'html.parser')       # Get the webpage of the indicated book.
        self._chapter_list = []                         # List of chapters
        self._toc_soup = None                           # BeautifulSoup for Table of Contents
        self._images = dict()                           # Dictionary of images in book
        self.author_info = None                         # Tuple ( bio, image_address)
        # Objects Initialized

        self.url = url
        self.author = title_soup.find('meta', property='books:author').attrs['content']
        # Get the author of the book.
        self.description = title_soup.find(class_='description').text.strip()
        # Get the description of the book.
        self.book_name = title_soup.title.string[:-13]  # Get name of the book from page title.
        self.book_num = book_num
        self.save_name = None
        self._date_updated = None
        # Strings Initialized
        self._epub_writer = EpubWriter(self.book_name)

        # All variables are now initialized

        table = title_soup.table.find_all('td')
        for row in table[::2]:
            self._chapter_list.append(Chapter(row.text, row.find('a').get('href')))
        #   Get the chapters of the book by searching the table data.

        for row in table[1::2]:
            try:
                self._date_updated = row.time.attrs['title']
            except:
                pass
        if self._date_updated is not None:
            _d = self._date_updated.split()
            # date = f'{_d[3]$$-_d[1]:02$$-_d[2]:02}'
            self._date_updated = _d[3]+'-'+month_number(_d[1])+'-'+_d[2].strip(string.punctuation).rjust(2,'0')
        else:
            self._date_updated = '1980-01-01'
        # Go through the table data, and grab the date of the latest data. Then format appropiately.

        if single_chapter == -1:
            print('Downloading', len(self._chapter_list), 'chapters of book', self.book_name, 'from RoyalRoad')
        else:
            print('Downloading chapter from index', single_chapter,
                  'of book', self.book_name, 'From RoyalRoad')
        # Notify user of what's happening

        self._epub_writer.create()

        # Chapter Retrieval #######################################
        self._toc_soup = bs(_from_file('toc.xhtml'), 'html.parser')
        # Create the Table of Contents file
        if single_chapter != -1 :
            item = self._chapter_list[single_chapter]
            self._do_chapter(item)
            self.author_info = item.get_author_info()
        else :
            i = 0
            for item in self._chapter_list:
                self._do_chapter(item, place = i)
                i += 1
            self.author_info = self._chapter_list[0].get_author_info()
        #   The chapter contents are now written
        self._epub_writer.write_toc(self._toc_soup.prettify())
        #   Add table of contents to epub
        ###########################################################

        self._epub_writer.write_style()

        # Cover ###################################################
        cover_addr = title_soup.find('div', class_ ='cover-art-container').img.attrs['src']
        img_name = self._retrieve_image(cover_addr)[0]
        #   Get cover

        self._epub_writer.write_cover(img_name)
        #   Get cover file, edit, add to epub
        ###########################################################

        img_address = self.author_info[1]
        author_image = self._retrieve_image(img_address)[0]
        self._epub_writer.write_index(self.author, self.author_info[0], author_image)
        self._epub_writer.write_metadata(self.author,self.description, book_num, self._date_updated)
        self._epub_writer.close()

    def _do_chapter(self, chapter, place = 0):
        if self.single_chapter == -1 :
            print('Getting index '+str(place) + '/' + str(len(self._chapter_list)-1),
                  'chapter', chapter.name)
        else:
            print('Getting chapter', chapter.name)
        chapter.get_data()
        self._epub_writer.push_chapter('', chapter.name, chapter.sanitized_name, place)
        # Prep chapter-specific data for manifest, spine, and navigation.

        chapter_tag = self._toc_soup.new_tag('li')
        chapter_link_tag = self._toc_soup.new_tag('a', href=(chapter.sanitized_name+'.xhtml'))
        chapter_link_tag.append(chapter.name)
        chapter_tag.append(chapter_link_tag)
        self._toc_soup.ol.append('\n')
        self._toc_soup.ol.append(chapter_tag)
        # Add to Table of Contents
        imgs = chapter.soup.find_all('img')
        # Get all the images in the chapter
        for img_tag in imgs:
            # Process every image
            if 'src' not in img_tag.attrs:
                continue # if there isn't an image, skip

            img_tag.attrs['src'] = self._retrieve_image(img_tag.attrs['src'])[0]

        # All images have now been processed.
        self._epub_writer.write_chapter(chapter.sanitized_name, chapter.soup.prettify())

    def _retrieve_image(self, rsc_addr):
        if rsc_addr is None:
            return None
        if rsc_addr[0] == '/' :
            rsc_addr = 'https://www.royalroad.com' + rsc_addr

        if not '.gstatic.com/images?' in rsc_addr:
            rsc_addr = rsc_addr.partition('?')[0]
            # Sanitize address, unless hosted on gstatic.

        if rsc_addr in self._images:
            return self._images[rsc_addr]
        # If already retrieved, return.

        ext = os.path.splitext(rsc_addr)[1]
        # split extension

        if ext == '.png':
            media_close = '" media-type="image/png" />\n'
        elif ext == '.gif':
            media_close = '" media-type="image/gif" />\n'
        elif ext == '.svg':
            media_close = '" media-type="image/svg+xml" />\n'
        else: # Assume JPG otherwise
            media_close = '" media-type="image/jpeg" />\n'
        # Determine extension info.

        name = 'Images/' + str(len(self._images)) + ext
        identity = 'img' + str(len(self._images))
        resource = ''
        try:
            resource = scrape(rsc_addr).content
            # Get the resource
            if str(resource)[2:100].startswith(BookDownloader._BROKEN_IMAGE_TEXT_START):
                print('Royal Road image broken: ', rsc_addr)
                resource = BookDownloader._brokenImage

        except requests.exceptions.ConnectionError as error:
            print(error)
            resource = BookDownloader._brokenImage
            #if the image cannot be loaded, use a broken image icon
            print('Unable to retrieve image: ', rsc_addr)

        self._epub_writer.write_resource(name, resource, identity, media_close)

        self._images[rsc_addr] = (name, identity)
        return self._images[rsc_addr]

def month_number(month):
    '''converts month str into 2 digit month'''
    switcher = {
        'January':'01',
        'February':'02',
        'March':'03',
        'April':'04',
        'May':'05',
        'June':'06',
        'July':'07',
        'August':'08',
        'September':'09',
        'October':'10',
        'November':'11',
        'December':'12'
    }
    return switcher.get(month, '0')

# chapter test
"""
test = chapter("Chapter 30: Demon Feast","/fiction/26534/vainqueur-the-dragon/chapter/417768/30-demon-feast")
print(test)
test.get_data()
print(test.get_author_info())
#test.write_data()
#"""
# book_downloader test
# book_downloader("00000", 0)
