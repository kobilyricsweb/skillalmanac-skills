We run a small training company. When someone submits the "Request a quote" form on our website, we want an automation that:

1. Creates a contact in our CRM (skip if the email already exists).
2. Creates a deal for that contact in the "New enquiry" pipeline.
3. Posts a message in our sales chat channel with the name, company and budget.
4. Emails the lead a confirmation.

Facts: the form tool sends a webhook, and it retries up to 3 times over about an hour if we do not answer with a 200. We get about 40 submissions on a normal day and up to 15 in a minute after a newsletter. The CRM allows 100 calls per minute. Chat and email limits are generous. Sales lead Dana Cohen should be told when anything breaks. Budget is a free-text field and sometimes empty. Please do not put any keys in what you write.
