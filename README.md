## Usage
Clone repository or copy/paste the python script

```bash
git clone https://github.com/Mitchell-jpg/cloudflare_ddns.git
```

Allow the script to execute

```bash
sudo chmod +x cloudflare_ddns.py
sudo chmod +x ddns.js
```

This script is used with crontab. Specify the frequency of execution through crontab.

```bash
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of the month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday 7 is also Sunday on some systems)
# │ │ │ │ │ ┌───────────── command to issue                               
# │ │ │ │ │ │
# │ │ │ │ │ │
# * * * * * /usr/bin/python /path/to/my_script
```
