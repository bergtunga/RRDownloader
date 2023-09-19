'''TODO: replace with dedicated package someone else spent effort working on'''
import sys
import zipfile
import re
from datetime import datetime
from xml.sax.saxutils import escape
from bs4 import BeautifulSoup as bs

def _from_file(name):
    result = None
    with open('./assets/' + name, mode="r", encoding="UTF-8") as stream:
        result = stream.read()
    return result

class EpubWriter:
    '''writes epubs'''
    def __init__(self, book_name, log = sys.stdout):
        self.log = log
        self.book_name = book_name
        self._epub_file = None
        self._manifest_addition = ''
        self._ncx_addition = ''
        self._spine_addition = ''

    def create(self):
        '''Create the epub file'''
        i = 0
        sanitizedName = re.sub(r"""['"{}\/\\<>`!@#$%&*\-_+\s|?=:]+""", ' ', self.book_name, 1000000)
        while self._epub_file is None:
            try:
                if i == 0 :
                    self.save_name = sanitizedName + ".epub"
                else:
                    self.save_name = sanitizedName+str(i) + ".epub"
                self._epub_file = zipfile.ZipFile(self.save_name, 'w',
                                    compression=zipfile.ZIP_DEFLATED,
                                    compresslevel=6)
        # ZIP_DEFLATED is used for for standard .zip files.
        # compresslevel=6 matches Z_DEFAULT_COMPRESSION from
        # https://docs.python.org/3/library/zlib.html#zlib.compressobj
        # and overrides the default None value.
        #   *Not sure if None equates to 0 or aforementioned default
            except PermissionError:
                if i < 10 :
                    i += 1
                else:
                    raise
        # Assign self.save_name, self._epub_file.
        self._log_status('making epup ' + self._epub_file.filename)

        self._epub_file.writestr(
            'mimetype',
            'application/epub+zip',
            compress_type=zipfile.ZIP_STORED
        )
        #   mimetype cannot be compressed.
        self._epub_file.writestr('META-INF/container.xml', _from_file('container.xml'))
        #   meta-inf
        #   The basic metadata for the .epub is now written.

    def write_toc(self,contents):
        self._epub_file.writestr('OEBPS/toc.xhtml', contents)

    def write_chapter(self, sanitized_name,  contents):
        self._epub_file.writestr('OEBPS/' + sanitized_name + ".xhtml", contents)

    def write_style(self):
        self._epub_file.writestr('OEBPS/Styles/RRStyle.css', _from_file("RRStyle.css"))

    def write_cover(self, img):
        cover_soup = bs(_from_file('cover.xhtml'), 'html.parser')
        cover_soup.img.attrs['src'] = img
        self._epub_file.writestr('OEBPS/cover.xhtml', cover_soup.prettify())

    def write_index(self, author, author_bio, author_image):
        index_soup = bs(_from_file('index.xhtml'), 'html.parser')
        index_soup.title.string = self.book_name
        index_soup.find('div', class_="book").attrs['title'] = self.book_name
        index_soup.find('strong').string = self.book_name
        index_soup.find('h2').string = "By: " + author

        bio = author_bio
        if bio is None:
            index_soup.find('div', class_="author-description").decompose()
        else:
            index_soup.find('div', class_="author-description").string = bio

        index_soup.img.attrs['src'] = author_image

        self._epub_file.writestr('OEBPS/index.xhtml', index_soup.prettify())

    def write_metadata(self, author, description, book_id, updated_date):
        '''Writes the files enumerating content and ordering'''
        #   content.opf lists all the contents of the book.
        self._epub_file.writestr('OEBPS/content.opf',
                                _from_file('content_template.opf').format(
                                    book_name = self.book_name,
                                    author = author,
                                    description = description,
                                    date_updated = updated_date,
                                    date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    manifest_chapter_string = self._manifest_addition,
                                    spine_string = self._spine_addition,
                                    book_num = book_id
                                 )
                                )

        #   toc.ncx indicates the proper order of the book.
        self._epub_file.writestr('OEBPS/toc.ncx',
                                _from_file('toc_template.ncx').format(
                                    book_num = book_id,
                                    book_name = self.book_name,
                                    author = author,
                                    ncx_chapter_string = self._ncx_addition)
                                )

    def push_manifest(self, *content):
        self._manifest_addition += ''.join(content)

    def push_spine(self, *content):
        self._spine_addition += ''.join(content)

    def push_nav(self, *content):
        self._ncx_addition += ''.join(content)

    def push_chapter(self, chapter_content, name, sanitized_name, place):
        self.push_manifest(' <item id="CHAPTER', sanitized_name,
                           '" href="', sanitized_name,
                           '.xhtml" media-type="application/xhtml+xml" />\n')
        self.push_spine('\n <itemref idref="CHAPTER', sanitized_name, '"/>')
        self.push_nav('<navPoint id="id', str(place),
                      '" playOrder="', str(4 + place),
                      '"><navLabel><text>', escape(name),
                      '</text></navLabel><content src="', sanitized_name,
                      '.xhtml"/></navPoint>\n')

    def write_resource(self, name, resource, identity, media_close):
        self._epub_file.writestr('OEBPS/' + name, resource)
        self.push_manifest(' <item id="'+identity+'" href="'+ name + media_close)

    def close(self):
        self._epub_file.close()


    def _log_status(self, string):
        print('epub_writer:' + string, file=self.log)
