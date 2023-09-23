#!/usr/bin/python
import sys
import os
import pathlib
import platform
import subprocess
import argparse
from source.rr_dwnldr import BookDownloader

def main() -> None:
    '''Start me from the command line. Either provide "arguments" in-code or from cmd line'''
    parser = bootstrap_arguments()
    args = parser.parse_args()
    #args = parser.parse_args(['d', '12345'])
    if args.op is None:
        parser.print_help()
        return
    if args.op in ('l', 'list'):
        list_books()
        return
    if args.op in ('download', 'd'):
        specific_chapter = -1 if 'single' not in vars(args) else 0 if args.single is None else args.single
        try:
            book = BookDownloader(args.id, specific_chapter)
        except ConnectionError as c_e:
            print(c_e.args[0])
        except RuntimeError:
            print('The story you entered does not exist!')
        if args.open:
            open_sys(book.save_name)
        return
    print('unexpected error: unrecognized operation')
    return

def list_books() -> None:
    books_tmp = pathlib.Path().glob('*.epub')
    books = list(books_tmp)
    if len(books) == 0 :
        print("You haven't downloaded any books!")
    else:
        for i, book in enumerate(books):
            print(i, end='')
            print(' ', book)
        i = -1
        while i == -1:
            r = input('Enter the number of the book you wish to open, or enter to quit.\n')
            if r == '':
                i = -2
            else:
                try:
                    i = int(r)
                    if i >= len(books) or i < 0:
                        print('That book does not exist.')
                        i = -1
                except:
                    print('Enter a number')

        if i != -2 :
            open_sys(str(books[i]))

def open_sys(file: str) -> None:
    opsys = platform.system()

    if opsys == 'Linux':
        # Untested
        subprocess.call(('xdg-open', file))
    elif opsys == 'Darwin':
        # Untested
        subprocess.call(('open', file))
    elif opsys == 'Windows':
        os.startfile(file) # type: ignore[attr-defined]
    else:
        print('System type unsupported - assuming *nix varient')
        subprocess.call(('xdg-open', file))

def bootstrap_arguments() -> argparse.ArgumentParser:
    '''Sets up an argument parser for the tool'''
    parser = argparse.ArgumentParser(
        prog='RRTool.py',
        usage='pipenv run %(prog)s',
        description='Download stories from RoyalRoad.com'
    )
    subparsers = parser.add_subparsers(
        title='usage',
        description='this can be used to list epubs in the current directory or to download and create a new epub',
        help='list or download',
        metavar='download|list',
        dest='op')
    download = subparsers.add_parser(
        'download',
        prog='download',
        aliases=['d'],
        help='downloads a book from RoyalRoad and saves as an epub'
    )
    subparsers.add_parser(
        'list',
        prog='list',
        aliases=['l'],
        help='list books in current directory'
    )
    download.add_argument(
        '-o', '--open',
        action='store_true',
        help='open after downloading. Only valid with -d option'
    )
    download.add_argument(
        '-s', '--single',
        metavar='index',
        nargs='?',
        type=int,
        default=argparse.SUPPRESS,
        help='only download one chapter (defaults to first chapter)'
    )
    download.add_argument(
        'id',
        help='id can be found after "fiction/" in the URL'
    )
    return parser

main()
