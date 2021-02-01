Last Updated 1.Feb.2021
# Make sure to donate to any authors you appreciate!
## RRDownloader
The goal of this project is to create .epub v3 files that are compatible with v2 systems, by downloading works from RoyalRoad. This was more of a personal project rather than something for mass adoption, as sometimes I want reread books that authors take down for various reasons. Furthermore, it was a small but non-trivial introduction to python. This project has taught me about python documentation, the libraries BeautifulSoup4 and requests, the format/documentation of .epub and formatting of .xhtml files, as well as a bit about python style choices.

## Requirements
This requires the requests library as well as beautifulsoup4 to be installed to run. These can be installed by running
```shell
$ git clone https://github.com/Goobabtc/RRDownloader.git
Cloning into 'RRDownloader'...

$ cd RRDownloader/
$ pip3 install -r requirements.txt

OR

$ pipenv install && pipenv shell
```

The program depends on the following **Python 3** modules:
```python3
requests>=2.20.0
beautifulsoup4>=4.9.1
```
Older versions may work, but are untested.

### What is pip & why it is used?
(included because I didn't know this before this project)
pip is the package manager included with python by default in the scripts subfolder of the python directory.
pip takes less setup than pipenv, though pipenv allows different versions of the same module to be installed for different projects.
For example, it may be installed in `Program Files\Python\Python38\Scripts`
Python **will NOT** recognize packages pip installs, unless
	a) you install as an administrator, or 
	b) you add your **local** Scripts folder to your Environment path e.g.(`C:\Users\USERNAME\AppData\Roaming\Python\Python38\Scripts`)

The difference between pip and pip3 is pip3 is for Python3, whereas pip guesses python version to install for based on context. If you only have one install of python it shouldn't matter.

**[Click here](https://pip.pypa.io/en/stable/)** for detailed pip documentation.

## Current execution
Run `RRTool -l` to list .epub files in the current directory, and to open it using the system default application.
Run `RRTool -d ######` to download a book from RR, where ###### is the 6 digit number following /fiction/ in the book's url.
Run `RRTool -d ###### -s #` to download a single chapter, where 0 is the first chapter.
Run `RRTool -do ######` to download and open the book.

## Possible feature additions
If anyone expresses interest, I may be motivated to implement the following features:
In order of decending priority
	
	#TODO: Implement qt-based user experience with graphics.
	#TODO:FIX: table width in author comments
	#TODO:FIX: 'Spoiler' tags do not expand.
	#TODO: implement reuse: ability to update previously created epubs
	#TODO:FIX: chapter numbering issues

# Make sure to donate to any authors you appreciate!