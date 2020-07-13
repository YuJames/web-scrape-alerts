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
from traceback import (
    format_exc
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


port = 587
smtp_server = "smtp.gmail.com"
sender_email = "yujames33@gmail.com"
sender_password = environ["SENDER_PASS"]
receiver_email = "jennifer.nguyen.130@gmail.com"
# receiver_email = "yujames33@gmail.com"

def send_email(message):
    try:
        server = SMTP(smtp_server,port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message)
    except Exception as e:
        print(e)
        print(format_exc())
    finally:
        server.close()


def scrape_site(last_state):
    """Scrape the site and send an alert when the state changes.
    
    Args:
        last_state (str): previous state
    Returns:
        (str): state
    """
    
    while True:
        try:
            site = 'https://www.claires.com/us/squishmallows-5"-summer-fun-plush-toy---styles-may-vary-260946.html?pid=260946'
            # site = "https://www.claires.com/us/ryans-world-spinzals-blind-bag---styles-may-vary-246365.html?cgid=2991#start=1"
            xpath = "//*[@class='product-info-container']"
            options = Options()
            options.headless = True
            driver = webdriver.Firefox(
                executable_path=path.join(path.abspath(getcwd()), "geckodriver"),
                options=options
            )
            waiter = WebDriverWait(driver, 120)
            driver.get(site)
            
            element = waiter.until(
                visibility_of_element_located((By.XPATH, xpath))
            )
            availability = element.find_element_by_tag_name("p").text
            print(availability)
            
            if availability != last_state:
                cr = "\n"
                message = (
                    f"From: {sender_email}{cr}"
                    f"To: {receiver_email}{cr}"
                    f"Subject: {site}{cr}{cr}"
                    f"{availability}"
                )
                send_email(
                    message
                )
            
            return availability
        except Exception as e:
            print(e)
            print(format_exc())
        finally:
            driver.quit()

def main():
    # last_state = "In Stock"
    last_state = "Out Of Stock"
    while True:
        last_state = scrape_site(last_state)
        sleep(30)

if __name__ == "__main__":
    main()
