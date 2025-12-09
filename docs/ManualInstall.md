# Manual Install

It is highly recommended that you use the Docker Container. However, if you prefer to install the application directly,
that can be done. It may require adjusting some of the paths that the application is using to look for label and 
config files.

## Install

Get the code:

    git clone https://github.com/cvergaray/label_web.git

or download [the ZIP file](https://github.com/cvergaray/label_web/archive/master.zip) and unpack it.

Install the requirements:

    pip install -r requirements.txt

In addition, `fontconfig` should be installed on your system. It's used to identify and
inspect fonts on your machine. This package is pre-installed on many Linux distributions.
If you're using a Mac, I recommend to use [Homebrew](https://brew.sh) to install
fontconfig using [`brew install fontconfig`](http://brewformulas.org/Fontconfig).

## Configuration

Details regarding the configuration file are the same as [the main documentation](../README.md#configuration-file).

## Startup

To start the server, run `./brother_ql_web.py`. The command line parameters overwrite the values configured in `config.json`. Here's its command line interface:

    usage: brother_ql_web.py [-h] 
                             [--port PORT] 
                             [--loglevel LOGLEVEL]
                             [--font-folder FONT_FOLDER]
    
    This is a web service to print labels on label printers.
    
    optional arguments:
      -h, --help            show this help message and exit
      --port PORT
      --loglevel LOGLEVEL
      --font-folder FONT_FOLDER
                            folder for additional .ttf/.otf fonts
