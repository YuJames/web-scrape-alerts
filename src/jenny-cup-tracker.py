from asyncio import (
    get_event_loop,
    gather
)
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
from uuid import (
    uuid4
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
    def __init__(self, **kwargs):
        self.id = str(uuid4())[-12:]
        self.sites = {
            x: {
                "id": str(uuid4())[-12:],
                "url": y
            }
            for x, y in kwargs.items()
        }
        self.options = Options()
        self.options.headless = True
        self.driver = None
        self.waiter = None

    def __getitem__(self, key):
        return self.sites[key]

    async def reconnect(self, site_key):
        """Connect to a site through a fresh connection.

        Args:
            site_key (str): key to website
        Returns:
            (None)
        """

        self.driver = webdriver.Firefox(
            executable_path=path.join(PROJECT_ROOT, "geckodriver"),
            options=self.options
        )
        self.waiter = WebDriverWait(self.driver, 10)
        self.driver.get(self[site_key]["url"])


class ScrapeTiming:
    def __init__(self):
        self.sleep_time = 3
        self.poll_time = 5
        self.max_refreshes = 20


class AmazonScraper(Scraper, ScrapeTiming):
    def __init__(self, sites, **kwargs):
        Scraper.__init__(self, **sites)
        ScrapeTiming.__init__(self)

        self.emailer = Emailer(**kwargs)

    async def scrape_site(self, site_key, initial=True):
        """Scrape the site and send an alert when the state changes.

        Args:
            site_key (str): key to website
            initial (bool): send initial email to indicate scrape start
        Returns:
            (str): state
        """

        run_id = f"{self.id}::{site_key}::{self[site_key]['url']}"

        xpath = "//*[@id='availability']"

        await self.reconnect(site_key)

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
                logger.write(INFO, f"{run_id} - AmazonScraper.scrape_site run {i}: {availability}")
                # when to send out an alert
                if i == 0:
                    if initial:
                        is_sent = self.emailer.send_email(
                            subject=f"Scraper ({site_key}) first run: {availability}",
                            message=self[site_key]["url"]
                        )
                        if not is_sent:
                            raise Exception("Email not sent")
                elif availability != self.stock_state:
                    is_sent = self.emailer.send_email(
                        subject=f"Scraper ({site_key}) change detected: {availability}",
                        message=self[site_key]["url"]
                    )
                    if not is_sent:
                        raise Exception("Email not sent")
                # update stock state only after no error
                self.stock_state = availability

                if i % self.max_refreshes == 0:
                    self.driver.quit()
                    await self.reconnect(site_key)
            except Exception as e:
                logger.write(ERROR, f"{run_id} - AmazonScraper.scrape_site - {repr(e)}")
                self.driver.quit()
                await self.reconnect(site_key)
            finally:
                sleep(self.poll_time)


async def main():
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
        {"gradient-cups": scraper_configs["gradient-cups"]},
        **jenny_email_configs
    )
    await gather(
        jenny_scraper.scrape_site(
            site_key="gradient-cups",
            initial=True
        )
    )


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
    loop.close()
