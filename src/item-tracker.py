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
from re import (
    search,
    sub
)
from smtplib import (
    SMTP
)
from uuid import (
    uuid4
)

from fastcore.utils import (
    store_attr
)
from selenium.webdriver import (
    Firefox,
    FirefoxProfile
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
from twilio.rest import (
    Client
)

from logger import (
    logger,
    DEBUG, INFO, WARNING, ERROR
)


PROJECT_ROOT = environ["PROJECT_ROOT"]
CONFIG_FILE = path.join(PROJECT_ROOT, "items.json")
SUBSCRIBERS_FILE = path.join(PROJECT_ROOT, "subscribers.json")

class EmailTiming:
    def __init__(self, max_retries=3):
        """Determine email timing values.

        Args:
            max_retries (int): maximum action attempts before terminating
        """

        store_attr()

class ScrapeTiming:
    def __init__(self, site_load_time=10, poll_time=10, max_refreshes=3, max_wait_time=10):
        """Determine scrape timing values.

        Args:
            site_load_time (int): wait time for a site to load before scraping
            poll_time (int): wait time between scraping a site
            max_refreshes (int): maximum site refreshes before reconnecting
            max_wait_time (int): maximum wait time for a site element to be found during scraping
        """

        store_attr()

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
        store_attr()

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

class Messenger:
    def __init__(self, sender, account_id, auth_token):
        """Sends SMS.

        Args:
            sender (str): sender number
            account_id (str): twilio account id
            auth_token (str): twilio auth token
        """

        store_attr()

        self.client = Client(account_id, auth_token)

    def send_sms(self, message, recipient):
        """Send a sms.

        Args:
            message (str): sms message
            recipient (list): sms recipients
        Returns:
            (None)
        """

        for i in recipient:
            self.client.messages.create(
                body=message,
                from_=self.sender,
                to=i
            )

class Database:
    def __init__(self, items_db_file, subs_db_file):
        """Access databases for items and subscriptions.

        Args:
            items_db_file (str): file path for database of items
            subs_db_file (str): file path for database of subscribers
        """

        store_attr()

        with open(file=self.items_db_file, mode="r") as f: self.items_db = load(fp=f)
        with open(file=self.subs_db_file, mode="r") as f: self.subs_db = load(fp=f)

    def get_subscribed(self):
        """Get items that have subscribers.

        Args:
            N/A
        Returns:
            (dict): items database
        """
                
        subscribed = {
            x: [z for z in y if len(z["subscribers"]) > 0]
            for x, y in self.items_db.items()
            if sum([len(z["subscribers"]) for z in y]) > 0
        }
        
        return subscribed

    def get_item(self, item):
        """Get item description.

        Args:
            item (str): item name
        Returns:
            (dict): item description
        """

        all_items = [z for x, y in self.items_db.items() for z in y]

        item_description = [x for x in all_items if x["name"] == item][0]

        return item_description

    def get_subscribers(self, item):
        """Get subscribers to an item.

        Args:
            item (str): item name
        Returns:
            (list): subscribers
        """

        all_items = [z for x, y in self.items_db.items() for z in y]
        subscribers = [y for x in all_items for y in x["subscribers"] if x["name"] == item]

        subscribers_data = [self.subs_db[x] for x in subscribers]

        return subscribers_data

class ScraperFactory():
    def __init__(self, emailer_configs, messenger_configs, database):
        """Factory class for creating specific scrapers.

        Args:
            emailer_configs (dict): configs for email sender
            messenger_configs (dict): configs for sms sender
            database (Database): database of items and subscribers
        """

        store_attr()

        self.scrapers_classes = [x for x in Scraper.__subclasses__()]

    def create_scrapers(self):
        """Create scrapers.

        Args:
            N/A
        Returns:
            (list): subclasses of Scraper
        """

        combined_dbs = self.database.get_subscribed().copy()
        for i, j in combined_dbs.items():
            for k in j:
                k["subscribers"] = [self.database.subs_db[x] for x in k["subscribers"]]

        scrapers = [
            z(emailer=Emailer(**self.emailer_configs), messenger=Messenger(**self.messenger_configs), items=y)
            for x, y in combined_dbs.items()
            for z in self.scrapers_classes
            if x == z.domain
        ]

        return scrapers

class Scraper(ScrapeTiming):
    domain = ""
    xpath = ""
    e_property = None

    def __init__(self, emailer, messenger, items):
        """Base class for scraping.

        Args:
            emailer (Emailer): emailer to use for alerts
            messenger (Messenger): messenger to use for alerts
            items (list): list of item descriptions
        """

        super().__init__()
        store_attr()

        self.id = str(uuid4())[-12:]
        self.options = Options()
        self.options.headless = True
        # self.profile = FirefoxProfile()
        # self.profile.set_preference("dom.disable_beforeunload", True)
        # self.profile.set_preference("browser.tabs.warnOnClose", False)
        self.driver = None
        self.waiter = None

        self.stock_state = {}
        self.excluded_states = {x["name"]: x["exclude"] for x in items}

    def __getitem__(self, key):
        for i in self.items:
            if i["name"] == key:
                return i
        else:
            return None

    def _reconnect(self, url):
        """Connect to a site through a fresh connection.

        Args:
            url (str): site url
        Returns:
            (None)
        """

        try:
            self.driver.quit()
        except Exception as e:
            pass

        self.driver = Firefox(
            executable_path=path.join(PROJECT_ROOT, "geckodriver"),
            options=self.options
            # firefox_profile=self.profile
        )
        self.waiter = WebDriverWait(self.driver, self.max_wait_time)
        self.driver.get(url)
        self.waiter.until(lambda x: x.execute_script("return document.readyState") == "complete")

    async def _get_target_text(self, e_property=None):
        """Get target variable text from site.

        Args:
            N/A
        Returns:
            (str): text
        """

        await sleep(self.site_load_time)
        element = self.waiter.until(
            visibility_of_element_located((By.XPATH, self.xpath))
        )
        if e_property is not None:
            text = element.get_property(e_property)
        else:
            text = element.text
        availability = sub(
            pattern=r"\s",
            repl=" ",
            string=text
        )
        self.driver.refresh()

        return availability

    async def _scrape_item(self, item, initial=True):   
        """Scrape the site and send an alert when the state changes.

        Args:
            xpath (str): target xpath
            item (str): item name
            initial (bool): send initial email to indicate scrape start
        Returns:
            (None)
        """

        while True:
            try:
                item_db_entry = self[item]
                if item_db_entry is None:
                    return
                url = path.join(self.domain, item_db_entry["path"])
                run_id = f"{self.id}::{item}::{url}"

                email_subscriptions = [y for x in item_db_entry["subscribers"] for y in x["email"]]
                phone_subscriptions = [y for x in item_db_entry["subscribers"] for y in x["sms"]]

                self._reconnect(url)

                break
            except Exception as e:
                logger.write(ERROR, f"{run_id} - {self.__class__.__name__}.scrape_item - {repr(e)}")
                self._reconnect(url)
            finally:
                await sleep(self.poll_time)

        for i in count():
            try:
                availability = await self._get_target_text(self.e_property)
                if len([_ for _ in [search(pattern=x, string=availability) for x in self.excluded_states[item]] if _ is not None]) == 0:
                    # record scrape attempt after no scrape-related failures
                    logger.write(INFO, f"{run_id} - {self.__class__.__name__}.scrape_item run {i}: {availability}")
                    # when to send out an alert
                    if i == 0:
                        if initial:
                            subject, message = f"Scraper ({item}) first run: {availability}", url
                            
                            is_sent = self.emailer.send_email(
                                subject=subject,
                                message=message,
                                recipient=email_subscriptions
                            )
                            if not is_sent:
                                raise Exception("Email not sent")
                            self.messenger.send_sms(
                                message=f"{subject} - {message}",
                                recipient=phone_subscriptions
                            )
                    elif availability != self.stock_state[item]:
                        subject, message = f"Scraper ({item}) change detected: {availability}", url
                        is_sent = self.emailer.send_email(
                            subject=subject,
                            message=message,
                            recipient=email_subscriptions
                        )
                        if not is_sent:
                            raise Exception("Email not sent")
                        self.messenger.send_sms(
                            message=f"{subject}[{message}]",
                            recipient=phone_subscriptions
                        )
                    # update stock state only after no error
                    self.stock_state[item] = availability

                if i % self.max_refreshes == 0:
                    self._reconnect(url)

            except Exception as e:
                logger.write(ERROR, f"{run_id} - {self.__class__.__name__}.scrape_item - {repr(e)}")
                self._reconnect(url)
            finally:
                await sleep(self.poll_time)

    async def scrape_all_items(self, initial=True):
        """Get valid coroutines to run.

        Args:
            initial (bool): send initial email to indicate scrape start
        Returns:
            (list): coroutines
        """

        return [self._scrape_item(item=x["name"], initial=initial) for x in self.items]

class AmazonJpScraper(Scraper):
    domain = "https://www.amazon.co.jp"
    xpath = "//*[@id='availability']/child::span[1]"

class AmazonScraper(Scraper):
    domain = "https://www.amazon.com"
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

class BestBuyScraper(Scraper):
    domain = "https://www.bestbuy.com"
    xpath = "(//div[@class='fulfillment-add-to-cart-button'])[1]"

class FiveBelowScraper(Scraper):
    domain = "https://www.fivebelow.com"
    xpath = "//button[@data-cy='buyBox__addToCartButton']"

class LandrysScraper(Scraper):
    domain = "https://shop.landrysinc.com"
    xpath = "//div[@data-section-type='collection-template']"

class PlaystationScraper(Scraper):
    domain = "https://direct.playstation.com"
    xpath = "//producthero-info//div[@class='button-placeholder']//button[@aria-label='Add to Cart']"

class CostcoScraper(Scraper):
    domain = "https://www.costco.com"
    xpath = "//input[@id='add-to-cart-btn']"
    e_property = "value"

class SmythsScraper(Scraper):
    domain = "https://www.smythstoys.com"
    xpath = "//p[@class=' deliveryType homeDelivery js-stockStatus']"

async def main():
    # initialize database
    database = Database(items_db_file=CONFIG_FILE, subs_db_file=SUBSCRIBERS_FILE)
    # initialize scrapers
    factory = ScraperFactory(
        emailer_configs={
            "server": environ["SERVER"],
            "port": environ["PORT"],
            "sender": environ["EMAIL_SENDER"],
            "sender_pass": environ["EMAIL_SENDER_PASS"]
        },
        messenger_configs={
            "sender": environ["SMS_SENDER"],
            "account_id": environ["SMS_ACCOUNT_ID"],
            "auth_token": environ["SMS_AUTH_TOKEN"]
        },
        database=database
    )
    scrapers = factory.create_scrapers()
    alerts = [y for x in scrapers for y in await x.scrape_all_items(False)]

    await gather(*alerts)


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
    loop.close()
