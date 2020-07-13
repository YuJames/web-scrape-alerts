from abc import (
    ABC,
    abstractmethod
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


FILE_DIR = path.dirname(path.realpath(__file__))
SLEEP_TIME = 3
POLL_TIME = 30

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
        """

        try:
            server = SMTP(smtp_server,port)
            server.starttls()
            server.login(self.sender, self.sender_pass)
            server.sendmail(self.sender, self.receiver, message)

            return True
        except Exception as e:
            print(f"Emailer.send_email - {repr(e)}")

            return False
        finally:
            server.close()

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
        self.driver = webdriver.Firefox(
            executable_path=path.join(FILE_DIR, "geckodriver"),
            options=self.options
        )
        self.waiter = WebDriverWait(self.driver, 10)
    
    def scrape_site(self, period):
        """Scrape the site and send an alert when the state changes.
        
        Args:
            period (int): polling period in seconds
        Returns:
            (str): state
        """
        
        xpath = "//*[@id='availability']"
        while True:
            try:
                self.driver.get(site)
                
                element = self.waiter.until(
                    visibility_of_element_located((By.XPATH, xpath))
                )
                sleep(period)
                availability = element.find_elements()[0].text
                print("test", availability)
                
                # if availability != last_state:
                #     cr = "\n"
                #     message = (
                #         f"From: {sender_email}{cr}"
                #         f"To: {receiver_email}{cr}"
                #         f"Subject: {site}{cr}{cr}"
                #         f"{availability}"
                #     )
                #     send_email(
                #         message
                #     )
            except Exception as e:
                print(f"AmazonScraper.scrape_site - {repr(e)}")
            finally:
                self.driver.quit()
                sleep(period)


def main():
    email_configs = {
        "server": "smtp.gmail.com",
        "port": 587,
        "sender": "yujames33@gmail.com",
        "sender_pass": environ["SENDER_PASS"],
        "receiver": "jennifer.nguyen.130@gmail.com"
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
