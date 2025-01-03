#!/bin/bash

# Clone all github.com repositories for a specified user.

if [ $# -eq 0 ]
  then
    echo "Usage: $0 <user_name> "
    exit;
fi

USER=$1
git config --global url."https://".insteadOf git://



for repo in `curl -s https://api.github.com/users/$USER/repos?page=1 |grep git_url |awk '{print $2}'| sed 's/"\(.*\)",/\1/'`;do
git clone $repo;
done;

for repo in `curl -s https://api.github.com/users/$USER/repos?page=2 |grep git_url |awk '{print $2}'| sed 's/"\(.*\)",/\1/'`;do
git clone $repo;
done;

for repo in `curl -s https://api.github.com/users/$USER/repos?page=3 |grep git_url |awk '{print $2}'| sed 's/"\(.*\)",/\1/'`;do
git clone $repo;
done;
for repo in `curl -s https://api.github.com/users/$USER/repos?page=4 |grep git_url |awk '{print $2}'| sed 's/"\(.*\)",/\1/'`;do
git clone $repo;
done;