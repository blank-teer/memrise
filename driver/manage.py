from selene.api import browser
from selenium import webdriver

chrome_driver = {
    "location": "driver/chromedriver.exe"
}

chrome_user_data = {
    "location": "",
}


def configure():
    r"""
    Prerequisites:
    1) set chrome_driver's location whose value should point to chrome driver (https://chromedriver.chromium.org/)
    2) comment --user-data-dir and --profile-directory options adding
    3) run your python script and stop it when chrome has opened
    4) find out newly created chrome user data directory
       (in Windows its location look as C:\Users\%USERNAME%\AppData\Local\Temp\scoped_dir*)
    5) paste the path toward this directory as value of --user-data-dir option
    6) uncomment commented earlier options

    Now it will be used persistent chrome profile that retains any cache, cookies, etc. for the further runs.
    """
    o = webdriver.ChromeOptions()
    o.add_argument("--user-data-dir=" + chrome_user_data["location"])
    o.add_argument("--profile-directory=Default")
    o.add_argument("--start-maximized")

    selenium_driver = webdriver.Chrome(executable_path=chrome_driver["location"], options=o)
    browser.set_driver(selenium_driver)


def run_configured(url: str):
    configure()
    browser.open_url(url)


def restart(url: str):
    browser.close()
    run_configured(url)
