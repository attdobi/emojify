#!/bin/bash

if ps -ef | grep -v grep | grep twitter_mine_SQL ; then
        exit 0
else
        #/home/user/bin/doctype.php >> /home/user/bin/spooler.log &
        #mailing program
	#echo "restarting emoji_mine"
        #cpulimit --limit 50 nice python /home/ubuntu/emojify/emoji_mine_aws.py #"emojipy was not running...  Restarted."
        python /home/ubuntu/emojify/Mine/twitter_mine_SQL.py #restarting twitter mine
	#tasket -c 0 command #limits process to core number 0
	#nice also limits python usage when another intense program opens
exit 0
fi
