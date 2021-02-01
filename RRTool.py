#!/usr/bin/python
import sys
import os
import pathlib
import platform
import subprocess
import rr_dwnldr

def main():
    if len(sys.argv) == 1:
        """
        Print help
        """
        print("This is used to download stories from RoyalRoad.com")
        print("Use:python RRTool.py [-l] [-d ##### [-s #]]")
        print('\t-l or --list to list books in current directory')
        print('\t-d or --download ##### to download book')
        print('\t-do ##### to download and open book')
        print('\t-s # can be specified after a download option to only retrieve one chapter')
        print('The number can be found after "fiction/" in the URL')
    elif sys.argv[1] == '-l' or sys.argv[1] == '--list':
        list_books()
    elif sys.argv[1] == '-d' or sys.argv[1] == '--download' or sys.argv[1] == '-do':
        try:
            if len(sys.argv) == 5:
                if sys.argv[3] != '-s':
                    print("Unexpected argument", sys.argv[3])
                else:
                    err = False
                    i = None
                    try:
                        i = int(sys.argv[4])
                    except:
                        err = True
                    if err:
                        print("-s must specify an integer")
                    else:
                        book = rr_dwnldr.book_downloader(sys.argv[2], i)
                        if sys.argv[1] == '-do':
                            open_sys(book.save_name)
            elif len(sys.argv) == 4 and sys.argv[3] == '-s':
                print("-s must specify an integer")
            elif len(sys.argv) != 3:
                print("The download must include only the book ID")
            else:
                book = rr_dwnldr.book_downloader(sys.argv[2])
                if sys.argv[1] == '-do' :
                    open_sys(book.save_name)
        except ConnectionError:
            print('Unable to connect to server.\nCheck your internet connection and try again.')
        except RuntimeError:
            print("The story you entered does not exist!")

def list_books():
    books_tmp = pathlib.Path().glob("*.epub")
    books = []
    for i in books_tmp:
        books.append(i)
    if len(books) == 0 :
        print("You haven't downloaded any books!")
    else:
        for i in range(len(books)):
            print(i, end="")
            print(" ", books[i])
        i = -1
        while i == -1:
            r = input('Enter the number of the book you wish to open, or just type enter to quit.\n')
            if r == "":
                i = -2
            else:
                try:
                    i = int(r)
                    if i >= len(books) or i < 0:
                        print("That book does not exist.")
                        i = -1
                except:
                    print("Enter a number")
        
        if i != -2 :
            open_sys(books[i])
        
def open_sys(file):
    opsys = platform.system()
        
    if(opsys == 'Linux'):
        """-Untested-"""
        subprocess.call(('xdg-open', file))
    elif(opsys == 'Darwin'):
        """-Untested-"""
        subprocess.call(('open', file))
    elif(opsys == 'Windows'):
        os.startfile(file)
    else:
        print('System type unsupported - assuming *nix varient')
        subprocess.call(('xdg-open', file))


main()
