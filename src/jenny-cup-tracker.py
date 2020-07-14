from abc import (
    ABC,
    abstractmethod
)
from datetime import (
    datetime
)
from itertools import (
    count
)
from os import (
    environ,
    getcwd,
    path
)
from smtplib import (
    SMTP
)
from time import (
    sleep
)

from selenium import (
    webdriver
)
from selenium.webdriver.common.by import (
    By
)
from selenium.webdriver.firefox.options import (
    Options
)
from selenium.webdriver.support.expected_conditions import (
    visibility_of_element_located
)
from selenium.webdriver.support.ui import (
    WebDriverWait
)

from logger import (
    logger,
    DEBUG, INFO, WARNING, ERROR
)


FILE_DIR = path.dirname(path.realpath(__file__))
SLEEP_TIME = 3
POLL_TIME = 5
MAX_RETRIES = 10
MAX_REFRESHES = 20

class Emailer:
    def __init__(self, server, port, sender, sender_pass, receiver):
        self.server = server
        self.port = port
        self.sender = sender
        self.sender_pass = sender_pass
        self.receiver = receiver
    
    def send_email(self, subject, message):
        """Send email.

        Args:
            message (str): email message
        Returns:
            (bool): True if successful, False if otherwise
        """

        for _ in range(MAX_RETRIES):
            try:
                server = SMTP(self.server, self.port)
                server.starttls()
                server.login(self.sender, self.sender_pass)
                server.sendmail(
                    self.sender,
                    self.receiver,
                    (
                        f"From: {self.sender}\n"
                        f"To: {self.receiver}\n"
                        f"Subject: {subject}\n\n"
                        f"{message}"
                    )
                )

                return True
            except Exception as e:
                logger.write(DEBUG, f"Emailer.send_email - {repr(e)}")
            finally:
                server.close()
        
        return False

class Scraper(ABC):
    @abstractmethod
    def scrape_site(self):
        pass

class AmazonScraper(Scraper):
    def __init__(self, site, **kwargs):
        self.site = site
        self.emailer = Emailer(**kwargs)
        self.options = Options()
        self.options.headless = True
        
        self.reconnect()
    
    def reconnect(self):
        self.driver = webdriver.Firefox(
            executable_path=path.join(FILE_DIR, "..", "geckodriver"),
            options=self.options
        )
        self.waiter = WebDriverWait(self.driver, 10)
        self.driver.get(self.site)

    def scrape_site(self, period):
        """Scrape the site and send an alert when the state changes.
        
        Args:
            period (int): polling period in seconds
        Returns:
            (str): state
        """
        
        xpath = "//*[@id='availability']"

        for i in count():
            try:
                # scrape page and reload
                element = self.waiter.until(
                    visibility_of_element_located((By.XPATH, xpath))
                )
                sleep(SLEEP_TIME)
                availability = element.find_element_by_tag_name("span").text
                self.driver.refresh()
                # record scrape attempt after no scrape-related failures
                logger.write(INFO, f"AmazonScraper.scrape_site - run {i}: {availability}")
                # when to send out an alert
                if i == 0:
                    is_sent = self.emailer.send_email(self.site, f"Scraper first run: {availability}")
                    if not is_sent:
                        raise Exception("Email not sent")
                elif availability != self.stock_state:
                    is_sent = self.emailer.send_email(self.site, f"State change alert: {availability}")
                    if not is_sent:
                        raise Exception("Email not sent")
                # update stock state only after no error
                self.stock_state = availability

                if i % MAX_REFRESHES == 0:
                    self.reconnect()
            except Exception as e:
                logger.write(ERROR, f"AmazonScraper.scrape_site - {repr(e)}")
                self.driver.quit()
                self.reconnect()
            finally:
                sleep(period)


def main():
    email_configs = {
        "server": "smtp.gmail.com",
        "port": 587,
        "sender": "yujames33@gmail.com",
        "sender_pass": environ["SENDER_PASS"],
        "receiver": "Jennguyenna@gmail.com"
    }
    scraper_configs = {
        "site": "https://www.amazon.co.jp/-/en/Starbucks-Gradient-gradaion-Overseas-delivery/dp/B07CVC7Z5C?fbclid=IwAR3SEj9VKEJVxkIUIKtEfryyf3_cgOAVea5d84vnkkjxKnwhzD-SyeKf9so",
        "period": POLL_TIME
    }
    scraper = AmazonScraper(
        scraper_configs["site"],
        **email_configs
    )

    scraper.scrape_site(scraper_configs["period"])


if __name__ == "__main__":
    main()
