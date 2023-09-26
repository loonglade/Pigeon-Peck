# Pigeon-Peck

<img src="https://github.com/loonglade/Pigeon-Peck/blob/main/assets/images/logo.png" height="250">

A tiny app that notifies you of new youtube videos from channels you subscribe to without the need for an account.

It uses Selenium with a user_agent profile randomizer to fetch youtube channels data without the need for the Youtube API.

#### Install required libraries (You also need tkinter):

    git clone https://github.com/loonglade/Pigeon-Peck.git
    cd pigeon-peck
    pip install -r requirements.txt

#### This app has only been tested on MacOS, although it should work on Linux and Windows.
Linux might need libsndfile1 installed:
    
    sudo apt-get install libsndfile1

#### Warning
This code has only been tested on Python 3.9.
