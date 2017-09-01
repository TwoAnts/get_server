# Get Server #  
To get my laboratory's server.  
No use for others.  

## Requirements ##   
- beautifulsoup4 
- python-dateutil

## Usage ## 
1. `pip install python-dateutil beautifulsoup4` 
2. Modify the end of __get_server.py__
    ```
    mlog('='*45)
    try:
        ins_id = 'ca15'           #Your target name
        tl = timedelta(seconds=600)
        username = 'M201672711'   #Your username
        passwd = '123456'         #Your passwd
        sleep_to_apply_one(ins_id, tl, username, passwd)
    except Exception as e:
        mlog(traceback.format_exc())
    mlog('='*45)
    ```
3. `crontab -e`
    ```
    0 7 * * * /\<dir_path\>/get_server/get_server.py     #execute at 7:00 everyday
    57 6 * * * /\<dir_path\>/get_server/clean_log.py     #execute at 6:57 everyday
    @reboot /\<dir_path\>/get_server/get_server.py       #execute at reboot
    ```

