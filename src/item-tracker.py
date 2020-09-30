from asyncio import (
    gather,
    get_event_loop,
    sleep
)
from itertools import (
    count
)
from json import (
    load
)
from os import (
    environ,
    path
)
from smtplib import (
    SMTP
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
CONFIG_FILE = path.join(PROJECT_ROOT, "database.json")


class EmailTiming:
    def __init__(self):
        self.max_retries = 3


class ScrapeTiming:
    def __init__(self):
        self.sleep_time = 5
        self.poll_time = 10
        self.max_refreshes = 10
        self.max_wait_time = 20


class Emailer(EmailTiming):
    def __init__(self, server, port, sender, sender_pass, recipient):
        """Sends emails.

        Args:
            server (str): email server
            port (str): email server port
            sender (str): sender email address
            sender_pass (str): sender email password
            recipient (list): default email recipients
        """

        super().__init__()

        self.server = server
        self.port = port
        self.sender = sender
        self.sender_pass = sender_pass
        self.recipient = None

    def send_email(self, subject, message, recipient=None):
        """Send an email.

        Args:
            subject (str): email subject
            message (str): email message
            recipient (list): email recipients
        Returns:
            (bool): True if successful, False if otherwise
        """

        target_recipient = self.recipient if recipient is None else recipient
        for i in target_recipient:
            for _ in range(self.max_retries):
                try:
                    server = SMTP(self.server, self.port)
                    server.starttls()
                    server.login(self.sender, self.sender_pass)
                    server.sendmail(
                        self.sender,
                        i,
                        (
                            f"From: {self.sender}\n"
                            f"To: {i}\n"
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


class ScraperFactory():
    def __init__(self, emailer_configs, database_file):
        """Factory class for creating specific scrapers.

        Args:
            emailer_configs (dict): configs for email sender
            database_file (str): file path for database of urls, items, and subscriptions
        """

        self.scrapers_classes = [AmazonScraper, ClairesScraper, CollectableMadnessScraper]

        with open(file=CONFIG_FILE, mode="r") as f:
            self.database = load(fp=f)
        self.emailer_configs = emailer_configs

    def create_scrapers(self):
        """Create a scraper.

        Args:
            N/A
        Returns:
            (list): subclasses of Scraper
        """

        for i in self.database.keys():
            for j in self.scrapers_classes:
                if i == j.domain:

        return [
            z(emailer=Emailer(**self.emailer_configs, recipient=y["subscribers"]), items=y)
            for x, y in self.database.items()
            for z in self.scrapers_classes
            if x == z.domain
        ]


class Scraper(ScrapeTiming):
    def __init__(self, emailer, items):
        """Base class for scraping.

        Args:
            emailer (Emailer): emailer to use for alerts
            items (list): list of item descriptions
        """

        super().__init__()

        self.id = str(uuid4())[-12:]
        self.options = Options()
        self.options.headless = True
        self.driver = None
        self.waiter = None

        self.emailer = emailer
        self.items = items

    def __getitem__(self, key):
        for i in self.items:
            if i["name"] == key:
                return i
        else:
            return None

    def reconnect(self, item):
        """Connect to a site through a fresh connection.

        Args:
            item (str): item name
        Returns:
            (None)
        """

        self.driver = webdriver.Firefox(
            executable_path=path.join(PROJECT_ROOT, "geckodriver"),
            options=self.options
        )
        self.waiter = WebDriverWait(self.driver, self.max_wait_time)
        self.driver.get(self[item]["path"])

    async def scrape_all_items(self, initial=True):
        return [self.scrape_item(item=x, initial=initial) for x in self.items]

    async def scrape_item(self, item, initial=True):
        """Scrape the site and send an alert when the state changes.

        Args:
            site_key (str): item name
            initial (bool): send initial email to indicate scrape start
        Returns:
            (str): state
        """

        pass


class AmazonScraper(Scraper):
    domain = "https://www.amazon.co.jp"

    def __init__(self, emailer, items):
        super().__init__(emailer=emailer, items=items)

    async def scrape_item(self, item, initial=True):
        url = path.join(self.domain, self[item]["path"])
        run_id = f"{self.id}::{item}::{url}"

        xpath = "//*[@id='availability']/child::span[1]"

        self.reconnect(item)

        for i in count():
            try:
                # scrape page and reload
                element = self.waiter.until(
                    visibility_of_element_located((By.XPATH, xpath))
                )
                await sleep(self.sleep_time)
                availability = element.text
                self.driver.refresh()
                # record scrape attempt after no scrape-related failures
                logger.write(INFO, f"{run_id} - AmazonScraper.scrape_item run {i}: {availability}")
                # when to send out an alert
                if i == 0:
                    if initial:
                        is_sent = self.emailer.send_email(
                            subject=f"Scraper ({item}) first run: {availability}",
                            message=url
                        )
                        if not is_sent:
                            raise Exception("Email not sent")
                elif availability != self.stock_state:
                    is_sent = self.emailer.send_email(
                        subject=f"Scraper ({item}) change detected: {availability}",
                        message=url
                    )
                    if not is_sent:
                        raise Exception("Email not sent")
                # update stock state only after no error
                self.stock_state = availability

                if i % self.max_refreshes == 0:
                    self.driver.quit()
                    self.reconnect(item)
            except Exception as e:
                logger.write(ERROR, f"{run_id} - AmazonScraper.scrape_item - {repr(e)}")
                self.driver.quit()
                self.reconnect(item)
            finally:
                await sleep(self.poll_time)


class ClairesScraper(Scraper):
    domain = "https://www.claires.com"

    def __init__(self, emailer, items):
        super().__init__(emailer=emailer, items=items)

    async def scrape_item(self, item, initial=True):
        url = path.join(self.domain, self[item]["path"])
        run_id = f"{self.id}::{item}::{url}"

        xpath = "//*[@class='product-info-container']//child::p"

        self.reconnect(item)

        for i in count():
            try:
                # scrape page and reload
                element = self.waiter.until(
                    visibility_of_element_located((By.XPATH, xpath))
                )
                await sleep(self.sleep_time)
                availability = element.text
                self.driver.refresh()
                # record scrape attempt after no scrape-related failures
                logger.write(INFO, f"{run_id} - ClairesScraper.scrape_item run {i}: {availability}")
                # when to send out an alert
                if i == 0:
                    if initial:
                        is_sent = self.emailer.send_email(
                            subject=f"Scraper ({item}) first run: {availability}",
                            message=url
                        )
                        if not is_sent:
                            raise Exception("Email not sent")
                elif availability != self.stock_state:
                    is_sent = self.emailer.send_email(
                        subject=f"Scraper ({item}) change detected: {availability}",
                        message=url
                    )
                    if not is_sent:
                        raise Exception("Email not sent")
                # update stock state only after no error
                self.stock_state = availability

                if i % self.max_refreshes == 0:
                    self.driver.quit()
                    self.reconnect(item)
            except Exception as e:
                logger.write(ERROR, f"{run_id} - ClairesScraper.scrape_item - {repr(e)}")
                self.driver.quit()
                self.reconnect(item)
            finally:
                await sleep(self.poll_time)


class CollectableMadnessScraper(Scraper):
    domain = "https://collectiblemadness.com.au"

    def __init__(self, emailer, items):
        super().__init__(emailer=emailer, items=items)

    async def scrape_item(self, item, initial=True):
        url = path.join(self.domain, self[item]["path"])
        run_id = f"{self.id}::{item}::{url}"

        xpath = "//div[@class='product-form__payment-container']/button[1]"

        self.reconnect(item)

        for i in count():
            try:
                # scrape page and reload
                element = self.waiter.until(
                    visibility_of_element_located((By.XPATH, xpath))
                )
                await sleep(self.sleep_time)
                availability = element.text
                self.driver.refresh()
                # record scrape attempt after no scrape-related failures
                logger.write(INFO, f"{run_id} - CollectableMadnessScraper.scrape_item run {i}: {availability}")
                # when to send out an alert
                if i == 0:
                    if initial:
                        is_sent = self.emailer.send_email(
                            subject=f"Scraper ({item}) first run: {availability}",
                            message=url
                        )
                        if not is_sent:
                            raise Exception("Email not sent")
                elif availability != self.stock_state:
                    is_sent = self.emailer.send_email(
                        subject=f"Scraper ({item}) change detected: {availability}",
                        message=url
                    )
                    if not is_sent:
                        raise Exception("Email not sent")
                # update stock state only after no error
                self.stock_state = availability

                if i % self.max_refreshes == 0:
                    self.driver.quit()
                    self.reconnect(item)
            except Exception as e:
                logger.write(ERROR, f"{run_id} - CollectableMadnessScraper.scrape_item - {repr(e)}")
                self.driver.quit()
                self.reconnect(item)
            finally:
                await sleep(self.poll_time)


async def main():
    # create scrapers
    factory = ScraperFactory(
        emailer_configs={
            "server": environ["SERVER"],
            "port": environ["PORT"],
            "sender": environ["SENDER"],
            "sender_pass": environ["SENDER_PASS"]
        }
    )
    scrapers = factory.create_scrapers()
    alerts = [x.scrape_all_items() for x in scrapers]

    await gather(*alerts)


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
    loop.close()
