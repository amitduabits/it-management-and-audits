# Screenshots

This directory is reserved for screenshots that illustrate the testing workflow. Add screenshots here to document:

---

## Suggested Screenshots

### 1. API Server Running
Capture the terminal output after running `python -m api.app`, showing the server startup message and listening port.

**Filename:** `01_server_startup.png`

### 2. Postman Collection Imported
Show the Postman sidebar with the full Payment Processing API collection expanded, displaying all request folders and endpoints.

**Filename:** `02_postman_collection.png`

### 3. Postman Environment Configured
Screenshot of the environment variables panel showing all configured keys (base_url, api_key, admin_api_key, etc.).

**Filename:** `03_postman_environment.png`

### 4. Successful Payment Creation
Show a Postman request to `POST /v1/payments` returning 201 with the payment JSON body. Include both the request and response panels.

**Filename:** `04_create_payment_201.png`

### 5. Validation Error Response
Show the 422 response returned when submitting a payment with missing or invalid fields. Highlight the structured error array.

**Filename:** `05_validation_error_422.png`

### 6. Authentication Failure
Capture the 401 response when calling a protected endpoint without an API key.

**Filename:** `06_auth_error_401.png`

### 7. Payment Declined (402)
Show the response when creating a payment with amount `13.00` (triggers simulated card decline).

**Filename:** `07_payment_declined_402.png`

### 8. Postman Collection Runner Results
Screenshot of the Collection Runner after executing all tests, showing the pass/fail summary for each request.

**Filename:** `08_collection_runner_results.png`

### 9. Pytest Output
Terminal output of running `pytest tests/ -v` showing all test cases with their pass/fail status.

**Filename:** `09_pytest_output.png`

### 10. Integration Test Runner Output
Terminal output from running `python -m tests.test_runner` showing the test summary report.

**Filename:** `10_test_runner_output.png`

---

## How to Add Screenshots

1. Take the screenshot using your preferred tool.
2. Save the file in this directory (`docs/screenshots/`).
3. Use descriptive filenames matching the suggestions above.
4. Reference them in documentation using relative paths:

```markdown
![Server Startup](docs/screenshots/01_server_startup.png)
```
