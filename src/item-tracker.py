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
    def __init__(self, server, port, sender, sender_pass, recipient=None):
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
        self.recipient = recipient

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

                    break
                except Exception as e:
                    logger.write(DEBUG, f"Emailer.send_email - {repr(e)}")
                finally:
                    server.close()
            else:
                return False

        return True

class ScraperFactory():
    def __init__(self, emailer_configs, database_file):
        """Factory class for creating specific scrapers.

        Args:
            emailer_configs (dict): configs for email sender
            database_file (str): file path for database of urls, items, and subscriptions
        """

        self.scrapers_classes = [AmazonScraper, ClairesScraper, CollectableMadnessScraper, BathBodyWorksScraper]

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

        scrapers = []
        for i, j in self.database.items():
            for k in self.scrapers_classes:
                items_with_subscribers = [x for x in j if len(x["subscribers"]) != 0]
                if i == k.domain and len(items_with_subscribers) != 0:
                    scrapers.append(k(emailer=Emailer(**self.emailer_configs), items=j))

        return scrapers


class Scraper(ScrapeTiming):
    domain = ""
    xpath = ""

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

    def reconnect(self, url):
        """Connect to a site through a fresh connection.

        Args:
            url (str): site url
        Returns:
            (None)
        """

        self.driver = webdriver.Firefox(
            executable_path=path.join(PROJECT_ROOT, "geckodriver"),
            options=self.options
        )
        self.waiter = WebDriverWait(self.driver, self.max_wait_time)
        self.driver.get(url)

    async def _get_target_text(self):
        """Get target variable text from site.

        Args:
            N/A
        Returns:
            (str): text
        """

        element = self.waiter.until(
            visibility_of_element_located((By.XPATH, self.xpath))
        )
        await sleep(self.sleep_time)
        availability = element.text
        self.driver.refresh()

        return availability

    async def scrape_all_items(self, initial=True):
        """Get valid coroutines to run.

        Args:
            initial (bool): send initial email to indicate scrape start
        Returns:
            (list): coroutines
        """

        return [self.scrape_item(item=x["name"], initial=initial) for x in self.items]

    async def scrape_item(self, item, initial=True):
        """Scrape the site and send an alert when the state changes.

        Args:
            xpath (str): target xpath
            item (str): item name
            initial (bool): send initial email to indicate scrape start
        Returns:
            (str): state
        """

        while True:
            try:
                entry = self[item]
                if entry is None:
                    return
                recipient = entry["subscribers"]
                url = path.join(self.domain, entry["path"])
                run_id = f"{self.id}::{item}::{url}"

                self.reconnect(url)

                break
            except Exception as e:
                logger.write(ERROR, f"{run_id} - {self.__class__.__name__}.scrape_item - {repr(e)}")
                self.driver.quit()
                self.reconnect(url)
            finally:
                await sleep(self.poll_time)

        for i in count():
            try:
                availability = await self._get_target_text()
                # record scrape attempt after no scrape-related failures
                logger.write(INFO, f"{run_id} - {self.__class__.__name__}.scrape_item run {i}: {availability}")
                # when to send out an alert
                if i == 0:
                    if initial:
                        is_sent = self.emailer.send_email(
                            subject=f"Scraper ({item}) first run: {availability}",
                            message=url,
                            recipient=recipient
                        )
                        if not is_sent:
                            raise Exception("Email not sent")
                elif availability != self.stock_state:
                    is_sent = self.emailer.send_email(
                        subject=f"Scraper ({item}) change detected: {availability}",
                        message=url,
                        recipient=recipient
                    )
                    if not is_sent:
                        raise Exception("Email not sent")
                # update stock state only after no error
                self.stock_state = availability

                if i % self.max_refreshes == 0:
                    self.driver.quit()
                    self.reconnect(url)
            except Exception as e:
                logger.write(ERROR, f"{run_id} - {self.__class__.__name__}.scrape_item - {repr(e)}")
                self.driver.quit()
                self.reconnect(url)
            finally:
                await sleep(self.poll_time)

class AmazonScraper(Scraper):
    domain = "https://www.amazon.co.jp"
    xpath = "//*[@id='availability']/child::span[1]"


class ClairesScraper(Scraper):
    domain = "https://www.claires.com"
    xpath = "//*[@class='product-info-container']//child::p"


class CollectableMadnessScraper(Scraper):
    domain = "https://www.collectiblemadness.com.au"
    xpath = "//div[@class='product-form__payment-container']/button[1]"


class BathBodyWorksScraper(Scraper):
    domain = "https://www.bathandbodyworks.com"
    xpath = "//div[@class='availability-msg']"

async def main():
    # create scrapers
    factory = ScraperFactory(
        emailer_configs={
            "server": environ["SERVER"],
            "port": environ["PORT"],
            "sender": environ["SENDER"],
            "sender_pass": environ["SENDER_PASS"]
        },
        database_file=CONFIG_FILE
    )
    scrapers = factory.create_scrapers()
    alerts = [y for x in scrapers for y in await x.scrape_all_items(False)]

    await gather(*alerts)


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
    loop.close()
