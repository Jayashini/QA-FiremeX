
🚨 Defining Severity (Technical Impact)

Severity measures how much the defect breaks the software or blocks testing. It is a objective measure of technical damage.
• Critical (Blocker): The application crashes, data is corrupted, or a core function is completely broken with no workaround (e.g., users cannot log in or check out).
• Major: A core feature is broken or severely degraded, but a difficult workaround exists.
• Minor: A secondary feature does not work as expected, but the main user flow is unaffected.
• Trivial (Cosmetic): The software functions perfectly, but there are minor visual issues like typos, misaligned text, or wrong color shades.

📅 Defining Priority (Business Urgency)

Priority measures how quickly the team needs to fix the defect. It is a strategic measure based on business value and project timelines.
• P1 (Immediate / High): Must be fixed in the next immediate build or hotfix. Blocks the deployment or marketing launch.
• P2 (Medium): Should be fixed in the current sprint or release cycle before shipping to production.
• P3 (Low): Can be deferred to a future release or fixed when time permits.

📊 Matrix: How They Intersect

Severity and priority do not always match. Use this quick guide to handle unusual combinations:

Severity	Priority	Scenario Example	Action Plan
High	High	The checkout button crashes the entire app.	Fix immediately. Drop everything else.
High	Low	A crash occurs only on an obsolete browser version (e.g., Internet Explorer 11) that represents 0.01% of traffic.	Defer. The technical impact is massive, but it affects almost no business revenue.
Low	High	The company logo on the homepage is misspelled or upside down.	Fix quickly. It is a simple text change (low technical impact), but it severely hurts brand reputation (high business urgency).
Low	Low	A tiny typo in the privacy policy footer.	Backlog. Fix it during routine maintenance.

If you want, tell me:
• The specific bug you are trying to classify
• Your target audience or release deadline
I can help you pinpoint the exact priority and severity levels for it.
