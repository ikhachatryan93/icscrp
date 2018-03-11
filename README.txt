CONTENT
        1. INTRODUCTION
        2. FILE MANIFEST
        3. INSTALLATION
        4. USAGE

1. INTRODUCTION

The README file for ico profile scraper.
From configs.txt you can increase the number of threads, which will increase the speed.

2. FILE MANIFEST

data/icons/                  : the output folder for logos
data/csv_data/               : the output folder for backup csv files

Note: After scraper is done you can see the scraped profiles data in csv format, in /data/csv_data/[source_name], and final processed and merged data in data/csv_data/total/


utilities/drivers/           : drivers for phanthomjs, chrome and firefox needed by selenium framework
utilities/logging.py         : script to setup logging
utilities/mysql_wrapper.py   : wrapper for sending data to mysql db
utilities/proxies.txt        : file which contains proxies, please keep at least 30 stable proxies as scraper uses proxy rotation to pass bot detectors
utilities/proxy_generator.py : free proxy scraper, do not ues this as we already understand free proxies are bad idea
utilities/utils.py           : utils for scrapers e.g config parser, mysql utils, driver setup etc.

Note: After scraper is done you can see logs/*****.log file for the logs


scrapers/base_scraper.py     : base scraper class which implements multitasking tricks
scrapers/data_keys.py        : the file which contains the mapping of names in DB and in scrapers
scrapers/icobazaar.py        : scraper for icobazaar, is disable as working very slow due to multitasking issues
scrapers/icobench.py         : scraper for icobench, uses proxy rotation
scrapers/icodrops.py         : scraper for icodrops
scrapers/icomarks.py         : scraper for icomarks
scrapers/icorating.py        : scraper for icorating
scrapers/tokentops.py        : scraper for tokentops
scrapers/trackico.py         : scraper for trackico, uses proxy rotation
scrapers/bitcointalk.py      : scraper for bitcointalk, uses proxy rotation
scrapers/reddit.py           : scraper for reddit
scrapers/telegram.py         : scraper for telegram, uses proxy rotation


configs.txt/       : configuration file for the scraper tool

extractor.py/      : main executable script

scripts/setup.sh   : setup bash script which install dependencies


3. INSTALLATION

Windows: 
    Install python 3.5:
    - Download and install python3. When installing enable "Add python3 to PATH" checkbox.
    - Download and install firefox browser
    Install python modules:
    - run scripts/setup.bat

Linux (Ubuntu):
    Install python and modules from terminal:
    - open linux terminal
    > sudo scripts/setup.sh

4. USAGE 

Open terminal and run: 
    
    - update 'max_thread' and db info in configs.ini file
    > python3 extractor.py (ATTENTION: this script will scrape and update db once, for permanent run setup jobs in your server)

Note: this will run scrapers in 'while true' mode, run_loop.sh is taking argument (in seconds) for delaying between each db update. (e.g. /run_loop.sh  360 will wait 6 minutes)
