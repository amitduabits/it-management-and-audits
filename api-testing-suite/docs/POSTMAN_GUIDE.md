# Postman Collection Guide

Step-by-step instructions for importing the Payment API collection into Postman and using it for manual or automated testing.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Importing the Collection](#importing-the-collection)
3. [Setting Up the Environment](#setting-up-the-environment)
4. [Running Individual Requests](#running-individual-requests)
5. [Using the Collection Runner](#using-the-collection-runner)
6. [Understanding the Test Scripts](#understanding-the-test-scripts)
7. [Workflow: End-to-End Payment Flow](#workflow-end-to-end-payment-flow)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Postman** desktop application (v10 or later) or the web version
- The Payment API running locally on `http://localhost:5000`
- The collection file: `postman/payment_api_collection.json`
- The environment file: `postman/environment.json`

Start the API server before testing:

```bash
python -m api.app
```

---

## Importing the Collection

1. Open Postman.
2. Click the **Import** button in the top-left area (or press `Ctrl+O` / `Cmd+O`).
3. Select the **File** tab.
4. Drag and drop or browse to `postman/payment_api_collection.json`.
5. Click **Import**.

You should see a new collection named **Payment Processing API** in the sidebar.

---

## Setting Up the Environment

1. Click the **Import** button again.
2. Import `postman/environment.json`.
3. In the top-right corner of Postman, click the environment dropdown.
4. Select **Payment API - Local Development**.

The environment contains these variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `base_url` | API base URL | `http://localhost:5000/v1` |
| `api_key` | Standard test API key | `demo_key_4eC39HqLyjWDarjtT1zdp7dc` |
| `admin_api_key` | Admin test API key | `demo_key_BQokikJOvBiI2HlWgH4olfQ2` |
| `readonly_api_key` | Read-only test key | `demo_key_readonly_9f8g7h6j5k4l3m2n` |
| `payment_id` | Auto-populated by test scripts | (empty) |
| `refund_id` | Auto-populated by test scripts | (empty) |
| `webhook_id` | Auto-populated by test scripts | (empty) |
| `auth_code` | Auto-populated by OAuth flow | (empty) |
| `access_token` | Auto-populated by OAuth flow | (empty) |

---

## Running Individual Requests

### Creating a Payment

1. Expand **Payments** in the collection sidebar.
2. Click **Create Payment**.
3. Review the request body in the **Body** tab. Modify the amount, currency, or other fields as needed.
4. Click **Send**.
5. Check the response:
   - **201 Created**: Payment completed successfully.
   - **402 Payment Required**: Payment was declined (try amount `13.00` to simulate).
   - **422 Unprocessable Entity**: Validation errors in the request body.

The test script automatically saves the `payment_id` variable for subsequent requests.

### Retrieving a Payment

1. Click **Get Payment** under the Payments folder.
2. The URL uses `{{payment_id}}`, which was set by the Create Payment test script.
3. Click **Send** to retrieve the payment details.

### Testing Authentication

1. Expand the **Authentication** folder.
2. Run **OAuth2 - Authorize** first to obtain an authorization code.
3. Then run **OAuth2 - Token Exchange** to convert the code into an access token.

The collection scripts chain these values automatically.

---

## Using the Collection Runner

To execute all requests in sequence:

1. Click the **...** menu on the collection name and select **Run collection**.
2. In the Collection Runner, configure:
   - **Iterations**: 1 (or more for load testing).
   - **Delay**: 100ms between requests (recommended for rate limiting).
3. Click **Run Payment Processing API**.

The runner executes all requests in order and displays pass/fail results for each test script.

### Recommended Execution Order

For best results, run the folders in this order:

1. **Admin > Reset Test Data** -- Start with a clean state.
2. **Health & Info** -- Verify the API is running.
3. **Payments** -- Create, retrieve, list, check status, cancel, refund.
4. **Authentication** -- Test OAuth2 flows.
5. **Webhooks** -- Register, list, simulate, delete.

---

## Understanding the Test Scripts

Each request includes a **Tests** tab with JavaScript assertions. Example:

```javascript
pm.test('Payment created successfully', function () {
    pm.expect(pm.response.code).to.be.oneOf([201, 402]);
});

pm.test('Payment ID returned', function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.id).to.match(/^pay_/);
    pm.collectionVariables.set('payment_id', jsonData.id);
});
```

These scripts:
- Validate the response status code and body structure.
- Extract values (like `payment_id`) and store them as variables for later requests.
- Appear as green (pass) or red (fail) in the test results panel.

---

## Workflow: End-to-End Payment Flow

Here is a complete flow you can execute manually:

### Step 1: Health Check
```
GET {{base_url}}/health
```
Verify the API is responding.

### Step 2: Create a Payment
```
POST {{base_url}}/payments
Body: {"amount": 99.99, "currency": "USD", "description": "Test order", "customer_email": "user@example.com"}
```
Note the returned `payment_id`.

### Step 3: Retrieve the Payment
```
GET {{base_url}}/payments/{{payment_id}}
```
Verify the payment details match.

### Step 4: Check Payment Status
```
GET {{base_url}}/payments/{{payment_id}}/status
```

### Step 5: Partial Refund
```
POST {{base_url}}/payments/{{payment_id}}/refund
Body: {"amount": 30.00, "reason": "requested_by_customer"}
```

### Step 6: Verify Payment Updated
```
GET {{base_url}}/payments/{{payment_id}}
```
Status should now be `partially_refunded`.

### Step 7: List All Payments
```
GET {{base_url}}/payments?page=1&per_page=10
```

---

## Troubleshooting

### "Could not send request"
- Verify the API server is running: `python -m api.app`
- Check that `base_url` in your environment points to `http://localhost:5000/v1`

### "401 Unauthorized"
- Verify the environment is selected (top-right dropdown).
- Check that the `api_key` variable is set correctly.
- The collection uses collection-level Bearer auth. Individual requests override this where needed (e.g., OAuth endpoints use "No Auth").

### "Variable not resolved"
- Run the **Create Payment** request before requests that use `{{payment_id}}`.
- Check the **Environment quick look** (eye icon) to see current variable values.

### "429 Too Many Requests"
- You are hitting the rate limit. Wait for the `Retry-After` duration.
- Run **Admin > Reset Test Data** to clear rate limit counters.
- Add a delay between requests in the Collection Runner settings.

### Postman Console
Open the Postman Console (`View > Show Postman Console` or `Ctrl+Alt+C`) to see raw request/response data and debug test scripts.
