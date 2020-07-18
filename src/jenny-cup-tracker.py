from itertools import (
    count
)
from os import (
    environ,
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


PROJECT_ROOT = environ["PROJECT_ROOT"]


class EmailTiming:
    def __init__(self):
        self.max_retries = 3


class Emailer(EmailTiming):
    def __init__(self, server, port, sender, sender_pass, receiver):
        super().__init__()

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

        for _ in range(self.max_retries):
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


class Scraper():
    def __init__(self, site):
        self.site = site
        self.options = Options()
        self.options.headless = True
        self.driver = None
        self.waiter = None

    def reconnect(self):
        self.driver = webdriver.Firefox(
            executable_path=path.join(PROJECT_ROOT, "geckodriver"),
            options=self.options
        )
        self.waiter = WebDriverWait(self.driver, 10)
        self.driver.get(self.site)


class ScrapeTiming:
    def __init__(self):
        self.sleep_time = 3
        self.poll_time = 5
        self.max_refreshes = 20


class AmazonScraper(Scraper, ScrapeTiming):
    def __init__(self, site, **kwargs):
        Scraper.__init__(site)
        ScrapeTiming.__init__()

        self.emailer = Emailer(**kwargs)

        self.reconnect()

    def scrape_site(self, initial=True):
        """Scrape the site and send an alert when the state changes.

        Args:
            initial (bool): send initial email to indicate scrape start
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
                sleep(self.sleep_time)
                availability = element.find_element_by_tag_name("span").text
                self.driver.refresh()
                # record scrape attempt after no scrape-related failures
                logger.write(INFO, f"AmazonScraper.scrape_site - run {i}: {availability}")
                # when to send out an alert
                if i == 0 and initial:
                    is_sent = self.emailer.send_email(
                        subject=f"Scraper first run: {availability}",
                        message=self.site
                    )
                    if not is_sent:
                        raise Exception("Email not sent")
                elif availability != self.stock_state:
                    is_sent = self.emailer.send_email(
                        subject=f"State change alert: {availability}",
                        message=self.site
                    )
                    if not is_sent:
                        raise Exception("Email not sent")
                # update stock state only after no error
                self.stock_state = availability

                if i % self.max_refreshes == 0:
                    self.driver.quit()
                    self.reconnect()
            except Exception as e:
                logger.write(ERROR, f"AmazonScraper.scrape_site - {repr(e)}")
                self.driver.quit()
                self.reconnect()
            finally:
                sleep(self.poll_time)


def main():
    scraper_configs = {
        "gradient-cups": "https://www.amazon.co.jp/-/en/Starbucks-Gradient-gradaion-Overseas-delivery/dp/B07CVC7Z5C?fbclid=IwAR3SEj9VKEJVxkIUIKtEfryyf3_cgOAVea5d84vnkkjxKnwhzD-SyeKf9so"
    }
    jenny_email_configs = {
        "server": environ["SERVER"],
        "port": environ["PORT"],
        "sender": environ["SENDER"],
        "sender_pass": environ["SENDER_PASS"],
        "receiver": "Jennguyenna@gmail.com"
    }
    jenny_scraper = AmazonScraper(
        scraper_configs["gradient-cups"],
        **jenny_email_configs
    )
    jenny_scraper.scrape_site()


if __name__ == "__main__":
    main()
