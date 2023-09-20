'''TODO: replace with dedicated package someone else spent effort working on'''
import sys
from typing import TextIO
import zipfile
import re
from datetime import datetime
from xml.sax.saxutils import escape
from bs4 import BeautifulSoup as bs, NavigableString

class EpubException(Exception):
    pass

def _from_file(name: str) -> str:
    result = None
    with open('./assets/' + name, mode="r", encoding="UTF-8") as stream:
        result = stream.read()
    return result

class EpubWriter:
    '''writes epubs'''
    def __init__(self, book_name: str, log: TextIO = sys.stdout) -> None:
        self.log = log
        self.book_name = book_name
        self._epub_file: zipfile.ZipFile
        self._manifest_addition = ''
        self._ncx_addition = ''
        self._spine_addition = ''

    def create(self) -> str:
        '''Create the epub file'''
        i = 0
        save_name: str
        sanitized_name = re.sub(
            r"""['"{}\/\\<>`!@#$%&*\-_+\s|?=:]+""",
            ' ',
            self.book_name,
            1000000
        )
        isInit = None
        while isInit is None:
            try:
                if i == 0 :
                    save_name = sanitized_name + ".epub"
                else:
                    save_name = sanitized_name+str(i) + ".epub"
                isInit = self._epub_file = zipfile.ZipFile(
                    save_name,
                    'w',
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=6
                )
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
        if self._epub_file.filename is None:
            self._log_status('Epub missing name somehow?')
        else:
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
        return save_name

    def write_toc(self, contents: str) -> None:
        self._epub_file.writestr('OEBPS/toc.xhtml', contents)

    def write_chapter(self, sanitized_name: str,  contents: str) -> None:
        self._epub_file.writestr('OEBPS/' + sanitized_name + ".xhtml", contents)

    def write_style(self) -> None:
        self._epub_file.writestr('OEBPS/Styles/RRStyle.css', _from_file("RRStyle.css"))

    def write_cover(self, img: str|None) -> None:
        cover_soup = bs(_from_file('cover.xhtml'), 'html.parser')
        if cover_soup.img is None:
            raise Exception('bad cover.xhtml')
        if img is not None:
            cover_soup.img.attrs['src'] = img
        else:
            cover_soup.img.decompose()
        self._epub_file.writestr('OEBPS/cover.xhtml', cover_soup.prettify())

    def write_index(self, author: str|None, author_bio: str|None, author_image: str|None) -> None:
        index_soup = bs(_from_file('index.xhtml'), 'html.parser')
        try:
            index_soup.title.string = self.book_name  # type: ignore[union-attr]
            index_soup.find('div', class_="book").attrs['title'] = self.book_name # type: ignore[union-attr]
            index_soup.find('strong').string = self.book_name # type: ignore[union-attr]
            if author is not None:
                index_soup.find('h2').string = "By: " + author # type: ignore[union-attr]
            else:
                self._log_status('No author')
        except AttributeError as error:
            raise EpubException('invalid index.xhtml') from error

        desc_soup = index_soup.find('div', class_="author-description")
        if desc_soup is None or isinstance(desc_soup, NavigableString):
            raise EpubException('invalid index.xhtml')
        if author_bio is None:
            desc_soup.decompose()
        else:
            desc_soup.string = author_bio

        index_img = index_soup.img
        if index_img is None:
            raise EpubException('invalid index.xhtml')
        if author_image is not None:
            index_img.attrs['src'] = author_image
        else:
            index_img.decompose()

        self._epub_file.writestr('OEBPS/index.xhtml', index_soup.prettify())

    def write_metadata(self, author: str|None, description: str|None, book_id: str, updated_date: str) -> None:
        '''Writes the files enumerating content and ordering'''
        author = '' if author is None else author
        description = '' if description is None else description
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

    def push_manifest(self, *content: str) -> None:
        self._manifest_addition += ''.join(content)

    def push_spine(self, *content: str) -> None:
        self._spine_addition += ''.join(content)

    def push_nav(self, *content: str) -> None:
        self._ncx_addition += ''.join(content)

    def push_chapter(self, chapter_content: str, name: str, sanitized_name: str, place: int) -> None:
        self.push_manifest(' <item id="CHAPTER', sanitized_name,
                           '" href="', sanitized_name,
                           '.xhtml" media-type="application/xhtml+xml" />\n')
        self.push_spine('\n <itemref idref="CHAPTER', sanitized_name, '"/>')
        self.push_nav('<navPoint id="id', str(place),
                      '" playOrder="', str(4 + place),
                      '"><navLabel><text>', escape(name),
                      '</text></navLabel><content src="', sanitized_name,
                      '.xhtml"/></navPoint>\n')

    def write_resource(self, name: str, resource: bytes, identity: str, media_close: str) -> None:
        self._epub_file.writestr('OEBPS/' + name, resource)
        self.push_manifest(' <item id="'+identity+'" href="'+ name + media_close)

    def close(self) -> None:
        self._epub_file.close()


    def _log_status(self, string: str) -> None:
        print('epub_writer:' + string, file=self.log)
