'''TODO: replace with dedicated package someone else spent effort working on'''
import sys
import abc
from typing import TextIO, Callable, Iterator
import zipfile
import re
from datetime import datetime
from xml.sax.saxutils import escape
from typing_extensions import Self
from bs4 import BeautifulSoup as bs, NavigableString

def _parse_mediatype(ext: str) -> str:
    if ext == '.xhtml':
        return 'application/xhtml+xml'
    elif ext == '.png':
        return 'image/png'
    elif ext == '.gif':
        return '"image/gif'
    elif ext == '.svg':
        return 'image/svg+xml'
    elif ext == '.css':
        return 'text/css'
    elif ext == '.ncx':
        return 'application/x-dtbncx+xml'
    else: # Assume JPG otherwise
        return 'image/jpeg'

def _from_file(name: str) -> str:
    result = None
    with open('./assets/' + name, mode="r", encoding="UTF-8") as stream:
        result = stream.read()
    return result

class EpubException(Exception):
    '''Raised when parsing invalid source template files'''
    pass

class _EpubResourceManifests(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, __subclass: type) -> bool:
        return  (super().__subclasshook__(cls)
            and hasattr(__subclass, 'get_ext')   and callable(__subclass.get_ext)
            and hasattr(__subclass, 'get_idref') and callable(__subclass.get_idref)
            and hasattr(__subclass, 'get_short_name') and callable(__subclass.get_short_name)
            and hasattr(__subclass, 'get_play_order') and callable(__subclass.get_play_order)
            and hasattr(__subclass, 'get_nav_text') and callable(__subclass.get_nav_text)
            and hasattr(__subclass, 'get_data')     and callable(__subclass.get_data)
            or NotImplemented
        )

    @abc.abstractmethod
    def get_spine_priority(self) -> int:
        '''An int representing the priority for item order when adding to the spine'''
        raise NotImplementedError

    @abc.abstractmethod
    def get_nav_text(self) -> str:
        '''The string to display for clicking when navigating to this item'''
        raise NotImplementedError

    @abc.abstractmethod
    def get_ext(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_idref(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_short_name(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_data(self) -> str|bytes:
        raise NotImplementedError

    def get_additional_props(self) -> str:
        return ''

    def get_name(self) -> str:
        return self.get_short_name() + self.get_ext()

    def get_manifest(self) -> str:
        id_ref = self.get_idref()
        if id_ref == '':
            return ''
        result = '<item id="'
        result += id_ref
        result += '"'
        props = self.get_additional_props()
        if props != '':
            result += ' '
            result += props
        result += ' href="'
        result += self.get_name()
        result += '" media-type="'
        result += _parse_mediatype(self.get_ext())
        result += '" />'
        return result

    def get_nav(self, play_order: int) -> str:
        nav_text = self.get_nav_text()
        if nav_text == '':
            return ''
        return '<navPoint id="navpoint-' + self.get_idref() + '" playOrder="' + str(play_order) + '"><navLabel><text>' + escape(self.get_nav_text()) + '</text></navLabel><content src="' + self.get_name() + '"/></navPoint>'

    def get_spine(self) -> str:
        pri = self.get_spine_priority()
        if pri <= 0:
            return ''
        return '<itemref idref="' + self.get_idref() + '"/>'

class _ItemGroup:
    def __init__(self) -> None:
        self._item_dict: dict[int, list[_EpubResourceManifests]] = {}
        self.strat: Callable[[_EpubResourceManifests], bool] = lambda _: True

    def list_with_strat(self, strat: Callable[[_EpubResourceManifests], bool]) -> list[_EpubResourceManifests]:
        self.strat = strat
        result = list(self)
        self.strat = lambda _: True
        return result
    
    def append(self, item: _EpubResourceManifests) -> None:
        pri = item.get_spine_priority()
        if pri not in self._item_dict:
            self._item_dict[pri] = []
        self._item_dict[pri].append(item)

    def __iter__(self) -> Iterator[_EpubResourceManifests]:
        priorities = list(self._item_dict.keys())
        priorities.sort()
        for key in priorities: # iterate in priority order
            for item in self._item_dict[key]:
                if self.strat(item):
                    yield item

class EpubImage(_EpubResourceManifests):
    '''Represents an image to be added to an epub'''
    def __init__(self, data: str|bytes, ext: str, identity: str) -> None:
        super().__init__()
        self._data = data
        self._ext = ext
        self._identity = identity

    def get_idref(self) -> str:
        return 'img' + self._identity

    def get_short_name(self) -> str:
        return 'Images/' + self._identity
    
    def get_ext(self) -> str:
        return self._ext

    def get_nav_text(self) -> str:
        return ''

    def get_spine_priority(self) -> int:
        return 0

    def get_data(self) -> str|bytes:
        return self._data

class EpubChapter(_EpubResourceManifests):
    '''Represents a chapter to be added to an epub'''
    def __init__(self, name: str, sanitized_name: str, place: int, contents: str) -> None:
        super().__init__()
        self._name = name
        self._sanitized_name = sanitized_name
        self._place = place
        self._contents = contents

    def get_spine_priority(self) -> int:
        return 4

    def get_nav_text(self) -> str:
        return self._name

    def get_short_name(self) -> str:
        return self._sanitized_name

    def get_ext(self) -> str:
        return '.xhtml'

    def get_idref(self) -> str:
        return 'CHAPTER' + self._sanitized_name

    def get_data(self) -> str|bytes:
        return self._contents

    def get_raw_name(self) -> str:
        return self._name

class TableOfContents(_EpubResourceManifests):
    '''Represents the TOC to be added to an epub'''
    def __init__(self) -> None:
        super().__init__()
        soup = bs(_from_file('toc.xhtml'), 'html.parser')
        if soup.ol is None:
            raise EpubException('invalid toc')
        self._toc_soup: bs = soup

    def get_nav_text(self) -> str:
        return 'Table of Contents'

    def get_spine_priority(self) -> int:
        return 3

    def get_short_name(self) -> str:
        return 'toc'

    def get_ext(self) -> str:
        return '.xhtml'

    def get_idref(self) -> str:
        return 'toc'

    def get_data(self) -> str|bytes:
        return self._toc_soup.prettify()

    def get_additional_props(self) -> str:
        return 'properties="nav"'

    def push_chapter(self, chapter: EpubChapter) -> None:
        chapter_tag = self._toc_soup.new_tag('li')
        chapter_link_tag = self._toc_soup.new_tag('a', href=chapter.get_name())
        chapter_link_tag.append(chapter.get_raw_name())
        chapter_tag.append(chapter_link_tag)
        self._toc_soup.ol.append('\n') # type: ignore[union-attr]
        self._toc_soup.ol.append(chapter_tag) # type: ignore[union-attr]

class EpubCover(_EpubResourceManifests):
    '''cover'''
    def __init__(self, img: str|None, book_name: str) -> None:
        super().__init__()
        cover_soup = bs(_from_file('cover.xhtml'), 'html.parser')
        if cover_soup.img is None:
            raise EpubException('bad cover.xhtml')
        if img is not None:
            cover_soup.img.attrs['src'] = img
        else:
            cover_soup.img.decompose()
        self._data = cover_soup.prettify()
        self._book_name = book_name

    def get_nav_text(self) -> str:
        return self._book_name

    def get_spine_priority(self) -> int:
        return 1

    def get_short_name(self) -> str:
        return 'cover'

    def get_ext(self) -> str:
        return '.xhtml'

    def get_idref(self) -> str:
        return 'cover'

    def get_data(self) -> str|bytes:
        return self._data

class _EpubAuthorPage(_EpubResourceManifests):
    def __init__(self, book_name: str, author: str|None, author_bio: str|None, author_image: str|None) -> None:
        super().__init__()
        self._index_soup = index_soup = bs(_from_file('index.xhtml'), 'html.parser')
        index_title = index_soup.title
        index_mouseover = index_soup.find('div', class_="book")
        index_bold = index_soup.find('strong')
        index_img = index_soup.img
        index_header =index_soup.find('h2')
        desc_soup = index_soup.find('div', class_="author-description")
        if ((index_img is None) or
            (index_title is None) or
            (index_mouseover is None) or (isinstance(index_mouseover, NavigableString)) or
            (index_bold is None) or (isinstance(index_bold, NavigableString)) or
            (desc_soup is None) or (isinstance(desc_soup, NavigableString)) or
            (index_header is None) or (isinstance(index_header, NavigableString))):
            raise EpubException('invalid index.xhtml')

        index_title.string = book_name
        index_mouseover.attrs['title'] = book_name
        index_bold.string = book_name

        if author is None:
            index_header.decompose()
        else:
            index_header.string = "By: " + author

        if author_bio is None:
            desc_soup.decompose()
        else:
            desc_soup.string = author_bio

        if author_image is None:
            index_img.decompose()
        else:
            index_img.attrs['src'] = author_image

    def get_nav_text(self) -> str:
        return 'About Author'

    def get_spine_priority(self) -> int:
        return 2

    def get_short_name(self) -> str:
        return 'author'

    def get_ext(self) -> str:
        return '.xhtml'

    def get_idref(self) -> str:
        return 'author'

    def get_data(self) -> str|bytes:
        return self._index_soup.prettify()

class _EpubNcx(_EpubResourceManifests):
    '''toc.ncx indicates the proper order of the book'''
    def __init__(self, book_name: str, author: str|None, book_id: str, items: _ItemGroup) -> None:
        super().__init__()
        self._author = '' if author is None else author
        self._book_name = book_name
        self._items = items
        self._book_id = book_id

    def get_data(self) -> str|bytes:
        ncx_addition = ''
        play_order = 1
        for item in self._items.list_with_strat(lambda item: item.get_spine_priority() != 0):
            ncx_addition += item.get_nav(play_order) + '\n '
            play_order += 1

        return _from_file('toc_template.ncx').format(
                                    book_num = self._book_id,
                                    book_name = self._book_name,
                                    author = self._author,
                                    ncx_chapter_string = ncx_addition)

    def get_spine_priority(self) -> int:
        return 0 # no nav

    def get_nav_text(self) -> str:
        return '' # no nav

    def get_ext(self) -> str:
        return '.ncx'

    def get_idref(self) -> str:
        return 'ncx'

    def get_short_name(self) -> str:
        return 'toc'

class _EpubOpf(_EpubResourceManifests):
    '''content.opf lists all the contents of the book.'''
    def __init__(self,
                 book_name: str,
                 author: str|None,
                 book_id: str,
                 items: _ItemGroup,
                 description: str|None,
                 updated_date: str,
            ) -> None:
        super().__init__()
        self._author = '' if author is None else author
        self._description = '' if description is None else description
        self._date_updated = updated_date
        self._book_name = book_name
        self._items = items
        self._book_num = book_id

    def get_data(self) -> str|bytes:
        spine_addition = ''
        for item in self._items.list_with_strat(lambda item: item.get_spine_priority() != 0):
            spine_addition += item.get_spine() + '\n '
        manifest_addition = ''
        for item in self._items:
            manifest_addition += item.get_manifest() + '\n '

        return _from_file('content_template.opf').format(
                                    book_name = self._book_name,
                                    author = self._author,
                                    description = self._description,
                                    date_updated = self._date_updated,
                                    date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    manifest_chapter_string = manifest_addition,
                                    spine_string = spine_addition,
                                    book_num = self._book_num
                                 )

    def get_spine_priority(self) -> int:
        return 0

    def get_ext(self) -> str:
        return '.opf'

    def get_idref(self) -> str:
        return ''

    def get_short_name(self) -> str:
        return 'content'

    def get_nav_text(self) -> str:
        return ''

class EpubStyle(_EpubResourceManifests):

    def get_data(self) -> str:
        return _from_file("RRStyle.css")

    def get_spine_priority(self) -> int:
        return 0

    def get_nav_text(self) -> str:
        return ''

    def get_ext(self) -> str:
        return '.css'

    def get_idref(self) -> str:
        return 'RRStyle'

    def get_short_name(self) -> str:
        return 'Styles/RRStyle'

class EpubWriter:
    '''writes epubs'''
    def __init__(self, book_name: str, log: TextIO = sys.stdout) -> None:
        self.log = log
        self.book_name = book_name
        self._epub_file: zipfile.ZipFile
        self._toc = TableOfContents()
        self._item_group = _ItemGroup()

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
        initialized_file = None
        while initialized_file is None:
            try:
                if i == 0 :
                    save_name = sanitized_name + ".epub"
                else:
                    save_name = sanitized_name+str(i) + ".epub"
                initialized_file = self._epub_file = zipfile.ZipFile(
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

        #   mimetype cannot be compressed.
        self._epub_file.writestr(
            'mimetype',
            'application/epub+zip',
            compress_type=zipfile.ZIP_STORED
        )
        self._epub_file.writestr('META-INF/container.xml', _from_file('container.xml'))

        return save_name

    def push_item(self, item: _EpubResourceManifests) -> Self:
        self._item_group.append(item)
        return self

    def complete(self,
                 author: str|None,
                 author_bio: str|None,
                 author_image: str|None,
                 description: str|None,
                 book_id: str,
                 updated_date: str
            ) -> None:
        self.push_item(_EpubNcx(self.book_name, author, book_id, self._item_group))
        self.push_item(EpubStyle())
        self.push_item(_EpubAuthorPage(
            book_name=self.book_name,
            author=author,
            author_bio=author_bio,
            author_image=author_image
            ))
        self.push_item(_EpubOpf(self.book_name, author, book_id, self._item_group, description, updated_date))
        for item in self._item_group:
            self._epub_file.writestr('OEBPS/' + item.get_name(), item.get_data())
        self._epub_file.close()


    def _log_status(self, string: str) -> None:
        print('epub_writer:' + string, file=self.log)
