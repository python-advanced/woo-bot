import time
from playsound import playsound
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, ElementNotInteractableException, \
    ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options

使用 = 'chrome'  # 可以把這邊改成'firefox'

每次對話開始時延遲時間 = 2  # 單位 秒
傳每則訊息的延遲時間 = 1
等待訊息的時間 = 150  # 單位不是秒，可自行調整
留下關鍵字播放音檔 = 'NOTIFY.WAV'
錯誤時播放音檔 = 'tindeck_1.mp3'
驅動程式 = 'geckodriver_firefox.exe'
驅動程式第二 = 'chromedriver.exe'

預設訊息 = [
    '您好',
    '感謝您搭乘長榮航空',
    '祝您旅途愉快',
    '期待再次與您相會'
]

跳過關鍵字 = [
    '嗎',
    '嗨嗨'
]

留下關鍵字 = [
    '嗨',
    '您好'
]


class Scrapper(object):
    def __init__(self):
        if 使用 == 'firefox':
            geckoPath = 驅動程式
            self.browser = webdriver.Firefox(executable_path=geckoPath)
        else:
            chromedriver = 驅動程式第二
            opts = Options()
            opts.add_argument("--incognito")
            self.browser = webdriver.Chrome(executable_path=chromedriver)

        self.browser.get('https://wootalk.today/')
        self.對方訊息 = []
        self.left = False
        self.wait_time = 傳每則訊息的延遲時間

    def run(self):
        """ 執行流程 """
        self.click_chat()
        while True:
            time.sleep(每次對話開始時延遲時間)  # 每次結束等待兩秒 換下一個人
            被擋 = self.detect_blocked()
            if 被擋:
                print('被擋了，請人為解除')
                input('解除後回到 新的聊天(已經開始聊天)再按enter')
            self.left = False
            self.click_chat()
            self.chat()
            self.leave()

    def click_chat(self):
        """ 按下開始聊天 """
        try:
            selected = self.browser.find_element_by_xpath('//*[@id="startButton"]')
            if selected:
                selected.click()
        except ElementNotInteractableException:
            return

    def send_chat(self, m):
        """ 把訊息打上去 """
        selected = self.browser.find_element_by_xpath('//*[@id="messageInput"]')
        selected.clear()
        selected.send_keys(m)

    def click_send(self):
        """ 按下送出 """
        selected = self.browser.find_element_by_xpath('//*[@id="sendButton"]/input')
        selected.click()

    def check_leave(self):
        """ 檢查對方離開 """
        selected = self.browser.find_element_by_xpath('//*[@id="sendButton"]/input')
        if selected.get_attribute('value') == '回報':
            return True
        return False

    def leave(self):
        """ 離開 """
        try:
            self.click_leave()
            if not self.left:  # 自己主動離開
                while True:
                    selected = self.browser.find_element_by_xpath('//*[@id="popup-yes"]')
                    if not selected:
                        time.sleep(0.1)
                        continue
                    selected.click()
                    break
        except ElementNotInteractableException:
            return

    def click_leave(self):
        try:
            selected = self.browser.find_element_by_xpath('//*[@id="changeButton"]/input')
            selected.click()
        except ElementClickInterceptedException:
            print('caught ElementClickInterceptedException when clicking leave')

    def get_stranger_text(self):
        selected = self.browser.find_elements_by_class_name('stranger')
        return [d.text for d in selected]

    def clean_stranger_text(self, text):
        new_text = []
        for t in text:
            if t == '(剛剛)':
                continue
            t = t.replace('\n(剛剛)', '')
            t = t.replace('\n(\n行動裝置\n剛剛)', '')
            t = t.replace('\n', '')
            t = t.replace('(App剛剛)', '')
            if t == '(行動裝置剛剛)' or not t:
                continue
            new_text.append(t)

        return new_text

    def detect_blocked(self):
        selected = self.browser.find_elements_by_class_name('system')
        for d in selected:
            if '要繼續使用，請開啟此連結' in d.text:
                return True
        return False

    def wait_for_msg(self):
        print('等待對方講話中')
        wait_c = 0
        while True:
            if self.check_leave():
                print('發現對方離開了')
                self.left = True
                return

            try:
                data = self.get_stranger_text()
                data = self.clean_stranger_text(data)

                typing = False
                for d in data:
                    if '打字中' in d:
                        typing = True

                if typing:
                    time.sleep(1)
                    continue

                if data != self.對方訊息:
                    self.對方訊息 = data
                    return
                time.sleep(0.1)
                wait_c += 1
                if wait_c >= 等待訊息的時間:
                    print('等太久都沒訊息了，不等了')
                    return
            except StaleElementReferenceException:
                print('caught exceptions')
                continue

    def chat(self):
        """ 聊天訊息流程 """
        time.sleep(每次對話開始時延遲時間)
        c = 0
        self.wait_for_msg()
        for 訊息 in 預設訊息:
            c += 1
            time.sleep(self.wait_time)

            if c != 1:
                self.wait_for_msg()

            if self.check_leave():
                print('發現對方離開了')
                self.left = True
                return

            print(self.對方訊息)  # 印出所有對方訊息

            for d in self.對方訊息:
                skip = False
                for t in 跳過關鍵字:
                    if t in d:
                        skip = True
                if skip:
                    print('遇到   跳過關鍵字，換下一個人')
                    time.sleep(2)
                    return

                stay = False
                for t in 留下關鍵字:
                    if t in d:
                        stay = True

                if stay:
                    playsound(留下關鍵字播放音檔)
                    input('遇到  留下關鍵字，請接手，按ENTER即換下一個人')
                    return

                # 例外情況   如果這個詞出現在對方句子中，則改成回覆
                if '這個字' in d:
                    訊息 = '改成回覆這個'

            self.send_chat(訊息)
            self.click_send()

        input('沒有訊息要傳了，按ENTER即換下一個人')
        # time.sleep(3)


s = Scrapper()
try:
    s.run()
except KeyboardInterrupt:
    print('結束程式')
except Exception as e:
    print(e)
    print('發生錯誤')
    playsound(錯誤時播放音檔)