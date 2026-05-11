## brawl elo tracker

wat is this bradar:
this tracks the brawl stars competitive ELO in a cool graph yayayayayayayay

## how to install:

1: get the api key

1- enter https://developer.brawlstars.com
2- register
3- go to my account and new key
4- add a name
5- get ur ipv4 and put it in there, bc it wont work otherwise lol
6- get the token

btw if u have a dynamic ip (ip changes) uhh js do ts step again lmao (exept the registring)

2: configure the .env

change the name of .env.example to .env

add ur stuff on: 

BRAWL_API_KEY= the token from the previous step
PLAYER_TAG=# ur tag

3: install dependencies

u lowk need python for this, so js download python and after, paste this on the cmd from the folder:
pip install -r requirements.txt

it will install everything u need

4: run the server

do the following command on the console
python server.py
and open the html
everything should work ig


## what if ts doesnt work??

if it doesnt work, Brawl stars changed the API or:
HTTP 403: you put the IP wrong when setting up the key
HTTP 404: wrong player tag
or maybe my coding is ass idk maybe the last one

how to add to OBS:

1- in OBS, add a browser source
2- add as an URL either "http://localhost:6767" (lol) or the html file
3- configure it to have 500 width and 280 height
4- deactivate the following stuff:
    - Shutdown source when not visible
    - Refresh browser when scene becomes active
5- put it wherever you want

enjoy i guess
