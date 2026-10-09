import os
import unittest
import time
import re
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = os.getenv("FIREMEX_BASE_URL", "http://localhost:5173/FiremeX/register")

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

    def _wait_for_registration_toast(self, expected_title="Registration Successful"):
        title = self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//p[normalize-space(.)='Registration Successful' or normalize-space(.)='Registration Failed']")
        ))
        message = title.find_element(By.XPATH, "following-sibling::p").text
        self.assertEqual(
            title.text,
            expected_title,
            f"Expected toast title {expected_title!r}, got {title.text!r}: {message}",
        )
        return message

    def _select_organization_sector_and_country(self, country_name="United States"):
        sector = self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//label[normalize-space()='Sector']/following-sibling::select")
        ))
        Select(sector).select_by_visible_text("Industrial")

        country = self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//label[normalize-space()='Country']/following-sibling::select")
        ))
        Select(country).select_by_visible_text(country_name)

    def _create_operator_test_organization(self):
        org_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Organization') or contains(text(), 'Select Organization')]")
        ))
        org_btn.click()

        organization_name = f"Operator Validation Org {uuid.uuid4().hex[:8]}"
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Org Name']").send_keys(
            organization_name
        )
        self._select_organization_sector_and_country()
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Organization Email']").send_keys(
            f"admin+{uuid.uuid4().hex[:8]}@safetysolutions.com"
        )
        self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter Organization Contact Number']"
        ).send_keys("+1 202-555-0123")
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Administrator Name']").send_keys(
            "Mary Admin"
        )

        password_fields = self.driver.find_elements(By.XPATH, "//input[@type='password']")
        self.assertEqual(len(password_fields), 2, "Expected password and confirmation inputs.")
        password_fields[0].send_keys("SecurePass123!")
        password_fields[1].send_keys("SecurePass123!")

        self.driver.find_element(
            By.XPATH, "//button[@type='submit' and contains(normalize-space(.), 'Complete Registration')]"
        ).click()
        toast_message = self._wait_for_registration_toast()
        self.assertIn(f'Organization "{organization_name}" registered!', toast_message)
        org_code_match = re.search(r"ORG-\d{3}", toast_message)
        self.assertIsNotNone(org_code_match, "Organization registration toast did not include an ORG-000 code.")
        self.wait.until(EC.url_contains("/FiremeX/login"))
        return org_code_match.group(0)

    def _prepare_operator_form(self, org_code, email, password, confirmation, fill_fields=True):
        self.driver.get(BASE_URL)
        operator_card = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Operator') or contains(text(), 'Select Operator')]")
        ))
        operator_card.click()

        self.driver.execute_script(
            "window.__operatorRegistrationRequests = 0;"
            "const originalFetch = window.fetch.bind(window);"
            "window.fetch = (...args) => {"
            "  if (/register|operator/i.test(String(args[0]))) {"
            "    window.__operatorRegistrationRequests += 1;"
            "  }"
            "  return originalFetch(...args);"
            "};"
        )

        if fill_fields:
            self.driver.find_element(
                By.XPATH, "//input[contains(@placeholder, 'e.g. ORG-101') or contains(@placeholder, 'ORG-101')]"
            ).send_keys(org_code)
            self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Enter Name')]").send_keys(
                "Sama Silva"
            )
            self.driver.find_element(
                By.XPATH, "//input[@type='email' or contains(@placeholder, 'name@domain.com')]"
            ).send_keys(email)
            password_fields = self.driver.find_elements(By.XPATH, "//input[@type='password']")
            self.assertEqual(len(password_fields), 2, "Expected password and confirmation inputs.")
            password_fields[0].send_keys(password)
            password_fields[1].send_keys(confirmation)

            reason_fields = self.driver.find_elements(
                By.XPATH, "//textarea | //input[contains(@placeholder, 'Reason') or contains(@name, 'reason')]"
            )
            if reason_fields:
                reason_fields[0].send_keys("Requesting operator monitoring access.")

    def _assert_operator_registration_rejected(self, expected_error_pattern=None):
        submit_btn = self.driver.find_element(
            By.XPATH, "//button[@type='submit' or contains(normalize-space(.), 'Request') or contains(normalize-space(.), 'Register') or contains(normalize-space(.), 'Submit')]"
        )
        submit_btn.click()

        def get_validation_message(_):
            error_nodes = self.driver.find_elements(
                By.XPATH,
                "//*[@role='alert' or @aria-live='assertive' or @aria-live='polite']"
                " | //p[normalize-space(.)='Registration Failed']/following-sibling::p[1]",
            )
            for node in error_nodes:
                if node.is_displayed() and node.text.strip():
                    return node.text.strip()

            invalid_fields = self.driver.find_elements(By.CSS_SELECTOR, "form :invalid")
            for field in invalid_fields:
                message = field.get_attribute("validationMessage")
                if message:
                    return message
            return False

        error_message = WebDriverWait(self.driver, 3).until(get_validation_message)
        if expected_error_pattern:
            self.assertRegex(error_message, expected_error_pattern)
        self.assertEqual(
            self.driver.execute_script("return window.__operatorRegistrationRequests;"),
            0,
            "Operator registration request was sent despite invalid form input.",
        )
        self.assertIn("/register", self.driver.current_url)

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

        # 2. Sector and country dropdowns
        self._select_organization_sector_and_country()

        # 3. Organization Email & Format validation (name@company.com)
        org_email = self.driver.find_element(
            By.XPATH, "//input[@type='email' or contains(@placeholder, 'Email') or contains(@name, 'email')]"
        )
        self.assertTrue(org_email.is_enabled(), "Organization email field is not clickable.")
        test_email = f"admin+{uuid.uuid4().hex[:8]}@safetysolutions.com"
        org_email.clear()
        org_email.send_keys(test_email)
        self.assertTrue(re.match(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$", org_email.get_attribute("value")),
                        "Email format name@company.com validation failed.")

        # 4. Contact Number Input Field & Format Validation
        contact_field = self.driver.find_element(
            By.XPATH, "//input[contains(@type, 'tel') or contains(@placeholder, 'Contact') or contains(@placeholder, 'Phone') or contains(@name, 'phone')]"
        )
        self.assertTrue(contact_field.is_enabled(), "Contact number field is not clickable.")
        contact_field.clear()
        contact_field.send_keys("+1 202-555-0123")
        self.assertTrue(re.match(r"^\+?[\d\s\-]{7,15}$", contact_field.get_attribute("value")),
                        "Contact number format is invalid.")

        # 5. Administrator Name
        admin_name = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter Administrator Name']"
        )
        self.assertTrue(admin_name.is_enabled(), "Administrator name field is not clickable.")
        admin_name.send_keys("Mary Admin")

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
            By.XPATH, "//button[@type='button' and contains(@class, 'inset-y-0') and contains(@class, 'right-0')]"
        )
        self.assertEqual(len(eye_toggle_icons), 2, "Expected eye toggles for password and confirmation fields.")
        eye_btn = eye_toggle_icons[0]
        self.assertTrue(eye_btn.is_displayed(), "Eye toggle icon in password field is not visible.")
        self.assertEqual(password_field.get_attribute("type"), "password")
        eye_btn.click()
        self.wait.until(lambda _: password_field.get_attribute("type") == "text")
        self.assertEqual(confirm_password_field.get_attribute("type"), "text")
        eye_btn.click()
        self.wait.until(lambda _: password_field.get_attribute("type") == "password")
        self.assertEqual(confirm_password_field.get_attribute("type"), "password")

        # 9. Verify Registration button status and submit
        submit_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@type='submit' and contains(normalize-space(.), 'Complete Registration')]")
            )
        )
        self.assertTrue(submit_btn.is_enabled(), "Registration button is disabled after filling required inputs.")
        submit_btn.click()

        toast_message = self._wait_for_registration_toast()
        self.assertIn('Organization "Safety Solutions Corp" registered!', toast_message)
        self.assertRegex(toast_message, r"ORG-\d+")
        self.wait.until(EC.url_contains("/FiremeX/login"))

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

    def test_TC_REG_06_mismatched_passwords_show_error_toast_without_submitting(self):
        """Mismatched passwords show the in-page error toast and do not submit."""
        org_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Organization') or contains(text(), 'Select Organization')]")
        ))
        org_btn.click()

        self._select_organization_sector_and_country()
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Org Name']").send_keys("Mismatch Test Org")
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Organization Email']").send_keys(
            f"mismatch+{uuid.uuid4().hex[:8]}@safetysolutions.com"
        )
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Organization Contact Number']").send_keys(
            "+1 202-555-0123"
        )
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Administrator Name']").send_keys("Mary Admin")

        password_fields = self.driver.find_elements(
            By.XPATH, "//input[@placeholder='••••••••••••']"
        )
        self.assertEqual(len(password_fields), 2, "Expected password and confirmation inputs.")
        password_fields[0].send_keys("SecurePass123!")
        password_fields[1].send_keys("DifferentPass123!")

        self.driver.find_element(
            By.XPATH, "//button[@type='submit' and normalize-space(.)='Complete Registration']"
        ).click()
        message = self._wait_for_registration_toast("Registration Failed")
        self.assertEqual(message, "Passwords do not match")
        self.assertIn("/register", self.driver.current_url)

    def test_TC_REG_07_reject_phone_number_that_does_not_match_country(self):
        """Country-mismatched contact numbers are rejected before registration."""
        org_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Organization') or contains(text(), 'Select Organization')]")
        ))
        org_btn.click()

        self._select_organization_sector_and_country("United States")
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Org Name']").send_keys(
            "Phone Country Validation Org"
        )
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Organization Email']").send_keys(
            f"phone-country+{uuid.uuid4().hex[:8]}@safetysolutions.com"
        )
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Organization Contact Number']").send_keys(
            "+94 77 123 4567"
        )
        self.driver.find_element(By.XPATH, "//input[@placeholder='Enter Administrator Name']").send_keys("Mary Admin")

        password_fields = self.driver.find_elements(
            By.XPATH, "//input[@placeholder='••••••••••••']"
        )
        self.assertEqual(len(password_fields), 2, "Expected password and confirmation inputs.")
        password_fields[0].send_keys("SecurePass123!")
        password_fields[1].send_keys("SecurePass123!")

        self.driver.execute_script(
            "window.__organizationRegistrationRequests = 0;"
            "const originalFetch = window.fetch.bind(window);"
            "window.fetch = (...args) => {"
            "  if (String(args[0]).includes('register/organization')) {"
            "    window.__organizationRegistrationRequests += 1;"
            "  }"
            "  return originalFetch(...args);"
            "};"
        )
        self.driver.find_element(
            By.XPATH, "//button[@type='submit' and normalize-space(.)='Complete Registration']"
        ).click()

        message = self._wait_for_registration_toast("Registration Failed")
        self.assertEqual(message, "Contact number format mismatch")
        self.assertIn("/register", self.driver.current_url)
        self.assertEqual(
            self.driver.execute_script("return window.__organizationRegistrationRequests;"),
            0,
            "Registration request was sent despite the country/phone mismatch.",
        )

    # 4. OPERATOR REGISTRATION
    def test_TC_REG_05_register_as_operator_for_organization(self):
        """TC-REG-05: Register as an operator for an organization and verify request submission."""
        self.driver.get(BASE_URL)

        # Create a real organization first so the operator flow can use a valid org code.
        org_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Organization') or contains(text(), 'Select Organization')]")
        ))
        org_btn.click()
        time.sleep(1)

        org_name = self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[contains(@placeholder, 'Enter Org Name') or contains(@placeholder, 'Organization Name') or contains(@name, 'orgName') or contains(@name, 'name')]")
        ))
        org_name.send_keys("Safety Solutions Corp")

        self._select_organization_sector_and_country()
        self.driver.find_element(By.XPATH, "//input[@type='email' or contains(@placeholder, 'Business Email') or contains(@placeholder, 'Organization Email')] ").send_keys(f"admin+{uuid.uuid4().hex[:8]}@safetysolutions.com")
        self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Enter Organization Contact Number') or contains(@placeholder, 'Contact Number') or contains(@type, 'tel')] ").send_keys("+1 202-555-0123")
        self.driver.find_element(By.XPATH, "//input[@type='text' and contains(@placeholder, 'Enter Administrator Name')] ").send_keys("Mary Admin")

        password_fields = self.driver.find_elements(By.XPATH, "//input[@type='password' or contains(@placeholder, '••••••••••••')]")
        self.assertEqual(len(password_fields), 2, "Expected password and confirmation inputs.")
        password_fields[0].send_keys("SecurePass123!")
        password_fields[1].send_keys("SecurePass123!")

        self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(normalize-space(.), 'Complete Registration')]").click()
        toast_message = self._wait_for_registration_toast()
        self.assertIn('Organization "Safety Solutions Corp" registered!', toast_message)
        org_code_match = re.search(r"ORG-\d+", toast_message)
        self.assertIsNotNone(org_code_match, "Organization registration toast did not include an organization code.")
        org_code = org_code_match.group(0)

        self.wait.until(EC.url_contains("/FiremeX/login"))
        self.driver.get(BASE_URL)

        # Click Register as an Operator card
        operator_card = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Operator') or contains(text(), 'Select Operator')]")
        ))
        operator_card.click()
        time.sleep(1)

        # 1. Organization Code
        org_code_input = self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[contains(@placeholder, 'e.g. ORG-101') or contains(@placeholder, 'ORG-101')]")
        ))
        org_code_input.click()
        org_code_input.send_keys(org_code)

        # 2. Operator Full Name
        op_name = self.driver.find_element(
            By.XPATH, "//input[contains(@placeholder, 'Enter Name')]"
        )
        op_name.send_keys("Sama Silva")

        # 3. Operator Email
        op_email = self.driver.find_element(
            By.XPATH, "//input[@type='email' or contains(@placeholder, 'name@domain.com')]"
        )
        op_email.send_keys(f"operator+{uuid.uuid4().hex[:8]}@domain.com")

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
            By.XPATH, "//button[@type='submit' or contains(normalize-space(.), 'Request') or contains(normalize-space(.), 'Register') or contains(normalize-space(.), 'Submit')]"
        )
        self.assertTrue(submit_btn.is_enabled(), "Operator registration button is disabled.")
        submit_btn.click()

        toast_message = self._wait_for_registration_toast()
        self.assertIn(
            "Access request submitted! Pending approval from the organization administrator.",
            toast_message,
        )
        self.wait.until(EC.url_contains("/FiremeX/login"))

    def test_TC_REG_08_reject_operator_invalid_organization_code_format(self):
        """Malformed organization codes show a validation error without sending the request."""
        org_code = self._create_operator_test_organization()
        malformed_org_code = org_code.replace("-", "_")
        self._prepare_operator_form(
            malformed_org_code,
            f"operator+{uuid.uuid4().hex[:8]}@domain.com",
            "OperatorPass123!",
            "OperatorPass123!",
        )
        self._assert_operator_registration_rejected(r"(?i)(organization|org|code|format|invalid)")

    def test_TC_REG_09_reject_operator_invalid_email_format(self):
        """Malformed operator emails show a validation error without sending the request."""
        org_code = self._create_operator_test_organization()
        self._prepare_operator_form(
            org_code,
            "operator-email-without-domain",
            "OperatorPass123!",
            "OperatorPass123!",
        )
        self._assert_operator_registration_rejected(r"(?i)(email|@|valid|format)")

    def test_TC_REG_10_reject_operator_mismatched_passwords(self):
        """Mismatched operator passwords show a validation error without sending the request."""
        org_code = self._create_operator_test_organization()
        self._prepare_operator_form(
            org_code,
            f"operator+{uuid.uuid4().hex[:8]}@domain.com",
            "OperatorPass123!",
            "DifferentPass123!",
        )
        self._assert_operator_registration_rejected(r"(?i)(password|match|confirm|different)")

    def test_TC_REG_11_reject_operator_empty_required_fields(self):
        """Empty operator registration fields show a validation error without sending the request."""
        self.driver.get(BASE_URL)
        operator_card = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Register as an Operator') or contains(text(), 'Select Operator')]")
        ))
        operator_card.click()
        self.driver.execute_script(
            "window.__operatorRegistrationRequests = 0;"
            "const originalFetch = window.fetch.bind(window);"
            "window.fetch = (...args) => {"
            "  if (/register|operator/i.test(String(args[0]))) {"
            "    window.__operatorRegistrationRequests += 1;"
            "  }"
            "  return originalFetch(...args);"
            "};"
        )
        self._assert_operator_registration_rejected()

if __name__ == "__main__":
    unittest.main()
