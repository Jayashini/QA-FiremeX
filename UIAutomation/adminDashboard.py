import os
import re
import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


APP_URL = os.getenv("FIREMEX_BASE_URL", "http://localhost:5173/FiremeX").rstrip("/")
DASHBOARD_URL = f"{APP_URL}/admin/dashboard"
LOGIN_URL = f"{APP_URL}/login"
ADMIN_EMAIL = os.getenv("FIREMEX_ADMIN_EMAIL", "admin@firemex.com")
ADMIN_PASSWORD = os.getenv("FIREMEX_ADMIN_PASSWORD", "password123")


class FiremexAdminDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        if os.getenv("FIREMEX_HEADLESS", "").lower() in {"1", "true", "yes"}:
            chrome_options.add_argument("--headless=new")

        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "driver", None):
            cls.driver.quit()

    def setUp(self):
        self.driver.get(DASHBOARD_URL)
        try:
            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//h1[normalize-space()='Dashboard']")
                )
            )
        except TimeoutException:
            self.driver.get(LOGIN_URL)
            email = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//input[@type='email']"))
            )
            password = self.driver.find_element(By.XPATH, "//input[@type='password']")
            email.clear()
            email.send_keys(ADMIN_EMAIL)
            password.clear()
            password.send_keys(ADMIN_PASSWORD)
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(translate(normalize-space(.),"
                        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sign in')]",
                    )
                )
            ).click()
            self.wait.until(EC.url_contains("/admin/dashboard"))
            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//h1[normalize-space()='Dashboard']")
                )
            )

    @staticmethod
    def _text_xpath(text):
        return f"//*[normalize-space(.)='{text}']"

    def _sidebar_item(self, label):
        return self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//aside//*[self::a or self::button]"
                    f"[normalize-space(.)='{label}']"
                    f" | //nav//*[self::a or self::button]"
                    f"[normalize-space(.)='{label}']",
                )
            )
        )

    def _notification_button(self):
        return self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(translate(@aria-label,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'notification') "
                    "or contains(translate(@title,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'notification') "
                    "or contains(translate(@aria-label,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'alert')]"
                    " | //header//button[.//*[name()='svg']][last()]",
                )
            )
        )

    def _recent_incidents_panel(self):
        heading = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[self::h2 or self::h3][normalize-space()='Recent Incidents']")
            )
        )
        return heading.find_element(By.XPATH, "ancestor::*[.//table][1]")

    def _camera_preview_panel(self):
        heading = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//*[self::h2 or self::h3][contains(normalize-space(.), 'Camera Preview')]",
                )
            )
        )
        return heading.find_element(By.XPATH, "ancestor::*[.//img or .//video][1]")

    # TC_DB_001: Verify the notification icon opens the alerts page.
    def test_TC_DB_001_notification_icon_is_clickable(self):
        self._notification_button().click()
        self.wait.until(EC.url_contains("/admin/alerts"))

    # TC_DB_002: Verify the notification icon displays its unviewed count.
    def test_TC_DB_002_notification_icon_shows_unviewed_count(self):
        button = self._notification_button()
        count = button.find_element(
            By.XPATH,
            ".//*[self::span or self::div][normalize-space(.) "
            "and string(number(normalize-space(.))) != 'NaN']",
        )
        self.assertTrue(count.is_displayed(), "Notification count should be visible.")
        self.assertGreater(int(count.text), 0, "Expected at least one unviewed notification.")

    # TC_DB_003: Verify each dashboard sidebar option navigates to its page.
    def test_TC_DB_003_sidebar_options_are_clickable(self):
        navigation = {
            "Dashboard": "/admin/dashboard",
            "Live Feed": "/admin/livefeed",
            "Incidents": "/admin/incidents",
            "Alerts": "/admin/alerts",
            "Users": "/admin/users",
            "Settings": "/admin/settings",
        }
        for label, route in navigation.items():
            with self.subTest(sidebar_item=label):
                if "/admin/dashboard" not in self.driver.current_url:
                    self.driver.get(DASHBOARD_URL)
                    self.wait.until(EC.url_contains("/admin/dashboard"))
                self._sidebar_item(label).click()
                self.wait.until(EC.url_contains(route))

    # TC_DB_004: Verify the selected sidebar page is visibly highlighted.
    def test_TC_DB_004_active_sidebar_item_is_highlighted(self):
        self._sidebar_item("Live Feed").click()
        self.wait.until(EC.url_contains("/admin/livefeed"))
        active_item = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//aside//*[self::a or self::button]"
                    "[normalize-space(.)='Live Feed' and "
                    "(@aria-current='page' or contains(@class,'border-l-4') "
                    "or contains(@class,'bg-'))]"
                    " | //nav//*[self::a or self::button]"
                    "[normalize-space(.)='Live Feed' and "
                    "(@aria-current='page' or contains(@class,'border-l-4') "
                    "or contains(@class,'bg-'))]",
                )
            )
        )
        self.assertTrue(active_item.is_displayed())

    # TC_DB_005: Verify the signed-in user's name and role appear in the sidebar footer.
    def test_TC_DB_005_user_name_and_role_are_visible_in_sidebar_footer(self):
        footer = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//*[normalize-space()='Administrator']/ancestor::*"
                    "[.//*[normalize-space()='Sign out']][1]",
                )
            )
        )
        self.assertIn("Administrator", footer.text)
        displayed_name = [
            line.strip()
            for line in footer.text.splitlines()
            if line.strip() and line.strip() not in {"Administrator", "Sign out"}
        ]
        self.assertTrue(displayed_name, "Signed-in user name should be visible.")
        expected_name = os.getenv("FIREMEX_EXPECTED_USER_NAME")
        if expected_name:
            self.assertIn(expected_name, footer.text)

    # TC_DB_006: Verify the user profile control can be clicked.
    def test_TC_DB_006_user_profile_icon_is_clickable(self):
        footer = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//*[normalize-space()='Administrator']/ancestor::*"
                    "[.//*[normalize-space()='Sign out']][1]",
                )
            )
        )
        profile_button = footer.find_element(
            By.XPATH,
            ".//button[.//*[name()='svg'] or normalize-space(.) "
            "or @aria-label or @title]",
        )
        self.wait.until(lambda _driver: profile_button.is_enabled())
        profile_button.click()
        self.assertTrue(profile_button.is_displayed())

    # TC_DB_007: Verify the dashboard summary cards show their displayed details.
    def test_TC_DB_007_dashboard_static_card_details_are_visible(self):
        expected_details = ("CAMERAS", "0", "CURRENT RISK LEVEL", "Elevated",
                            "ACTIVE ALERTS", "3", "2 unacknowledged")
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        for detail in expected_details:
            with self.subTest(detail=detail):
                self.assertIn(detail.lower(), page_text.lower())

    # TC_DB_008: Verify Recent Incidents status badges use the expected colors.
    def test_TC_DB_008_recent_incident_statuses_use_expected_colors(self):
        expected_status_colors = {
            "Fire detected": "red",
            "Smoke detected": "yellow",
            "Resolved": "green",
            "Camera offline": "gray",
        }
        panel = self._recent_incidents_panel()
        statuses_found = set()

        for row in panel.find_elements(By.XPATH, ".//tbody/tr"):
            status_cell = row.find_element(By.XPATH, "./td[last()]")
            for status, expected_color in expected_status_colors.items():
                status_elements = status_cell.find_elements(
                    By.XPATH, f".//*[normalize-space(.)='{status}']"
                )
                if not status_elements:
                    continue

                badge = status_elements[-1]
                statuses_found.add(status)
                background = badge.value_of_css_property("background-color")
                foreground = badge.value_of_css_property("color")
                self.assertTrue(
                    self._matches_color_family(background, expected_color)
                    or self._matches_color_family(foreground, expected_color),
                    f"{status!r} should use a {expected_color} status color; "
                    f"found background={background!r}, foreground={foreground!r}.",
                )

        self.assertSetEqual(
            statuses_found,
            set(expected_status_colors),
            "Recent Incidents should show Fire detected, Smoke detected, "
            "Resolved, and Camera offline statuses.",
        )

    @staticmethod
    def _matches_color_family(css_color, expected_family):
        oklch = re.search(
            r"oklch\(\s*[\d.]+%?\s+([\d.]+)\s+([\d.]+)",
            css_color,
            re.IGNORECASE,
        )
        if oklch:
            chroma, hue = map(float, oklch.groups())
            hue %= 360
            if expected_family == "red":
                return chroma >= 0.08 and (hue <= 40 or hue >= 340)
            if expected_family == "yellow":
                return chroma >= 0.08 and 50 <= hue < 115
            if expected_family == "green":
                return chroma >= 0.08 and 115 <= hue < 190
            if expected_family == "gray":
                return chroma < 0.06
            return False

        channels = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", css_color)
        if not channels:
            return False
        red, green, blue = map(int, channels.groups())
        if expected_family == "red":
            return red > green * 1.4 and red > blue * 1.4
        if expected_family == "yellow":
            return red > blue * 1.2 and green > blue * 1.15 and red < green * 1.7
        if expected_family == "green":
            return green > red * 1.2 and green > blue * 1.15
        if expected_family == "gray":
            return max(red, green, blue) - min(red, green, blue) < 70
        return False

    # TC_DB_009: Verify the Recent Incidents "View all" link opens incidents.
    def test_TC_DB_009_recent_incidents_view_all_link_is_clickable(self):
        panel = self._recent_incidents_panel()
        view_all = self.wait.until(
            lambda _driver: panel.find_element(
                By.XPATH,
                ".//*[self::a or self::button][normalize-space(.)='View all']",
            )
        )
        self.wait.until(lambda _driver: view_all.is_enabled())
        view_all.click()
        self.wait.until(EC.url_contains("/admin/incidents"))

    # TC_DB_010: Verify the incidents panel contains the five latest entries.
    def test_TC_DB_010_recent_incidents_shows_five_most_recent_rows(self):
        rows = self._recent_incidents_panel().find_elements(By.XPATH, ".//tbody/tr")
        self.assertEqual(len(rows), 5, "Dashboard should show only the five most recent incidents.")
        times = [row.find_element(By.XPATH, "./td[1]").text.strip() for row in rows]
        self.assertEqual(times, sorted(times, reverse=True), "Incidents should be newest first.")

    # TC_DB_011: Verify all required incident table columns are present.
    def test_TC_DB_011_recent_incidents_shows_required_columns(self):
        panel = self._recent_incidents_panel()
        headers = [
            header.text.strip().upper()
            for header in panel.find_elements(By.XPATH, ".//thead//th")
        ]
        self.assertEqual(headers, ["TIME", "CAMERA", "ZONE", "AI CONF.", "STATUS"])

    # TC_DB_012: Verify the camera preview displays its detection status.
    def test_TC_DB_012_camera_preview_shows_detection_status(self):
        preview = self._camera_preview_panel()
        preview_text = preview.text.upper()
        self.assertTrue(
            any(status in preview_text for status in ("FIRE", "SMOKE", "NORMAL", "DETECTED")),
            "Camera preview should show a detection status.",
        )

    # TC_DB_013: Verify the camera preview identifies a camera and its zone.
    def test_TC_DB_013_camera_preview_shows_camera_number_and_zone(self):
        preview = self._camera_preview_panel()
        preview_text = preview.text
        self.assertRegex(preview_text, r"(?i)\bCAM(?:ERA)?[- ]?\d+\b")
        self.assertRegex(preview_text, r"(?i)\bZONE\b|[A-Z][A-Za-z ]+")

    # TC_DB_014: Verify detected cameras are represented in the preview list.
    def test_TC_DB_014_all_detected_cameras_have_preview_entries(self):
        preview = self._camera_preview_panel()
        camera_entries = preview.find_elements(
            By.XPATH,
            ".//*[self::article or self::li or self::div]"
            "[.//*[contains(translate(normalize-space(.),"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'CAM')]]",
        )
        camera_labels = [
            entry.text
            for entry in camera_entries
            if entry.is_displayed()
            and self.driver.execute_script(
                "return /CAM(?:ERA)?[- ]?\\d+/i.test(arguments[0]);", entry.text
            )
        ]
        self.assertTrue(camera_labels, "Expected detected cameras to be listed in the preview.")
        for label in camera_labels:
            with self.subTest(camera=label.splitlines()[0]):
                self.assertRegex(label, r"(?i)\bCAM(?:ERA)?[- ]?\d+\b")
                self.assertRegex(label, r"(?i)\bZONE\b|[A-Z][A-Za-z ]+")

    # TC_DB_015: Verify the Dashboard sidebar item is highlighted on Dashboard.
    def test_TC_DB_015_dashboard_sidebar_item_is_highlighted(self):
        dashboard_item = self._sidebar_item("Dashboard")
        self.assertTrue(
            dashboard_item.get_attribute("aria-current") == "page"
            or "border-l-4" in (dashboard_item.get_attribute("class") or "")
            or "bg-" in (dashboard_item.get_attribute("class") or ""),
            "Dashboard navigation item should have its active styling.",
        )

    # TC_DB_016: Verify clicking Sign out ends the session and returns to Login.
    def test_TC_DB_016_sign_out_button_is_clickable(self):
        sign_out = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[self::a or self::button][normalize-space(.)='Sign out']")
            )
        )
        sign_out.click()
        self.wait.until(
            lambda driver: "/login" in driver.current_url.lower()
            or driver.current_url.rstrip("/") == APP_URL.rstrip("/")
        )

    # TC_DB_017: Verify the live time is visible next to the dashboard alert icon.
    def test_TC_DB_017_live_time_is_visible_next_to_alert_icon(self):
        notification = self._notification_button()
        live_time = self.wait.until(
            lambda driver: driver.execute_script(
                """
                const timePattern = /^LIVE\\s*\\|\\s*\\d{1,2}\\s*:\\s*\\d{2}\\s*:\\s*\\d{2}$/i;
                const candidates = [...document.querySelectorAll('header *, [role="banner"] *, body *')]
                    .filter(element => {
                        const text = element.textContent.replace(/\\s+/g, ' ').trim();
                        return timePattern.test(text) && element.getClientRects().length > 0;
                    })
                    .sort((left, right) => left.textContent.length - right.textContent.length);
                return candidates[0] || null;
                """
            )
        )

        self.assertTrue(live_time.is_displayed(), "The LIVE time should be visible in the header.")
        positions = self.driver.execute_script(
            """
            const live = arguments[0].getBoundingClientRect();
            const alert = arguments[1].getBoundingClientRect();
            return {
                sameRow: Math.abs((live.top + live.bottom) / 2 - (alert.top + alert.bottom) / 2) < 40,
                gap: Math.max(0, alert.left - live.right, live.left - alert.right)
            };
            """,
            live_time,
            notification,
        )
        self.assertTrue(positions["sameRow"], "Live time and alert icon should be aligned in the header.")
        self.assertLess(positions["gap"], 200, "Live time should be next to the alert icon.")


if __name__ == "__main__":
    unittest.main(verbosity=2)