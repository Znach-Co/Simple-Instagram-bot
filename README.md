# Simple-Instagram-bot
A simple Instagram bot for daily use, to like, follow, unfollow and automate your Instagram actions. Ready to use!


Feel free to maintain and help good tools grow. :point_down:

<a href="https://www.buymeacoffee.com/2gcAduieV" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>


How to use:
-
- Install Python from https://www.python.org/downloads/ (download exe file version 3.6 or 3.7)
- Install pip (https://www.liquidweb.com/kb/install-pip-windows/)
- Unzip archive 
- open cmd
- cd path_to_unzip_folder/SimpleBot
- pip install -r requirements.txt
- check config.json file (open it with Notepad or other text editor), save and close

To run bot:
- open cmd
- cd path_to_unzip_folder/SimpleBot
- python main.py 


For pro users:
-
- update config.json
- python main.py



___________________________

Config.json

Example:
        
        {"credentials": {
            "user": "username",
            "password": "password"
          },
        "limitsPerHour":{ 
            "follow": 20, 
            "unfollow": 20, 
            "like": 40, 
            "unlike": 0 
          }, 
          "hashtags": ["insta","happy", "fun", "instagram", "likeforlike"], 
          "process": "Like-and-follow", /* "Like-and-follow" or "Like"*/ <- This parameter varies 
          "duration": { 
            "type": "by_time", /* "by_time" or "by_users" */ <- This parameter varies
            "value": "2"  /* "X" hrs or "X" users */ <- This parameter varies 
          } ,
        "whiteList": ["freddy", "@freddy_johnson"] /*array of user names which won't be unfollowed (with @ or without)*/
        }
        
        Explanation:
        If "process":"Like-and-follow", "duration": "by_users" or "by_time"
                                        "value": "X" users or "X" hrs
                                      
        If "process":"Like", "duration": "by_likes" or "by_time"
                                         "value": "X" likes or "X" hrs                                
_________
