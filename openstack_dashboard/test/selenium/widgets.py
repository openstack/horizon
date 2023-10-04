#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from dataclasses import dataclass
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@dataclass
class TableDefinition:
    """Class for keeping track of fields on the page"""
    next: bool
    prev: bool
    count: int
    names: list


def get_and_dismiss_messages(element):
    messages = element.find_elements_by_css_selector("div.messages div.alert")
    collect = []
    for message in messages:
        text = message.find_element_by_css_selector("p, div").text
        message.find_element_by_css_selector("a.close").click()
        collect.append(text)
    return collect


def find_already_visible_element_by_xpath(element, driver):
    return WebDriverWait(driver, 160).until(
        EC.visibility_of_element_located((By.XPATH, element)))


def select_from_dropdown(element, label):
    menu_button = element.find_element_by_css_selector(
        ".dropdown-toggle"
    )
    menu_button.click()
    options = element.find_element_by_css_selector("ul.dropdown-menu")
    selection = options.find_element_by_xpath(
        f".//*[normalize-space()='{label}']"
    )
    selection.click()


def select_from_specific_dropdown_in_form(driver, dropdown_id, label):
    dropdown = driver.find_element_by_xpath(
        f".//*[@for='{dropdown_id}']/following-sibling::div")
    dropdown.click()
    dropdown_options = dropdown.find_element_by_css_selector(
        "ul.dropdown-menu")
    dropdown_options.find_element_by_xpath(
        f".//*[normalize-space()='{label}']").click()


def confirm_modal(element):
    confirm = element.find_element_by_css_selector(
        ".modal-dialog .btn-danger"
    )
    confirm.click()


def is_next_link_available(driver):
    try:
        return driver.find_element_by_link_text("Next »").is_displayed()
    except (exceptions.NoSuchElementException,
            exceptions.ElementNotVisibleException):
        return False


def is_prev_link_available(driver):
    try:
        return driver.find_element_by_link_text("« Prev").is_displayed()
    except (exceptions.NoSuchElementException,
            exceptions.ElementNotVisibleException):
        return False


def get_table_definition(driver, sorting=False):
    names = driver.find_elements_by_css_selector('table tr td:nth-child(2)')
    rows = driver.find_elements_by_css_selector("tr[data-display-key='name']")
    if sorting:
        names.sort()
    actual_table = TableDefinition(next=is_next_link_available(driver),
                                   prev=is_prev_link_available(driver),
                                   count=len(rows), names=[names[0].text])
    return actual_table
