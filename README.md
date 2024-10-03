## Usage
Clone repository or copy/paste the python script

```bash
git clone https://github.com/Mitchell-jpg/cloudflare_ddns.git
```

Allow the script to execute

```bash
sudo chmod +x cloudflare_ddns.py
```

Interface



![image](https://github.com/user-attachments/assets/4882e820-213c-4af3-8e9e-8034570fa302)

After initial setup which will consist of entering the API key and other domain information, a pickle file will be created that will save the instance.

With the pickle file created from initial setup, you may now scheduele the script to run via crontab:

```bash
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of the month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday 7 is also Sunday on some systems)
# │ │ │ │ │ ┌───────────── command to issue                               
# │ │ │ │ │ │
# │ │ │ │ │ │
# * * * * * /usr/bin/python3 /path/to/clouflfare_ddns.py --name "yourdomain.com"
```
