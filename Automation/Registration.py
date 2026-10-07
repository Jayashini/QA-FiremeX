import unittest
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException, UnexpectedAlertPresentException

BASE_URL = "http://localhost:5174/FiremeX/register"

class FiremexRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(5)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()

    def setUp(self):
        """Ensure starting state before each test case."""
        self.driver.get(BASE_URL)
        time.sleep(1)

    # 1. LINK TO SIGN IN
    def test_TC_REG_01_verify_already_have_account_sign_in_link(self):
        """TC-REG-01: Verify 'Already have an account? Sign in' link navigates to login page."""
        self.driver.get(BASE_URL)
        
        sign_in_link = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(), 'Sign in') or contains(text(), 'Already have an account')] | //button[contains(text(), 'Sign in')]")
        ))
        self.assertTrue(sign_in_link.is_displayed(), "Sign in link is not visible.")
        sign_in_link.click()
        
        time.sleep(1)
        self.assertTrue("login" in self.driver.current_url.lower() or "register" not in self.driver.current_url.lower(),
                        "Navigation to Sign In page failed.")

    # 2. BACK BUTTON FUNCTIONALITY
    def test_TC_REG_02_verify_back_button_is_clickable(self):
        """TC-REG-02: Check organization registration back button is clickable and returns to selection."""
        self.driver.get(BASE_URL)
        
        # Navigate into Organization Registration form first
        org_card = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Organization') or contains(text(), 'Organization')]")
        ))
        org_card.click()
        time.sleep(1)
        
        # Verify Back button is visible and clickable
        back_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@aria-label, 'Back') or contains(@class, 'back') or descendant::*[name()='svg']]")
        ))
        self.assertTrue(back_btn.is_displayed(), "Back button is not displayed on registration form.")
        back_btn.click()
        time.sleep(1)
        
        # Verify returned to main selection view
        selection_header = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Register as an Organization') or contains(text(), 'Register to the System')]")
        ))
        self.assertTrue(selection_header.is_displayed(), "Failed to return to selection screen after clicking back button.")

    # 3. ORGANIZATION REGISTRATION FIELD VALIDATIONS & SUBMISSION
    def test_TC_REG_03_verify_organization_registration_fields_and_eye_toggle(self):
        """TC-REG-03: Verify Organization registration fields visibility, clickability, format validation & eye toggle."""
        self.driver.get(BASE_URL)
        
        # Click Organization registration card/button
        org_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Organization') or contains(text(), 'Select Organization')]")
        ))
        org_btn.click()
        time.sleep(1)
        
        # 1. Organization Name
        org_name = self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[contains(@placeholder, 'Org Name') or contains(@placeholder, 'Organization Name') or contains(@name, 'orgName') or contains(@name, 'name')]")
        ))
        self.assertTrue(org_name.is_enabled(), "Organization name field is not clickable/editable.")
        org_name.click()
        org_name.send_keys("Safety Solutions Corp")

        # 2. Sector Dropdown
        sector_elements = self.driver.find_elements(
            By.XPATH, "//select[contains(@name, 'sector')] | //*[contains(@placeholder, 'Sector') or contains(@name, 'sector') or contains(text(), 'Sector') or contains(@class, 'select')]"
        )
        if sector_elements:
            sector_dropdown = sector_elements[0]
            self.assertTrue(sector_dropdown.is_displayed(), "Organization Sector dropdown is not visible.")
            sector_dropdown.click()

        # 3. Organization Email & Format validation (name@company.com)
        org_email = self.driver.find_element(
            By.XPATH, "//input[@type='email' or contains(@placeholder, 'Email') or contains(@name, 'email')]"
        )
        self.assertTrue(org_email.is_enabled(), "Organization email field is not clickable.")
        test_email = "admin@safetysolutions.com"
        org_email.clear()
        org_email.send_keys(test_email)
        self.assertTrue(re.match(r"^[\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,}$", org_email.get_attribute("value")),
                        "Email format name@company.com validation failed.")

        # 4. Country Input Field
        country_elements = self.driver.find_elements(
            By.XPATH, "//input[contains(@placeholder, 'Country') or contains(@name, 'country')] | //select[contains(@name, 'country')] | //*[contains(text(), 'Country')]"
        )
        if country_elements:
            country_field = country_elements[0]
            self.assertTrue(country_field.is_enabled(), "Country input field is not clickable.")

        # 5. Contact Number Input Field & Format Validation
        contact_field = self.driver.find_element(
            By.XPATH, "//input[contains(@type, 'tel') or contains(@placeholder, 'Contact') or contains(@placeholder, 'Phone') or contains(@name, 'phone')]"
        )
        self.assertTrue(contact_field.is_enabled(), "Contact number field is not clickable.")
        contact_field.clear()
        contact_field.send_keys("+1 555-0199")
        self.assertTrue(re.match(r"^\+?[\d\s\-]{7,15}$", contact_field.get_attribute("value")),
                        "Contact number format is invalid.")

        # 6. Password setup field & Confirm Password field
        pass_inputs = self.driver.find_elements(
            By.XPATH, "//input[@type='password' or contains(@placeholder, '••••••••') or contains(@placeholder, 'Password')]"
        )
        self.assertTrue(len(pass_inputs) >= 1, "Password setup field not found.")
        password_field = pass_inputs[0]
        self.assertTrue(password_field.is_enabled(), "Password setup field is not clickable.")
        password_field.send_keys("SecurePass123!")

        # 7. Confirm Password field
        if len(pass_inputs) > 1:
            confirm_password_field = pass_inputs[1]
        else:
            confirm_password_field = self.driver.find_element(
                By.XPATH, "//input[contains(@placeholder, 'Confirm') or contains(@name, 'confirm')]"
            )
        self.assertTrue(confirm_password_field.is_enabled(), "Confirm Password field is not clickable.")
        confirm_password_field.send_keys("SecurePass123!")

        # 8. Password Eye Toggle Icon
        eye_toggle_icons = self.driver.find_elements(
            By.XPATH, "//button[descendant::*[name()='svg'] or contains(@class, 'eye')]"
        )
        if eye_toggle_icons:
            eye_btn = eye_toggle_icons[0]
            self.assertTrue(eye_btn.is_displayed(), "Eye toggle icon in password field is not visible.")
            eye_btn.click()
            time.sleep(0.5)

        # 9. Verify Registration button status and submit
        submit_btn = self.driver.find_element(
            By.XPATH, "//button[@type='submit'] | //button[contains(., 'Complete Registration')]"
        )
        self.assertTrue(submit_btn.is_enabled(), "Registration button is disabled after filling required inputs.")
        submit_btn.click()
        time.sleep(1)

        # 10. Organization registration successful message verification
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.assertIn("success", alert_text.lower())
            alert.accept()
        except Exception:
            # Check for onscreen success banner/toast if alert not present
            success_msg = self.driver.find_element(
                By.XPATH, "//*[contains(text(), 'successful') or contains(text(), 'Registered successfully') or contains(text(), 'registered')]"
            )
            self.assertTrue(success_msg.is_displayed(), "Organization registration success message not displayed.")

    def test_TC_REG_04_verify_registration_button_disabled_when_fields_empty(self):
        """TC-REG-04: Verify that the registration button is disabled until all mandatory input fields are filled."""
        self.driver.get(BASE_URL)
        
        org_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Organization') or contains(text(), 'Select Organization')]")
        ))
        org_btn.click()
        time.sleep(1)

        submit_btn = self.driver.find_element(
            By.XPATH, "//button[@type='submit'] | //button[contains(., 'Register') or contains(., 'Complete') or contains(., 'Submit') or contains(., 'Access')]"
        )
        
        # Button should either be disabled attribute or clicking without required fields triggers form validation
        is_disabled = not submit_btn.is_enabled() or submit_btn.get_attribute("disabled") is not None
        if not is_disabled:
            # Attempt submit to verify native validation prevents action
            submit_btn.click()
            org_name = self.driver.find_element(
                By.XPATH, "//input[contains(@placeholder, 'Org Name') or contains(@placeholder, 'Organization Name') or contains(@name, 'orgName') or contains(@name, 'name')]"
            )
            # Standard HTML5 validation check
            is_valid = self.driver.execute_script("return arguments[0].checkValidity();", org_name)
            self.assertFalse(is_valid, "Form submitted despite required fields being empty.")
        else:
            self.assertTrue(is_disabled, "Registration button is not disabled when input fields are empty.")

    # 4. OPERATOR REGISTRATION
    def test_TC_REG_05_register_as_operator_for_organization(self):
        """TC-REG-05: Register as an operator for an organization and verify request submission."""
        self.driver.get(BASE_URL)
        
        # Click Register as an Operator card
        operator_card = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Operator') or contains(text(), 'Select Operator')]")
        ))
        operator_card.click()
        time.sleep(1)

        # 1. Organization Code
        org_code = self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[contains(@placeholder, 'e.g. ORG-101') ]")
        ))
        org_code.click()
        org_code.send_keys("ORG-101")

        # 2. Operator Full Name
        op_name = self.driver.find_element(
            By.XPATH, "//input[contains(@placeholder, 'Enter Name')]"
        )
        op_name.send_keys("Sama Silva")

        # 3. Operator Email
        op_email = self.driver.find_element(
            By.XPATH, "//input[@type='email' or contains(@placeholder, 'name@domain.com')]"
        )
        op_email.send_keys("johndoe@domain.com")

        # 4. Password setup field & Confirm Password field
        pass_inputs = self.driver.find_elements(
            By.XPATH, "//input[@type='password' or contains(@placeholder, '••••••••') or contains(@placeholder, 'Password')]"
        )
        if len(pass_inputs) >= 2:
            pass_inputs[0].send_keys("OperatorPass123!")
            pass_inputs[1].send_keys("OperatorPass123!")
        else:
            password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password_field.send_keys("OperatorPass123!")

        # 5. Reason for Access / Notes (optional/mandatory)
        reason_fields = self.driver.find_elements(
            By.XPATH, "//textarea | //input[contains(@placeholder, 'Reason') or contains(@name, 'reason')]"
        )
        if reason_fields:
            reason_fields[0].send_keys("Requesting operator monitoring access for Central Station.")

        # 6. Submit Operator Request
        submit_btn = self.driver.find_element(
            By.XPATH, "//button[@type='submit'] | //button[contains(., 'Request') or contains(., 'Register') or contains(., 'Submit')]"
        )
        self.assertTrue(submit_btn.is_enabled(), "Operator registration button is disabled.")
        submit_btn.click()
        time.sleep(1)

        # 7. Verification of success prompt
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.assertIn("submitted", alert_text.lower())
            alert.accept()
        except Exception:
            success_element = self.driver.find_element(
                By.XPATH, "//*[contains(text(), 'submitted') or contains(text(), 'Request Sent') or contains(text(), 'successful')]"
            )
            self.assertTrue(success_element.is_displayed(), "Operator registration request confirmation not displayed.")

if __name__ == "__main__":
    unittest.main()
