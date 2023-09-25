from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from pytube import Playlist
from config import *
import argparse
import glob
import os


def get_video_urls(playlist_urls):
    urls = []

    for playlist in playlist_urls:
        all_video = Playlist(playlist)

        for url in all_video[:90]:
            urls.append(url)

    return urls


def download_sub(driver, page_url, video_url, save_path, rename, time_out=120):
    print("Downloading audio subtitle from YouTube...")
    driver.get(page_url)
    link_input = driver.find_element(by=By.TAG_NAME, value="input")

    link_input.send_keys(video_url)
    link_input.send_keys(Keys.ENTER)

    wait = WebDriverWait(driver, 30)
    srt_button = wait.until(EC.visibility_of_element_located((By.XPATH, download_sub_button_xpath)))
    srt_button.click()

    "Check if file is downloaded completely"
    dl_wait = True
    seconds = 0

    while dl_wait and seconds < time_out:
        sleep(1)
        files = os.listdir(save_path)
        dl_wait = False
        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True
        seconds += 1

    print("Download subtitle completed!")
    list_of_files = glob.glob(save_path + "/*")
    latest_file = max(list_of_files, key=os.path.getctime)
    os.rename(latest_file, os.path.join(save_path, rename + '.srt'))


def download_audio(driver, page_url, video_url, save_path, rename, time_out=120):
    print("Downloading audio from YouTube...")
    driver.get(page_url)
    link_input = driver.find_element(by=By.ID, value="videoUrl")

    link_input.send_keys(video_url)
    link_input.send_keys(Keys.ENTER)

    wait = WebDriverWait(driver, 30)
    audio_type_button = wait.until(EC.visibility_of_element_located((By.XPATH, audio_type_button_xpath)))
    audio_type_button.click()
    wav_button = driver.find_element(by=By.XPATH, value=wav_xpath)
    wav_button.click()
    "Check if file is downloaded completely"
    dl_wait = True
    seconds = 0

    while dl_wait and seconds < time_out:
        sleep(1)
        files = os.listdir(save_path)
        dl_wait = False
        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True
        seconds += 1
    print("Download audio completed!")
    list_of_files = glob.glob(save_path + "/*")
    latest_file = max(list_of_files, key=os.path.getctime)
    os.rename(latest_file, os.path.join(save_path, rename + '.wav'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_dir",
                        type=str,
                        help="path to the save directory", default='/home/artorias/PycharmProjects/CrawlData/downloads')
    parser.add_argument("--file",
                        type=str,
                        help="path to the txt file which contains all playlist_url",default = 'all_urls.txt')
    args = parser.parse_args()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    p = {"download.default_directory": args.save_dir}
    chrome_options.add_experimental_option(name="prefs", value=p)
    chrome_driver = webdriver.Chrome(options=chrome_options)

    with open(args.file) as f:
        all_playlist_urls = f.readlines()
        all_video_urls = get_video_urls(all_playlist_urls)
    f.close()

    for idx, line in enumerate(all_video_urls):
        print(f'File {idx + 1}/{len(all_video_urls)}----------------')
        download_sub(chrome_driver, download_sub_page_url, line, args.save_dir, str(idx))
        download_audio(chrome_driver, download_audio_page_url, line, args.save_dir, str(idx))

    chrome_driver.quit()
