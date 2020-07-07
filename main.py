import json
import os
from datetime import datetime
import time

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# from dotenv import load_dotenv
# load_dotenv()

if 'DYNO' not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()
else:
    SECRETS = json.loads(os.getenv('SECRETS'))
    with open('client_secrets.json', 'w') as f:
        json.dump(SECRETS, f)

    CRED = json.loads(os.getenv('CRED'))
    with open('creds.txt', 'w') as f:
        json.dump(CRED, f)

USERNAME = os.getenv('SIMPLI_USERNAME')
PASSWORD = os.getenv('SIMPLI_PASSWORD')


FOLDER = os.getenv('FOLDER')
FORMAT = os.getenv('FORMAT')

TIMEOUT = int(os.getenv('TIMEOUT'))
DURATION = int(os.getenv('DURATION'))

CHROME_PATH = os.getenv('CHROME_PATH')
DRIVER_PATH = os.getenv('DRIVER_PATH')

with open("record.js", "r") as file:
    RECORDJS = file.read()

gdrive = ""
driver = ""


def driveAuth():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("creds.txt")
    if gauth.credentials is None:
        gauth.CommandLineAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("creds.txt")
    drive = GoogleDrive(gauth)
    return drive


def browserInit():
    cwd = os.path.dirname(os.path.abspath(__file__))
    prefs = {'download.default_directory': cwd +
             "\\", 'download.prompt_for_download': False}

    chrome_options = Options()

    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    if 'DYNO' in os.environ:
        chrome_options.add_experimental_option('prefs', prefs)
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.binary_location = str(CHROME_PATH)
    else:
        chrome_options.add_experimental_option(
            "debuggerAddress", "127.0.0.1:9222")

    chrome_driver = DRIVER_PATH
    driver = webdriver.Chrome(
        executable_path=str(DRIVER_PATH), chrome_options=chrome_options, desired_capabilities=caps)
    driver.set_script_timeout(999)

    return driver


def isLoggedIn():
    currentUrl = driver.current_url
    if "login" in currentUrl:
        return False
    else:
        return True


def isPlaying():
    try:
        stream = driver.find_element_by_tag_name('video')
        src = stream.get_attribute("src")
        if "blob" in src:
            return True
        else:
            return False
    except NoSuchElementException:
        return False


def isCameraConnected():
    try:
        driver.find_element_by_class_name("camera-disconnected")
        return False
    except NoSuchElementException:
        return True


def deleteFile(file):
    while os.path.exists(file):
        try:
            os.remove(file)
        except Exception as e:
            print(e)


def login():
    print("[LOGGING IN]")
    loggedIn = False
    driver.get('https://webapp.simplisafe.com/#/login')
    try:
        element = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "ss-standard-button"))
        )
    except TimeoutException:
        print("[PAGE TIMED OUT]")
        driver.quit()
    username = driver.find_element_by_class_name("email")
    username.clear()
    username.send_keys(USERNAME)
    password = driver.find_element_by_class_name("password")
    password.clear()
    password.send_keys(PASSWORD)
    driver.find_element_by_class_name("ss-standard-button").click()

    while not loggedIn:
        driver.save_screenshot("screenshot.png")
        file = gdrive.CreateFile(
            {'parents': [{'id': FOLDER}]})
        file.SetContentFile("screenshot.png")
        try:
            file.Upload()
        finally:
            file.content.close()
        deleteFile("screenshot.png")
        time.sleep(15)
        loggedIn = isLoggedIn()

    driver.get("https://webapp.simplisafe.com/new/#/cameras")

    play()

    return True


def play():
    driver.refresh()

    playing = False
    print("[PLAYING STREAM]")

    try:
        element = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "transparent-panel"))
        )
    except TimeoutException:
        print("[PAGE TIMED OUT]")
        driver.quit()

    driver.find_element_by_class_name("transparent-panel").click()

    while not playing:
        playing = isPlaying()

    return True


def convertToMP4(filename):
    command = "ffmpeg -i recording.mkv -c copy -c:a aac -movflags +faststart " + \
        str(filename) + ".mp4"
    os.system(command)
    deleteFile("recording.mkv")
    return filename


def getFolderID():
    folderName = datetime.now().strftime("%d-%m-%Y")
    folders = gdrive.ListFile(
        {"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()

    for folder in folders:
        if folder['title'] == folderName:
            return folder['id']

    folderMeta = {'title': folderName,
                  'mimeType': 'application/vnd.google-apps.folder', 'parents': [{'id': FOLDER}]}

    folder = gdrive.CreateFile(folderMeta)
    folder.Upload()

    return folder['id']


def upload(filename):
    folderID = getFolderID()
    file = gdrive.CreateFile(
        {'parents': [{'id': folderID}]})
    file.SetContentFile(filename + ".mp4")

    try:
        file.Upload()
    finally:
        file.content.close()

    deleteFile(filename + ".mp4")


def recordMotion():
    print("[RECORDING MOTION]")
    filename = datetime.now().strftime(FORMAT)

    print("[CAPTURING STREAM]")
    driver.execute_async_script(RECORDJS, DURATION*1000)

    print("[CONVERTING TO MP4]")
    convertToMP4(filename)

    print("[UPLOADING TO DRIVE]")
    upload(filename)
    print("[FINISHED CAPTURE]")


def main():
    while True:
        motion = False

        if(isLoggedIn()):
            if(isPlaying() and isCameraConnected()):
                motion = False
                for entry in driver.get_log('performance'):
                    if "Motion" in str(entry):
                        motion = True
                        break
            else:
                if(not isCameraConnected()):
                    time.sleep(5)
                play()
        else:
            login()

        if motion:
            recordMotion()


if __name__ == "__main__":
    print("[GOOGLE DRIVE AUTH]")
    gdrive = driveAuth()

    print("[INITIALISING BROWSER]")
    driver = browserInit()
    login()

    try:
        main()
    except KeyboardInterrupt:
        print("[KEYBOARD INTERRUPT]")
