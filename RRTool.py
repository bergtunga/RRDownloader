#!/usr/bin/python
import sys
import os
import pathlib
import platform
import subprocess
from source.rr_dwnldr import BookDownloader

def main():
    '''Start me from the command line. Either provide "arguments" in-code or from cmd line'''
    # argumentList = ['', '-d', '12345']
    argumentList = sys.argv # TODO: bring in argument parser
    if len(argumentList) == 1:
        # Print help
        print('This is used to download stories from RoyalRoad.com')
        print('Use:python RRTool.py [-l] [-d ##### [-s #]]')
        print('\t-l or --list to list books in current directory')
        print('\t-d or --download ##### to download book')
        print('\t-do ##### to download and open book')
        print('\t-s # can be specified after a download option to only retrieve one chapter')
        print('The number can be found after "fiction/" in the URL')
    elif argumentList[1] == '-l' or argumentList[1] == '--list':
        list_books()
    elif argumentList[1] == '-d' or argumentList[1] == '--download' or argumentList[1] == '-do':
        try:
            if len(argumentList) == 5:
                if argumentList[3] != '-s':
                    print('Unexpected argument', argumentList[3])
                else:
                    err = False
                    i = None
                    try:
                        i = int(argumentList[4])
                    except:
                        err = True
                    if err:
                        print('-s must specify an integer')
                    else:
                        book = BookDownloader(argumentList[2], i)
                        if argumentList[1] == '-do':
                            open_sys(book.save_name)
            elif len(argumentList) == 4 and argumentList[3] == '-s':
                print('-s must specify an integer')
            elif len(argumentList) != 3:
                print('The download must include only the book ID')
            else:
                book = BookDownloader(argumentList[2])
                if argumentList[1] == '-do' :
                    open_sys(book.save_name)
        except ConnectionError as e:
            print(e.args[0])
        except RuntimeError:
            print('The story you entered does not exist!')

def list_books():
    books_tmp = pathlib.Path().glob('*.epub')
    books = []
    for i in books_tmp:
        books.append(i)
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
            open_sys(books[i])

def open_sys(file):
    opsys = platform.system()

    if opsys == 'Linux':
        # Untested
        subprocess.call(('xdg-open', file))
    elif opsys == 'Darwin':
        # Untested
        subprocess.call(('open', file))
    elif opsys == 'Windows':
        os.startfile(file)
    else:
        print('System type unsupported - assuming *nix varient')
        subprocess.call(('xdg-open', file))


main()
