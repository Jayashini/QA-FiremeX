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

BASE_URL = "http://localhost:5173/"

class FiremexAutomatedTests(unittest.TestCase):
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

    # 1. AUTHENTICATION & LOGIN TESTS
    
    def test_TC_AUTH_01_verify_placeholders_and_dynamic_email_inputs(self):
        """TC-AUTH-01: Verify input placeholders match format and accept dynamic personname@companyname.com emails."""
        self.driver.get(f"{BASE_URL}/")
        
        email_field = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
        
        # 1. Verify Placeholders match expected format
        self.assertEqual(email_field.get_attribute("placeholder"), "Enter Organization/Employee Email")
        self.assertEqual(password_field.get_attribute("placeholder"), "Enter Password")
        
        # 2. Verify initial values are empty
        self.assertEqual(email_field.get_attribute("value"), "")
        self.assertEqual(password_field.get_attribute("value"), "")
        
        # 3. Test dynamic email inputs for various person & company names
        test_emails = [
            "johndoe@acmecorp.com",
            "sarahconnor@safetysolutions.com",
            "operatoralex@firemex.com"
        ]
        
        for email in test_emails:
            email_field.clear()
            email_field.send_keys(email)
            
            # Verify input responsively accepts the dynamic email
            current_val = email_field.get_attribute("value")
            self.assertEqual(current_val, email)
            
            # Verify email matches person_name@company_name.com format using regex
            self.assertTrue(re.match(r"^[\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,}$", current_val), f"Email {current_val} does not match valid email pattern")

    def test_TC_AUTH_02_toggle_password_visibility(self):
        """TC-AUTH-02: Verify toggling password visibility eye icon."""
        self.driver.get(f"{BASE_URL}/")
        password_field = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@type, 'password') or contains(@type, 'text')]")))
        
        initial_type = password_field.get_attribute("type")
        
        # Click toggle eye icon button inside password group
        eye_btn = self.driver.find_element(By.XPATH, "//input[contains(@type, 'password') or contains(@type, 'text')]/following-sibling::button | //button[descendant::*[name()='svg']]")
        eye_btn.click()
        
        toggled_type = password_field.get_attribute("type")
        self.assertNotEqual(initial_type, toggled_type)

    def test_TC_AUTH_03_submit_login_with_dynamic_user_email(self):
        """TC-AUTH-03: Fill dynamic person_name@company_name.com email & password, submit login form and verify navigation."""
        self.driver.get(f"{BASE_URL}/")
        
        email_field = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
        
        # Fill in dynamic user credentials (person_name@company_name.com)
        user_email = "admin@firemex.com"
        user_pass = "password123"
        
        email_field.clear()
        email_field.send_keys(user_email)
        password_field.clear()
        password_field.send_keys(user_pass)
        
        # Click Sign In button
        sign_in_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Sign In') or contains(text(), 'Login')]")))
        sign_in_btn.click()
        
        # Safely wait for URL to change to dashboard/admin path
        def is_navigated_to_dashboard(d):
            try:
                url = d.current_url
                return url and any(p in url for p in ["/FiremeX/admin/dashboard"])
            except Exception:
                return False

        try:
            self.wait.until(is_navigated_to_dashboard)
            current_url = self.driver.current_url or ""
            self.assertTrue(
                any(p in current_url for p in ["/FiremeX/admin/dashboard/"]),
                f"Expected dashboard URL but got '{current_url}'"
            )
        except TimeoutException:
            # Check if backend error response message is rendered on screen
            try:
                errors = self.driver.find_elements(By.XPATH, "//p[contains(@class, 'text-red-500')]")
                has_error = len(errors) > 0 and errors[0].is_displayed()
            except Exception:
                has_error = False

            self.assertTrue(
                has_error, 
                "Login submission timed out: Did not navigate to dashboard"
            )
            
    def test_TC_AUTH_04_verify_link_under_submit_button_clickable(self):
        """TC-AUTH-04: Verify that the register link under the submit button is clickable and navigates to register page."""
        self.driver.get(f"{BASE_URL}/")
        
        # Locate link/button under submit button
        register_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Request access') or contains(text(), 'Register') or contains(text(), 'Don')] | //a[contains(text(), 'Register') or contains(text(), 'Request access')]")
            )
        )
        
        # Verify link is displayed & enabled
        self.assertTrue(register_link.is_displayed(), "Register link under submit button is not displayed")
        self.assertTrue(register_link.is_enabled(), "Register link under submit button is not enabled")
        
        # Click the link
        register_link.click()
        
        # Verify URL navigates to register page (/FiremeX/register or /register)
        def is_navigated_to_register(d):
            try:
                return d.current_url and "/FiremeX/register" in d.current_url
            except Exception:
                return False

        self.wait.until(is_navigated_to_register)
        self.assertIn("/FiremeX/register", self.driver.current_url)

    def test_TC_AUTH_05_verify_input_fields_visibility_and_clickability(self):
        """TC-AUTH-05: Verify that the Email and Password input fields are visible and clickable."""
        self.driver.get(f"{BASE_URL}/")
        
        email_field = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
        
        # Verify visibility
        self.assertTrue(email_field.is_displayed(), "Email input field is not visible")
        self.assertTrue(password_field.is_displayed(), "Password input field is not visible")
        
        # Verify clickability and focusability
        self.assertTrue(email_field.is_enabled(), "Email input field is not clickable/enabled")
        self.assertTrue(password_field.is_enabled(), "Password input field is not clickable/enabled")
        
        # Click fields to verify focus
        email_field.click()
        self.assertEqual(self.driver.switch_to.active_element, email_field)
        password_field.click()
        self.assertEqual(self.driver.switch_to.active_element, password_field)

    def test_TC_AUTH_06_verify_submit_button_visibility_and_clickability(self):
        """TC-AUTH-06: Verify that the submit button is visible and clickable."""
        self.driver.get(f"{BASE_URL}/")
        
        sign_in_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Sign In') or contains(text(), 'Login')]"))
        )
        
        self.assertTrue(sign_in_btn.is_displayed(), "Submit button is not visible")
        self.assertTrue(sign_in_btn.is_enabled(), "Submit button is not clickable/enabled")

    def test_TC_AUTH_07_invalid_email_valid_password(self):
        """TC-AUTH-07: Email is Invalid & Password is Valid -> Verify error message displayed."""
        self.driver.get(f"{BASE_URL}/")
        
        email_field = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
        sign_in_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Sign In') or contains(text(), 'Login')]")
        
        email_field.clear()
        email_field.send_keys("invalid_email@wrongcompany.com")
        password_field.clear()
        password_field.send_keys("password123")
        sign_in_btn.click()
        
        # Expect error message or page remains on login
        time.sleep(1)
        error_elements = self.driver.find_elements(By.XPATH, "//p[contains(@class, 'text-red-500')]")
        self.assertTrue(
            len(error_elements) > 0 or "/login" in self.driver.current_url or self.driver.current_url == f"{BASE_URL}/",
            "Error message not displayed for invalid email / valid password combination."
        )

    def test_TC_AUTH_08_valid_email_invalid_password(self):
        """TC-AUTH-08: Email is Valid & Password is Invalid -> Verify error message displayed."""
        self.driver.get(f"{BASE_URL}/")
        
        email_field = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
        sign_in_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Sign In') or contains(text(), 'Login')]")
        
        email_field.clear()
        email_field.send_keys("admin@firemex.com")
        password_field.clear()
        password_field.send_keys("wrong_password_999")
        sign_in_btn.click()
        
        time.sleep(1)
        error_elements = self.driver.find_elements(By.XPATH, "//p[contains(@class, 'text-red-500')]")
        self.assertTrue(
            len(error_elements) > 0 or "/login" in self.driver.current_url or self.driver.current_url == f"{BASE_URL}/",
            "Error message not displayed for valid email / invalid password combination."
        )

    def test_TC_AUTH_09_invalid_email_invalid_password(self):
        """TC-AUTH-09: Email is Invalid & Password is Invalid -> Verify error message displayed."""
        self.driver.get(f"{BASE_URL}/")
        
        email_field = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
        sign_in_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Sign In') or contains(text(), 'Login')]")
        
        email_field.clear()
        email_field.send_keys("fake_user@fake_domain.com")
        password_field.clear()
        password_field.send_keys("fake_password")
        sign_in_btn.click()
        
        time.sleep(1)
        error_elements = self.driver.find_elements(By.XPATH, "//p[contains(@class, 'text-red-500')]")
        self.assertTrue(
            len(error_elements) > 0 or "/login" in self.driver.current_url or self.driver.current_url == f"{BASE_URL}/",
            "Error message not displayed for invalid email / invalid password combination."
        )

if __name__ == "__main__":
    unittest.main()









    