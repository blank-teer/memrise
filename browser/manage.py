from selene.api import browser
from selenium import webdriver

chrome_driver = {
    "location": "browser/driver/chromedriver.exe"
}

chrome_profile = {
    "location": "browser/profile/chromeprofile",
}


def configure():
    """
    Prerequisites:
    - download chrome driver compatible with chrome version of yours
      and put it 'driver' folder. (https://chromedriver.chromium.org/)
    """
    o = webdriver.ChromeOptions()
    o.add_argument("--user-data-dir=" + chrome_profile["location"])
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
