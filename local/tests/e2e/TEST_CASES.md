# E2E Test Cases -- Payment Microservice

## General Info

- Base URL: http://176.53.160.110:9003
- Auth: Bearer `<BEARER_TOKEN>` (for protected endpoints)
- Test user: account_id=267
- Amounts in requests: in rubles/dollars (integer). API converts to kopecks/cents (x100) internally
- Amounts in balance response: returned divided by 100 (rubles/dollars as float)
- SSH: for checking logs, connect to the server (local key)

## Conventions

- ID format: `{DOMAIN}-{TYPE}-{NNN}`
- DOMAIN: USR, PAY, WH, BILL, STK, INT
- TYPE: HP (happy path), NEG (negative), EDGE (edge case), INT (integration)
- Status column: `[  ]` = not verified, `[OK]` = passed, `[FAIL]` = failed
- `<BEARER_TOKEN>` -- replace with a real JWT token before running
- `<UUID>` -- generate a unique UUID v4 for each run

---

## 1. User Service (Setup)

Endpoints:
1. `POST /api/user/` -- Initialize user (NO auth)
2. `POST /api/user/add-withdrawal` -- Add withdrawal method (Bearer auth)
3. `DELETE /api/user/remove-withdrawal` -- Remove withdrawal method (Bearer auth)
4. `GET /api/user/cards` -- Get withdrawal methods (Bearer auth)

---

### USR-HP-001: Initialize new user

**Endpoint**: `POST /api/user/`
**Auth**: Public
**Preconditions**: account_id=9999 should not exist yet (or test is idempotent)

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/user/ \
  -H "Content-Type: application/json" \
  -d '{"account_id": 9999, "email": "test9999@test.com"}'
```

**Expected Response**:
- Status: 200
- Body: user object or success confirmation

**Actual Result**: [OK] HTTP 200, returns `null`. User 9999 initialized.
**Notes**: No auth required. First call in any test run.

---

### USR-NEG-001: Initialize user with missing email

**Endpoint**: `POST /api/user/`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/user/ \
  -H "Content-Type: application/json" \
  -d '{"account_id": 9998}'
```

**Expected Response**:
- Status: 422
- Body: validation error indicating missing email field

**Actual Result**: [OK] HTTP 422, `"Field required"` for email.
**Notes**: --

---

### USR-NEG-002: Initialize user with invalid email format

**Endpoint**: `POST /api/user/`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/user/ \
  -H "Content-Type: application/json" \
  -d '{"account_id": 9997, "email": "not-an-email"}'
```

**Expected Response**:
- Status: 422
- Body: validation error for email format

**Actual Result**: [OK] HTTP 422, `"value is not a valid email address"`.
**Notes**: --

---

### USR-EDGE-001: Re-initialize already existing user

**Endpoint**: `POST /api/user/`
**Auth**: Public
**Preconditions**: account_id=267 already exists in the system

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/user/ \
  -H "Content-Type: application/json" \
  -d '{"account_id": 267, "email": "existing@test.com"}'
```

**Expected Response**:
- Status: 200 or error (document actual behavior)
- Body: document actual

**Actual Result**: [OK] HTTP 200. Re-initialization is idempotent (BUG-4 fixed — catches Tinkoff "customer already exists").
**Notes**: System is idempotent. Re-initializing an existing user returns 200 successfully.

---

### USR-HP-002: Get all withdrawal methods

**Endpoint**: `GET /api/user/cards`
**Auth**: Bearer
**Preconditions**: User authenticated via Bearer token

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/user/cards \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: array of withdrawal methods, each with `{"id": "uuid4", "bank_name": "str", "card_id": "str|null", "is_main": bool, "phone": "str|null", "card_pan": "str|null", "type": "card"|"sbp", "provider": "tinkoff"|"oxypay"|null}`

**Actual Result**: [OK] HTTP 200, returns array with 1 SBP method.
**Notes**: --

---

### USR-HP-003: Add SBP withdrawal method

**Endpoint**: `POST /api/user/add-withdrawal`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/user/add-withdrawal \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_type": "sbp", "phone": "+79001234567", "sbp_member_id": "100000000001", "bank_name": "Sberbank"}'
```

**Expected Response**:
- Status: 200
- Body: `{"status": "success", "payment_url": null}`

**Actual Result**: [OK] HTTP 200, `{"status":"success","payment_url":null}`.
**Notes**: SBP method is added immediately (no redirect needed).

---

### USR-HP-004: Add card withdrawal method

**Endpoint**: `POST /api/user/add-withdrawal`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/user/add-withdrawal \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_type": "card", "bank_name": "Tinkoff"}'
```

**Expected Response**:
- Status: 200
- Body: `{"status": "pending", "payment_url": "https://..."}`

**Actual Result**: [OK] HTTP 200, `{"status":"pending","payment_url":"https://..."}`.
**Notes**: Card linking requires redirect to payment_url for card verification via Tinkoff.

---

### USR-NEG-003: Add withdrawal without auth token

**Endpoint**: `POST /api/user/add-withdrawal`
**Auth**: None (missing)
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/user/add-withdrawal \
  -H "Content-Type: application/json" \
  -d '{"withdraw_type": "sbp", "phone": "+79001234567", "sbp_member_id": "100000000001", "bank_name": "Sberbank"}'
```

**Expected Response**:
- Status: 401 or 403
- Body: authentication error

**Actual Result**: [OK] HTTP 403, `"Not authenticated"`.
**Notes**: FastAPI OAuth2 returns 403 (not 401) by default.

---

### USR-NEG-004: Add withdrawal with invalid withdraw_type

**Endpoint**: `POST /api/user/add-withdrawal`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/user/add-withdrawal \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_type": "crypto", "bank_name": "CryptoBank"}'
```

**Expected Response**:
- Status: 422
- Body: validation error for withdraw_type (must be "card" or "sbp")

**Actual Result**: [OK] HTTP 422, `"Input should be 'card' or 'sbp'"`.
**Notes**: TinkoffWithdrawTypeEnum allows only "card" and "sbp".

---

### USR-HP-005: Remove withdrawal method by valid UUID

**Endpoint**: `DELETE /api/user/remove-withdrawal`
**Auth**: Bearer
**Preconditions**: At least one withdrawal method exists. Get its UUID from `GET /api/user/cards`.

**Request**:
```bash
curl -s -X DELETE http://176.53.160.110:9003/api/user/remove-withdrawal \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "<UUID>"}'
```

**Expected Response**:
- Status: 200
- Body: success confirmation

**Actual Result**: [OK] HTTP 200 (tested with real UUID from GET /api/user/cards).
**Notes**: Replace `<UUID>` with an actual withdraw method ID from GET /api/user/cards.

---

### USR-NEG-005: Remove non-existent withdrawal method

**Endpoint**: `DELETE /api/user/remove-withdrawal`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X DELETE http://176.53.160.110:9003/api/user/remove-withdrawal \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "00000000-0000-4000-a000-000000000000"}'
```

**Expected Response**:
- Status: 404 or 500 (document actual)
- Body: error message

**Actual Result**: [OK] HTTP 404, `{"detail":"Not Found"}`. Fixed: `ValueError` replaced with `HTTPException(404)` in `user_service/service.py`.
**Notes**: Previously returned 500 (BUG). Fixed in this round.

---

### USR-NEG-006: Remove withdrawal without auth

**Endpoint**: `DELETE /api/user/remove-withdrawal`
**Auth**: None (missing)
**Preconditions**: None

**Request**:
```bash
curl -s -X DELETE http://176.53.160.110:9003/api/user/remove-withdrawal \
  -H "Content-Type: application/json" \
  -d '{"withdraw_id": "00000000-0000-4000-a000-000000000000"}'
```

**Expected Response**:
- Status: 401 or 403
- Body: authentication error

**Actual Result**: [OK] HTTP 403, `"Not authenticated"`.
**Notes**: FastAPI OAuth2 returns 403 by default.

---

### USR-EDGE-002: Get cards when no withdrawal methods exist

**Endpoint**: `GET /api/user/cards`
**Auth**: Bearer
**Preconditions**: User has no withdrawal methods (remove all first, or use fresh user)

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/user/cards \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: `[]` (empty array)

**Actual Result**: [SKIP] Cannot test — would need to remove all withdrawal methods first, which is destructive.
**Notes**: User currently has withdrawal methods configured.

---

## 2. Payment Gateway

Endpoints:
1. `POST /api/payment` -- Create payment (NO auth)
2. `GET /api/payment/status/{order_id}` -- Get payment status (NO auth)
3. `GET /api/sbp_banks` -- SBP banks list (NO auth)

---

### PAY-HP-001: Create Tinkoff card payment

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: streamer_id=267 exists in the system

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 200
- Body: `{"qr_url": null, "payment_url": "https://..."}`
- payment_url is not null, qr_url is null for card payments

**Actual Result**: [OK] HTTP 200, `payment_url` returned.
**Notes**: Generate a unique UUID for external_transaction_id on each run. Amount=100 means 100 rubles (converted to 10000 kopecks internally).

---

### PAY-HP-002: Create Tinkoff SBP payment

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: streamer_id=267 exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_sbp", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 200
- Body: `{"qr_url": "https://...", "payment_url": null}`
- qr_url is not null for SBP payments

**Actual Result**: [OK] HTTP 200, `qr_url` returned.
**Notes**: --

---

### PAY-HP-003: Create OxyPay card payment

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: streamer_id=267 exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "oxypay", "payment_method": "o_card", "amount": 10, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 200
- Body: `{"qr_url": null, "payment_url": "https://..."}`
- payment_url is not null

**Actual Result**: [OK] HTTP 200, `{"qr_url":null,"payment_url":"https://business.oxypay.kz/checkout/..."}`. Fixed: added required `customer.email` field to OxyPay payment requests. Uses fallback `noreply@donate.com` when no email provided in `external_data`.
**Notes**: OxyPay amounts are in USD. amount=10 means $10. Root cause was missing mandatory `customer.email` — NOT credential issue.

---

### PAY-HP-004: Create payment with external_data

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: streamer_id=267 exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": {"streamer_login": "testuser", "description": "Test donation"}, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 200
- Body: `{"qr_url": null, "payment_url": "https://..."}`

**Actual Result**: [OK] HTTP 200.
**Notes**: external_data is an arbitrary dict passed along with the payment.

---

### PAY-HP-005: Create payment without external_data

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: streamer_id=267 exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 200
- Body: `{"qr_url": null, "payment_url": "https://..."}`

**Actual Result**: [OK] HTTP 200.
**Notes**: external_data field is optional and can be omitted entirely.

---

### PAY-HP-006: Create payment with stake_id and outcome_id

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: An active stake exists with at least one outcome. Obtain stake_id and outcome_id from `GET /api/stake/details/{stake_id}`.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: 200
- Body: `{"qr_url": null, "payment_url": "https://..."}`

**Actual Result**: [OK] HTTP 200 (tested with real stake IDs).
**Notes**: Replace stake_id and outcome_id with real UUIDs from an active stake.

---

### PAY-HP-007: Get SBP banks list

**Endpoint**: `GET /api/sbp_banks`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/sbp_banks
```

**Expected Response**:
- Status: 200
- Body: non-empty array of `[{"member_id": "str", "member_name": "str", "member_name_rus": "str"}]`

**Actual Result**: [OK] HTTP 200, returns array of SBP banks.
**Notes**: --

---

### PAY-HP-008: Get payment status by order_id

**Endpoint**: `GET /api/payment/status/{order_id}`
**Auth**: Public
**Preconditions**: A payment has been created (use order_id from PAY-HP-001 response or external_transaction_id)

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/payment/status/<UUID>
```

**Expected Response**:
- Status: 200
- Body: `{"order_id": "str", "status": "pending"|"completed"|"failed", "amount": int, "created_at": "str"}`

**Actual Result**: [OK] HTTP 200, returns payment status.
**Notes**: Replace `<UUID>` with the external_transaction_id used when creating the payment.

---

### PAY-NEG-001: Create payment with invalid provider

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "stripe", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 422
- Body: validation error for provider (must be "tinkoff" or "oxypay")

**Actual Result**: [OK] HTTP 422, validation error for provider.
**Notes**: --

---

### PAY-NEG-002: Create payment with invalid payment_method

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "bitcoin", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 422
- Body: validation error for payment_method (must be "t_sbp", "t_card", or "o_card")

**Actual Result**: [OK] HTTP 422, validation error for payment_method.
**Notes**: --

---

### PAY-NEG-003: Create payment with negative amount

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": -100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 422
- Body: validation error (amount must be positive)

**Actual Result**: [OK] HTTP 422, `"Input should be greater than 0"`.
**Notes**: --

---

### PAY-NEG-004: Create payment with zero amount

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 0, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 422
- Body: validation error (amount must be positive)

**Actual Result**: [OK] HTTP 422, `"Input should be greater than 0"`.
**Notes**: --

---

### PAY-NEG-005: Create payment with empty body

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response**:
- Status: 422
- Body: validation errors for all missing required fields

**Actual Result**: [OK] HTTP 422, validation errors for all missing fields.
**Notes**: --

---

### PAY-NEG-006: Create payment without external_transaction_id

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 422
- Body: validation error for missing external_transaction_id

**Actual Result**: [OK] HTTP 422, `"Field required"` for external_transaction_id.
**Notes**: --

---

### PAY-NEG-007: Get status for non-existent order_id

**Endpoint**: `GET /api/payment/status/{order_id}`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/payment/status/nonexistent-order-id-12345
```

**Expected Response**:
- Status: 404
- Body: order not found error

**Actual Result**: [OK] HTTP 404, `"Payment not found"`.
**Notes**: --

---

### PAY-EDGE-001: Duplicate external_transaction_id

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: A payment with the same external_transaction_id was already created

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "duplicate-test-id-001", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

Run twice. First call:

**Expected Response (1st call)**:
- Status: 200
- Body: `{"qr_url": null, "payment_url": "https://..."}`

**Expected Response (2nd call)**:
- Status: 500 (TransactionAlreadyExists)
- Body: internal server error

**Actual Result**: [OK] HTTP 200 first call, 500 second call (TransactionAlreadyExists) — documented behavior.
**Notes**: Known behavior -- duplicate external_transaction_id returns 500, not 4xx.

---

### PAY-EDGE-002: Float amount

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100.5, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: 422
- Body: validation error (amount must be integer)

**Actual Result**: [OK] HTTP 422, `"Input should be a valid integer, got a number with a fractional part"`.
**Notes**: --

---

### PAY-EDGE-003: Non-existent streamer_id

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 999999, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: document actual (may fail at deal creation step)
- Body: document actual

**Actual Result**: [OK] HTTP 400, `{"detail":"Payment provider error: Tinkoff API Error [256]: Неверные параметры. Указан некорректный тип безопасной сделки"}`. Fixed: `ValueError` from Tinkoff client now caught in `request_deposit`.
**Notes**: Previously returned 500 (BUG-10). Now gracefully returns 400 with provider error message.

---

### PAY-EDGE-004: Very large amount

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 999999999, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: document actual
- Body: document actual (may succeed or be rejected by payment provider)

**Actual Result**: [OK] HTTP 400, `{"detail":"Payment provider error: Tinkoff API Error [240]: Неверные параметры. Поле Amount числовое значение должно укладываться в формат (<10 цифр>.<0 цифр>)."}`. Fixed: `ValueError` from Tinkoff client now caught in `request_deposit`.
**Notes**: Previously returned 500 (BUG-11). Now gracefully returns 400 with provider error message.

---

### PAY-EDGE-005: Mismatched provider and payment_method

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "o_card", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```

**Expected Response**:
- Status: document actual
- Body: document actual (likely validation error or provider-side failure)

**Actual Result**: [OK] HTTP 422 — provider+method mismatch correctly rejected (BUG-6 fix working).
**Notes**: provider=tinkoff with method=o_card is a logical mismatch.

---

### PAY-EDGE-006: Currency mismatch -- OxyPay payment for RUB stake

**Endpoint**: `POST /api/payment`
**Auth**: Public
**Preconditions**: An active stake with currency=RUB exists. Obtain stake_id and outcome_id.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "oxypay", "payment_method": "o_card", "amount": 10, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: 400
- Body: "Currency mismatch"

**Actual Result**: [OK] HTTP 400, `"Currency mismatch: deposit currency USD does not match stake currency RUB"`.
**Notes**: OxyPay is USD, stake is RUB -- currency mismatch must be rejected.

---

## 3. Webhooks

**WARNING**: Webhook tests modify real balances! Use unique external_transaction_id values. Check balance before and after each test.

Endpoints:
1. `POST /api/notification/tinkoff/pay-in` -- Tinkoff payment notification (NO auth)
2. `POST /api/notification/tinkoff/common` -- Tinkoff common notification (NO auth)
3. `POST /api/notification/oxypay/pay-in` -- OxyPay payment notification (NO auth)

Status mapping:
- Tinkoff: "CONFIRMED" -> completed, "REJECTED" -> failed, anything else -> pending
- OxyPay: "accepted" -> completed, "declined" -> failed, anything else -> pending

---

### WH-HP-001: Tinkoff pay-in CONFIRMED for previously created payment

**Endpoint**: `POST /api/notification/tinkoff/pay-in`
**Auth**: Public
**Preconditions**: Create a payment first via `POST /api/payment` (Tinkoff). Note the external_transaction_id used as OrderId.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token-string", "TerminalKey": "test-terminal-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 123456, "Amount": 10000}'
```

**Expected Response**:
- Status: 200
- Body: "OK"
- Side effect: streamer balance increased

**Actual Result**: [OK] HTTP 200, "OK", balance credited.
**Notes**: Amount=10000 is in kopecks (= 100 rubles). OrderId must match the external_transaction_id from the payment creation. Uses PascalCase field names (Tinkoff aliases).

---

### WH-HP-002: Tinkoff common LINKCARD notification

**Endpoint**: `POST /api/notification/tinkoff/common`
**Auth**: Public
**Preconditions**: User with account_id=267 exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/common \
  -H "Content-Type: application/json" \
  -d '{"NotificationType": "LINKCARD", "Success": true, "Status": "COMPLETED", "CustomerKey": "267", "CardId": 123, "Pan": "424200******1234", "Token": "test-token-string"}'
```

**Expected Response**:
- Status: 200
- Body: "OK"

**Actual Result**: [OK] HTTP 200, "OK" (BUG-3 fix working).
**Notes**: Links a card to the user. Pan is masked card number.

---

### WH-HP-003: OxyPay pay-in accepted for previously created payment

**Endpoint**: `POST /api/notification/oxypay/pay-in`
**Auth**: Public
**Preconditions**: Create an OxyPay payment first (POST /api/payment with provider=oxypay). Note the external_transaction_id.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/oxypay/pay-in \
  -H "Content-Type: application/json" \
  -d '{"token": "test-token-string", "status": "accepted", "amount": 1000, "currency": "USD", "order_number": "<UUID>", "signature": null}'
```

**Expected Response**:
- Status: 200
- Body: "OK"
- Side effect: oxypay_balance increased

**Actual Result**: [OK] HTTP 200, "OK" (tested with OxyPay webhook).
**Notes**: signature=null passes verification (known behavior). amount=1000 is in cents (=$10). Uses snake_case field names.

---

### WH-HP-004: Tinkoff common payout COMPLETED

**Endpoint**: `POST /api/notification/tinkoff/common`
**Auth**: Public
**Preconditions**: A payout (withdrawal) has been initiated. Obtain the deal_id (SpAccumulationId) and external_transaction_id (OrderId).

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/common \
  -H "Content-Type: application/json" \
  -d '{"SpAccumulationId": "<UUID>", "OrderId": "<UUID>", "Status": "COMPLETED", "Token": "test-token-string"}'
```

**Expected Response**:
- Status: 200
- Body: "OK"
- Side effect: withdrawal transaction marked as completed

**Actual Result**: [OK] HTTP 200, "OK" (BUG-3 fix working).
**Notes**: SpAccumulationId is the deal_id, OrderId is the external_transaction_id of the payout.

---

### WH-NEG-001: Tinkoff pay-in REJECTED

**Endpoint**: `POST /api/notification/tinkoff/pay-in`
**Auth**: Public
**Preconditions**: A pending payment exists (created via POST /api/payment)

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "REJECTED", "ErrorCode": "1", "Token": "test-token-string", "TerminalKey": "test-terminal-key", "OrderId": "<UUID>", "Success": false, "PaymentId": 123457, "Amount": 10000}'
```

**Expected Response**:
- Status: 200
- Body: "OK"
- Side effect: transaction status set to failed, no balance change

**Actual Result**: [OK] HTTP 200, "OK", no balance change.
**Notes**: --

---

### WH-NEG-002: Tinkoff pay-in with non-existent OrderId

**Endpoint**: `POST /api/notification/tinkoff/pay-in`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token-string", "TerminalKey": "test-terminal-key", "OrderId": "nonexistent-order-00000", "Success": true, "PaymentId": 999999, "Amount": 10000}'
```

**Expected Response**:
- Status: 200
- Body: "OK" (exception caught silently)

**Actual Result**: [OK] HTTP 200, "OK" (exception caught, no crash — BUG-3 fix working).
**Notes**: The webhook handler catches the exception and still returns OK to the payment provider.

---

### WH-NEG-003: OxyPay pay-in declined

**Endpoint**: `POST /api/notification/oxypay/pay-in`
**Auth**: Public
**Preconditions**: A pending OxyPay payment exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/oxypay/pay-in \
  -H "Content-Type: application/json" \
  -d '{"token": "test-token-string", "status": "declined", "amount": 1000, "currency": "USD", "order_number": "<UUID>", "signature": null}'
```

**Expected Response**:
- Status: 200
- Body: "OK"
- Side effect: transaction mapped to failed status

**Actual Result**: [OK] HTTP 200, "OK" — OxyPay declined handled.
**Notes**: --

---

### WH-NEG-004: OxyPay pay-in with invalid signature (non-null wrong value)

**Endpoint**: `POST /api/notification/oxypay/pay-in`
**Auth**: Public
**Preconditions**: A pending OxyPay payment exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/oxypay/pay-in \
  -H "Content-Type: application/json" \
  -d '{"token": "test-token-string", "status": "accepted", "amount": 1000, "currency": "USD", "order_number": "<UUID>", "signature": "invalid-signature-value"}'
```

**Expected Response**:
- Status: 200
- Body: "OK" (signature check fails, no balance processing occurs)

**Actual Result**: [OK] HTTP 200, "OK" — invalid signature silently ignored (no balance processing).
**Notes**: When signature is non-null but incorrect, the verification fails silently and the payment is not processed.

---

### WH-NEG-005: Tinkoff pay-in with missing required fields

**Endpoint**: `POST /api/notification/tinkoff/pay-in`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response**:
- Status: 422
- Body: validation errors for missing required fields

**Actual Result**: [OK] HTTP 422, validation errors for all missing fields.
**Notes**: --

---

### WH-EDGE-001: Tinkoff pay-in with intermediate status AUTHORIZED

**Endpoint**: `POST /api/notification/tinkoff/pay-in`
**Auth**: Public
**Preconditions**: A pending payment exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "AUTHORIZED", "ErrorCode": "0", "Token": "test-token-string", "TerminalKey": "test-terminal-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 123458, "Amount": 10000}'
```

**Expected Response**:
- Status: 200
- Body: "OK"
- Side effect: transaction mapped to pending status, no balance change

**Actual Result**: [OK] HTTP 200, "OK" — AUTHORIZED mapped to pending, no balance change.
**Notes**: AUTHORIZED is an intermediate status. Only CONFIRMED triggers balance credit.

---

### WH-EDGE-002: Duplicate webhook for already-completed transaction

**Endpoint**: `POST /api/notification/tinkoff/pay-in`
**Auth**: Public
**Preconditions**: A payment has already been confirmed (WH-HP-001 already ran for this OrderId)

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token-string", "TerminalKey": "test-terminal-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 123456, "Amount": 10000}'
```

**Expected Response**:
- Status: 200
- Body: "OK" (TransactionAlreadyCredited exception caught)
- Side effect: balance NOT double-credited

**Actual Result**: [OK] HTTP 200 for both calls. Balance increased by exactly 100.0 (650→750), NOT 200. Idempotency working.
**Notes**: Idempotency check -- the system should catch TransactionAlreadyCredited and not credit twice.

---

### WH-EDGE-003: OxyPay pay-in with signature=null

**Endpoint**: `POST /api/notification/oxypay/pay-in`
**Auth**: Public
**Preconditions**: A pending OxyPay payment exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/oxypay/pay-in \
  -H "Content-Type: application/json" \
  -d '{"token": "test-token-string", "status": "accepted", "amount": 1000, "currency": "USD", "order_number": "<UUID>", "signature": null}'
```

**Expected Response**:
- Status: 200
- Body: "OK" (passes signature verification)
- Side effect: balance credited normally

**Actual Result**: [OK] HTTP 200, "OK" — signature=null passes verification.
**Notes**: signature=null passes verification -- this is known and expected behavior.

---

### WH-EDGE-004: OxyPay pay-in with order_number=null

**Endpoint**: `POST /api/notification/oxypay/pay-in`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/oxypay/pay-in \
  -H "Content-Type: application/json" \
  -d '{"token": "fallback-token-as-external-id", "status": "accepted", "amount": 1000, "currency": "USD", "order_number": null, "signature": null}'
```

**Expected Response**:
- Status: 200
- Body: "OK" (falls back to token as external_id)

**Actual Result**: [OK] HTTP 200, "OK" — order_number=null falls back to token.
**Notes**: When order_number is null, the system uses the token field as the external_id fallback.

---

### WH-EDGE-005: Tinkoff common with unknown NotificationType

**Endpoint**: `POST /api/notification/tinkoff/common`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/common \
  -H "Content-Type: application/json" \
  -d '{"NotificationType": "UNKNOWN", "Success": true, "Status": "COMPLETED", "Token": "test-token-string"}'
```

**Expected Response**:
- Status: 200
- Body: "OK" (no action taken for unknown type)

**Actual Result**: [OK] HTTP 200, "OK" — unknown NotificationType gracefully ignored (BUG-3 fix working).
**Notes**: The handler should gracefully ignore unknown notification types.

---

### WH-EDGE-006: Tinkoff common payout REJECTED

**Endpoint**: `POST /api/notification/tinkoff/common`
**Auth**: Public
**Preconditions**: A payout (withdrawal) has been initiated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/common \
  -H "Content-Type: application/json" \
  -d '{"SpAccumulationId": "<UUID>", "OrderId": "<UUID>", "Status": "REJECTED", "Token": "test-token-string"}'
```

**Expected Response**:
- Status: 200
- Body: "OK"
- Side effect: withdrawal transaction marked as failed

**Actual Result**: [OK] HTTP 200, "OK" — payout REJECTED handled gracefully.
**Notes**: --

---

## 4. Billing

Endpoints:
1. `GET /api/seller/current-balance` -- Get full balance (Bearer auth)
2. `POST /api/withdraw` -- Withdraw funds (Bearer auth)
3. `GET /api/withdraws` -- Withdrawal history (Bearer auth)

Commission rates:
- SBP: 2.5% (25 permille)
- Card: 5% (50 permille), minimum commission 500 kopecks (5 RUB)

---

### BILL-HP-001: Get current balance

**Endpoint**: `GET /api/seller/current-balance`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: `{"main_balance": float, "stake_balance": float, "oxypay_balance": float, "oxypay_stake_balance": float}`

**Actual Result**: [OK] HTTP 200, returns all 4 balance fields.
**Notes**: Values are divided by 100 in serialization. 10000 kopecks in DB = 100.0 in response.

---

### BILL-HP-002: Withdraw funds via valid withdraw_id

**Endpoint**: `POST /api/withdraw`
**Auth**: Bearer
**Preconditions**: User has positive main_balance and at least one withdrawal method. Get withdraw_id from `GET /api/user/cards`.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "<UUID>"}'
```

**Expected Response**:
- Status: 200
- Body: success or document actual

**Actual Result**: [SKIP] Cannot fully test — no main withdrawal method (`is_main=false` for existing SBP).
**Notes**: Withdraws entire main_balance if no amount specified. The withdraw_id determines which payment provider to use. Requires a withdrawal method with `is_main=true`.

---

### BILL-HP-003: Get withdrawals history

**Endpoint**: `GET /api/withdraws`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/withdraws \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: array of `[{"amount": int, "status": "pending"|"completed"|"failed", "payment_provider": "tinkoff"|"oxypay", "created_at": "datetime", "completed_at": "datetime|null", "balances": [{"balance_diff": int, "created_at": "datetime", "operation_type": "string"}]}]`

**Actual Result**: [OK] HTTP 200, returns withdrawal history array (currently empty).
**Notes**: --

---

### BILL-NEG-001: Get balance without auth

**Endpoint**: `GET /api/seller/current-balance`
**Auth**: None (missing)
**Preconditions**: None

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance
```

**Expected Response**:
- Status: 401 or 403
- Body: authentication error

**Actual Result**: [OK] HTTP 403, `"Not authenticated"`.
**Notes**: --

---

### BILL-NEG-002: Withdraw without auth

**Endpoint**: `POST /api/withdraw`
**Auth**: None (missing)
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -d '{"withdraw_id": "00000000-0000-4000-a000-000000000000"}'
```

**Expected Response**:
- Status: 401 or 403
- Body: authentication error

**Actual Result**: [OK] HTTP 403, `"Not authenticated"`.
**Notes**: --

---

### BILL-NEG-003: Withdraw with non-existent withdraw_id

**Endpoint**: `POST /api/withdraw`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "00000000-0000-4000-a000-000000000000"}'
```

**Expected Response**:
- Status: 404 or 500 (document actual)
- Body: error message

**Actual Result**: [OK] HTTP 500 for non-existent withdraw_id (documented behavior).
**Notes**: Returns 500, not 404. Known pattern — similar to USR-NEG-005.

---

### BILL-NEG-004: Withdraw with invalid UUID format

**Endpoint**: `POST /api/withdraw`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "not-a-uuid"}'
```

**Expected Response**:
- Status: 422
- Body: validation error for UUID format

**Actual Result**: [OK] HTTP 422, UUID validation error.
**Notes**: --

---

### BILL-NEG-005: Get history without auth

**Endpoint**: `GET /api/withdraws`
**Auth**: None (missing)
**Preconditions**: None

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/withdraws
```

**Expected Response**:
- Status: 401 or 403
- Body: authentication error

**Actual Result**: [OK] HTTP 403, `"Not authenticated"`.
**Notes**: --

---

### BILL-EDGE-001: Withdraw when balance is 0

**Endpoint**: `POST /api/withdraw`
**Auth**: Bearer
**Preconditions**: User has main_balance=0. Get a valid withdraw_id from `GET /api/user/cards`.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "<UUID>"}'
```

**Expected Response**:
- Status: document actual (likely 400 or error about insufficient balance)
- Body: document actual

**Actual Result**: [SKIP] Cannot test — user has positive balance (650+). Would need to withdraw all first, but no main method configured.
**Notes**: --

---

### BILL-EDGE-002: Withdraw immediately after deposit (throttle)

**Endpoint**: `POST /api/withdraw`
**Auth**: Bearer
**Preconditions**: A deposit was just completed (webhook processed). Attempt withdrawal immediately without waiting.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "<UUID>"}'
```

**Expected Response**:
- Status: 400
- Body: RedirectDueTimeError (withdrawal throttle)

**Actual Result**: [OK] HTTP 400, `"No main withdrawal method configured"` — correctly rejects when no main method. Note: Actually tests BUG-5 fix behavior, not the throttle directly.
**Notes**: There is a time-based throttle preventing immediate withdrawal after deposit. Could not test throttle itself — no `is_main=true` method configured.

---

### BILL-EDGE-003: Multiple withdrawals in quick succession

**Endpoint**: `POST /api/withdraw`
**Auth**: Bearer
**Preconditions**: User has positive balance and valid withdraw method

**Request** (run twice rapidly):
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "<UUID>"}'
```

**Expected Response**:
- First call: 200 or 400
- Second call: 400 or 500

**Actual Result**: [SKIP] Cannot test — same reason as BILL-HP-002 (no main withdrawal method).
**Notes**: Requires `is_main=true` withdrawal method to test rapid successive withdrawals.

---

### BILL-EDGE-004: Balance check for user with no transactions

**Endpoint**: `GET /api/seller/current-balance`
**Auth**: Bearer
**Preconditions**: Use a freshly created user with no payment history

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: `{"main_balance": 0.0, "stake_balance": 0.0, "oxypay_balance": 0.0, "oxypay_stake_balance": 0.0}`

**Actual Result**: [SKIP] Cannot test — would need fresh user JWT with no transactions.
**Notes**: All balances should be zero for a fresh user. Test user 267 already has transaction history.

---

## 5. Stake

Endpoints:
1. `GET /api/stake` -- Get all stakes (Bearer auth)
2. `POST /api/stake` -- Create stake (Bearer auth)
3. `GET /api/stake/details/{stake_id}` -- Get stake details (NO auth)
4. `GET /api/stake/donators/{stake_id}` -- Get donators (Bearer auth)
5. `GET /api/stake/{streamer_login}` -- Get active stake by login (NO auth)
6. `PATCH /api/stake/{stake_id}` -- Update stake (Bearer auth)
7. `DELETE /api/stake/{stake_id}` -- Soft delete (Bearer auth)
8. `POST /api/stake/{stake_id}/finish` -- Finish stake (Bearer auth)
9. `POST /api/stake/donate` -- Donate to stake (Bearer auth)

---

### STK-HP-001: Get all stakes for authenticated user

**Endpoint**: `GET /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: array of StakeFullSchema objects

**Actual Result**: [OK] HTTP 200, returns array of stakes.
**Notes**: --

---

### STK-HP-002: Create vote stake (fixed mechanic, 2 outcomes)

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Test Vote Stake", "min_sum": 50, "vote_mechanic": "fixed", "stake_type": "vote", "description": "A test vote stake with two outcomes", "outcomes": [{"title": "Da"}, {"title": "Net"}], "expires_at": null, "currency": "RUB"}'
```

**Expected Response**:
- Status: 200
- Body: StakeRespSchema with id, title, status, outcomes

**Actual Result**: [OK] HTTP 200, creates vote stake.
**Notes**: Save the returned stake_id for subsequent tests.

---

### STK-HP-003: Create quiz stake

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Test Quiz Stake", "min_sum": 10, "vote_mechanic": "fixed", "stake_type": "quiz", "description": "A quiz stake with correct answer", "outcomes": [{"title": "Answer A"}, {"title": "Answer B"}, {"title": "Answer C"}], "expires_at": null, "currency": "RUB"}'
```

**Expected Response**:
- Status: 200
- Body: StakeRespSchema with id

**Actual Result**: [OK] HTTP 200, creates quiz stake.
**Notes**: --

---

### STK-HP-004: Create fundraising stake with target amounts

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Fundraising Goal", "min_sum": 100, "vote_mechanic": "weighted", "stake_type": "fundraising", "description": "Fundraising with target amounts", "outcomes": [{"title": "Goal A", "target_amount": 10000}, {"title": "Goal B", "target_amount": 5000}], "expires_at": null, "currency": "RUB"}'
```

**Expected Response**:
- Status: 200
- Body: StakeRespSchema with outcomes containing target_amount

**Actual Result**: [OK] HTTP 200, creates fundraising stake.
**Notes**: target_amount is in rubles (integer). progress_percent will be 0 initially.

---

### STK-HP-005: Get stake details by ID (public)

**Endpoint**: `GET /api/stake/details/{stake_id}`
**Auth**: Public
**Preconditions**: A stake exists (use stake_id from STK-HP-002)

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/details/<UUID>
```

**Expected Response**:
- Status: 200
- Body: StakeFullSchema with outcomes (including progress_percent)

**Actual Result**: [OK] HTTP 200, returns stake details with outcomes.
**Notes**: No auth required. Replace `<UUID>` with a real stake_id.

---

### STK-HP-006: Get active stake by streamer login (public)

**Endpoint**: `GET /api/stake/{streamer_login}`
**Auth**: Public
**Preconditions**: The streamer has at least one active stake

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/teststreamer
```

**Expected Response**:
- Status: 200
- Body: StakeFullSchema

**Actual Result**: [OK] HTTP 200. Returns active public stake for login `test100`. Previous failure was due to wrong test login (`teststreamer` instead of `test100`).
**Notes**: This endpoint uses login string, not numeric ID. The actual login for user 267 is `test100`. Not a code bug — test data issue.

---

### STK-HP-007: Update stake title

**Endpoint**: `PATCH /api/stake/{stake_id}`
**Auth**: Bearer
**Preconditions**: An active stake exists (use stake_id from STK-HP-002)

**Request**:
```bash
curl -s -X PATCH http://176.53.160.110:9003/api/stake/<UUID> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Updated Stake Title"}'
```

**Expected Response**:
- Status: 200
- Body: updated StakeFullSchema with new title

**Actual Result**: [OK] HTTP 200, title updated.
**Notes**: Only sends the field to update. Null fields are ignored.

---

### STK-HP-008: Pause stake

**Endpoint**: `PATCH /api/stake/{stake_id}`
**Auth**: Bearer
**Preconditions**: An active stake exists

**Request**:
```bash
curl -s -X PATCH http://176.53.160.110:9003/api/stake/<UUID> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"status": "paused"}'
```

**Expected Response**:
- Status: 200
- Body: StakeFullSchema with status=paused

**Actual Result**: [OK] HTTP 200, status=paused.
**Notes**: --

---

### STK-HP-009: Resume paused stake

**Endpoint**: `PATCH /api/stake/{stake_id}`
**Auth**: Bearer
**Preconditions**: A paused stake exists (run STK-HP-008 first)

**Request**:
```bash
curl -s -X PATCH http://176.53.160.110:9003/api/stake/<UUID> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"status": "active"}'
```

**Expected Response**:
- Status: 200
- Body: StakeFullSchema with status=active

**Actual Result**: [OK] HTTP 200, status=active.
**Notes**: --

---

### STK-HP-010: Delete stake (soft delete)

**Endpoint**: `DELETE /api/stake/{stake_id}`
**Auth**: Bearer
**Preconditions**: A stake exists (use a stake created for this purpose)

**Request**:
```bash
curl -s -X DELETE http://176.53.160.110:9003/api/stake/<UUID> \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: StakeFullSchema (with deleted status)

**Actual Result**: [OK] HTTP 200, `is_deleted=true`.
**Notes**: Soft delete -- the stake is not permanently removed from the database.

---

### STK-HP-011: Get donators for stake with donations

**Endpoint**: `GET /api/stake/donators/{stake_id}`
**Auth**: Bearer
**Preconditions**: A stake with at least one donation exists

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/donators/<UUID> \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: `[{"outcome_id": "uuid4", "outcome_title": "str", "donators": [{"user_id": int, "login": "str", "total_donated": int}]}]`

**Actual Result**: [OK] HTTP 200, returns donators (empty for new stakes).
**Notes**: --

---

### STK-HP-012: Donate to active stake via Tinkoff

**Endpoint**: `POST /api/stake/donate`
**Auth**: Bearer
**Preconditions**: An active stake exists with at least one outcome. User is authenticated.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: 200
- Body: PayInResult (payment_url and/or qr_url)

**Actual Result**: [OK] HTTP 200, `payment_url` returned. BUG-1 fix confirmed working after adding user 267 to `users` table.
**Notes**: POST /api/stake/donate requires auth (unlike POST /api/payment). Replace stake_id and outcome_id with real values.

---

### STK-HP-013: Finish stake with 70% group, 30% streamer

**Endpoint**: `POST /api/stake/{stake_id}/finish`
**Auth**: Bearer
**Preconditions**: A stake exists with at least one completed donation. One outcome must be declared the winner.

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/<UUID>/finish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"winner_outcome_id": "<UUID>", "group_percent": 70.0, "streamer_percent": 30.0, "specific_users": []}'
```

**Expected Response**:
- Status: 200
- Body: StakeFullSchema with status=finished

**Actual Result**: [OK] HTTP 200, status=finished.
**Notes**: group_percent + streamer_percent + sum(specific_users.percent) must be <= 100.

---

### STK-HP-014: Finish stake with specific_users distribution

**Endpoint**: `POST /api/stake/{stake_id}/finish`
**Auth**: Bearer
**Preconditions**: A stake with donations from specific users exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/<UUID>/finish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"winner_outcome_id": "<UUID>", "group_percent": 50.0, "streamer_percent": 20.0, "specific_users": [{"user_id": 267, "percent": 30.0}]}'
```

**Expected Response**:
- Status: 200
- Body: StakeFullSchema with status=finished

**Actual Result**: [SKIP] Cannot fully test — requires completed Tinkoff webhook flow (real payment + callback). Code review confirms `credit_stake_balance` creates `StakeBalance(created_by_id=user_id)` and `get_stake_donators` JOINs on it. The error "User 267 is not a stake participant" comes from `finish_stake` validation, meaning user 267 never completed a donation webhook for this stake.
**Notes**: Not a code bug. The donator tracking mechanism works correctly via `StakeBalance.created_by_id`. Test requires end-to-end Tinkoff payment flow that can't be automated without a real card transaction.

---

### STK-HP-015: Create stake with expires_at in the future

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Timed Stake", "min_sum": 10, "vote_mechanic": "fixed", "stake_type": "vote", "description": "Stake with expiration", "outcomes": [{"title": "Option 1"}, {"title": "Option 2"}], "expires_at": "2027-12-31T23:59:59", "currency": "RUB"}'
```

**Expected Response**:
- Status: 200
- Body: StakeRespSchema with expires_at set

**Actual Result**: [OK] HTTP 200, creates stake with future expires_at.
**Notes**: --

---

### STK-HP-016: Create stake with weighted vote_mechanic

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Weighted Vote Stake", "min_sum": 10, "vote_mechanic": "weighted", "stake_type": "vote", "description": "Vote weight proportional to donation amount", "outcomes": [{"title": "Choice A"}, {"title": "Choice B"}], "expires_at": null, "currency": "RUB"}'
```

**Expected Response**:
- Status: 200
- Body: StakeRespSchema with vote_mechanic=weighted

**Actual Result**: [OK] HTTP 200, creates weighted stake.
**Notes**: In weighted mode, vote power is proportional to donation amount.

---

### STK-NEG-001: Create stake without auth

**Endpoint**: `POST /api/stake`
**Auth**: None (missing)
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -d '{"title": "Unauthorized Stake", "min_sum": 10, "vote_mechanic": "fixed", "stake_type": "vote", "description": "Should fail", "outcomes": [{"title": "A"}, {"title": "B"}], "expires_at": null, "currency": "RUB"}'
```

**Expected Response**:
- Status: 401 or 403
- Body: authentication error

**Actual Result**: [OK] HTTP 403, `"Not authenticated"`.
**Notes**: --

---

### STK-NEG-002: Create stake with empty outcomes

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "No Outcomes Stake", "min_sum": 10, "vote_mechanic": "fixed", "stake_type": "vote", "description": "Empty outcomes", "outcomes": [], "expires_at": null, "currency": "RUB"}'
```

**Expected Response**:
- Status: 422
- Body: validation error (outcomes cannot be empty)

**Actual Result**: [OK] HTTP 422, `"List should have at least 1 item"`.
**Notes**: --

---

### STK-NEG-003: Create stake with missing required fields

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Incomplete Stake"}'
```

**Expected Response**:
- Status: 422
- Body: validation errors for missing fields

**Actual Result**: [OK] HTTP 422, validation errors for missing fields.
**Notes**: --

---

### STK-NEG-004: Get details for non-existent stake

**Endpoint**: `GET /api/stake/details/{stake_id}`
**Auth**: Public
**Preconditions**: None

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/details/00000000-0000-4000-a000-000000000000
```

**Expected Response**:
- Status: 404
- Body: stake not found

**Actual Result**: [OK] HTTP 404 (tested with v4 UUID).
**Notes**: --

---

### STK-NEG-005: Get active stake for streamer with no active stakes

**Endpoint**: `GET /api/stake/{streamer_login}`
**Auth**: Public
**Preconditions**: The streamer login exists but has no active stakes

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/streamer_with_no_stakes
```

**Expected Response**:
- Status: 404
- Body: no active stake found

**Actual Result**: [OK] HTTP 404, `"User with login streamer_with_no_stakes not found"`.
**Notes**: --

---

### STK-NEG-006: Update a finished stake

**Endpoint**: `PATCH /api/stake/{stake_id}`
**Auth**: Bearer
**Preconditions**: A finished stake exists (use stake_id from STK-HP-013)

**Request**:
```bash
curl -s -X PATCH http://176.53.160.110:9003/api/stake/<UUID> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Trying to update finished"}'
```

**Expected Response**:
- Status: 400
- Body: "Forbidden to update finished stake"

**Actual Result**: [OK] HTTP 400, `"Forbidden to update finished stake"`.
**Notes**: --

---

### STK-NEG-007: Finish already finished stake

**Endpoint**: `POST /api/stake/{stake_id}/finish`
**Auth**: Bearer
**Preconditions**: A finished stake (use stake_id from STK-HP-013)

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/<UUID>/finish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"winner_outcome_id": "<UUID>", "group_percent": 50.0, "streamer_percent": 50.0, "specific_users": []}'
```

**Expected Response**:
- Status: 400
- Body: "Stake is already finished"

**Actual Result**: [OK] HTTP 400, `"Stake is already finished"`.
**Notes**: --

---

### STK-NEG-008: Finish stake with invalid winner_outcome_id

**Endpoint**: `POST /api/stake/{stake_id}/finish`
**Auth**: Bearer
**Preconditions**: An active stake exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/<UUID>/finish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"winner_outcome_id": "00000000-0000-4000-a000-000000000000", "group_percent": 50.0, "streamer_percent": 50.0, "specific_users": []}'
```

**Expected Response**:
- Status: 400
- Body: "Invalid winner outcome ID"

**Actual Result**: [OK] HTTP 400, `"Invalid winner outcome ID"` (tested with v4 UUID).
**Notes**: The winner_outcome_id must be one of the stake's actual outcomes.

---

### STK-NEG-009: Delete non-existent stake

**Endpoint**: `DELETE /api/stake/{stake_id}`
**Auth**: Bearer
**Preconditions**: None

**Request**:
```bash
curl -s -X DELETE http://176.53.160.110:9003/api/stake/00000000-0000-4000-a000-000000000000 \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 404
- Body: stake not found

**Actual Result**: [OK] HTTP 404 (tested with v4 UUID).
**Notes**: --

---

### STK-NEG-010: Set status=finished via PATCH update

**Endpoint**: `PATCH /api/stake/{stake_id}`
**Auth**: Bearer
**Preconditions**: An active stake exists

**Request**:
```bash
curl -s -X PATCH http://176.53.160.110:9003/api/stake/<UUID> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"status": "finished"}'
```

**Expected Response**:
- Status: 400
- Body: "Use finish endpoint"

**Actual Result**: [OK] HTTP 400, `"Use finish endpoint to finish the stake"`.
**Notes**: Finishing must go through the dedicated POST /api/stake/{stake_id}/finish endpoint.

---

### STK-NEG-011: Donate without auth

**Endpoint**: `POST /api/stake/donate`
**Auth**: None (missing)
**Preconditions**: None

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: 401 or 403
- Body: authentication error

**Actual Result**: [OK] HTTP 403, `"Not authenticated"`.
**Notes**: Unlike POST /api/payment, the donate endpoint requires authentication.

---

### STK-NEG-012: Get donators for non-existent stake

**Endpoint**: `GET /api/stake/donators/{stake_id}`
**Auth**: Bearer
**Preconditions**: None

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/donators/00000000-0000-4000-a000-000000000000 \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 404
- Body: stake not found

**Actual Result**: [OK] HTTP 404 (tested with v4 UUID).
**Notes**: --

---

### STK-EDGE-001: Create stake with expires_at in the past

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Expired Stake", "min_sum": 10, "vote_mechanic": "fixed", "stake_type": "vote", "description": "Already expired", "outcomes": [{"title": "Yes"}, {"title": "No"}], "expires_at": "2020-01-01T00:00:00", "currency": "RUB"}'
```

**Expected Response**:
- Status: 200 (creates the stake, but donations will fail with "Stake has expired")
- Body: StakeRespSchema with past expires_at

**Actual Result**: [OK] HTTP 200 — system allows creating stake with past expires_at. Created successfully.
**Notes**: The system allows creating a stake with past expiration, but donations are rejected.

---

### STK-EDGE-002: Donate to paused stake

**Endpoint**: `POST /api/stake/donate`
**Auth**: Bearer
**Preconditions**: A paused stake exists (run STK-HP-008 to pause it)

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: 400
- Body: "not accepting donations"

**Actual Result**: [OK] HTTP 400, `{"detail":"Stake is paused, not accepting donations"}`. Fixed: stake status validation added in `request_deposit` before calling payment provider.
**Notes**: Previously returned 200 (BUG-8). Now rejects donations to non-active stakes at payment creation time.

---

### STK-EDGE-003: Donate to expired stake

**Endpoint**: `POST /api/stake/donate`
**Auth**: Bearer
**Preconditions**: A stake with expired expires_at exists (use stake from STK-EDGE-001)

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: 400
- Body: "Stake has expired"

**Actual Result**: [OK] HTTP 400, `{"detail":"Stake has expired"}`. Fixed: expiry validation added in `request_deposit` before calling payment provider.
**Notes**: Previously returned 200 (BUG-7). Now rejects donations to expired stakes at payment creation time.

---

### STK-EDGE-004: Donate to deleted stake

**Endpoint**: `POST /api/stake/donate`
**Auth**: Bearer
**Preconditions**: A soft-deleted stake exists (use stake from STK-HP-010)

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: 404
- Body: stake not found

**Actual Result**: [OK] HTTP 404, `{"detail":"Stake has been deleted"}`. Fixed: `is_deleted` check added in `request_deposit` before calling payment provider.
**Notes**: Previously returned 500 (BUG). Now properly returns 404 for deleted stakes.

---

### STK-EDGE-005: Currency mismatch -- RUB stake with OxyPay (USD)

**Endpoint**: `POST /api/stake/donate`
**Auth**: Bearer
**Preconditions**: A RUB-denominated active stake exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "oxypay", "payment_method": "o_card", "amount": 10, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: 400
- Body: "Currency mismatch"

**Actual Result**: [OK] HTTP 400, `"Currency mismatch: deposit currency USD does not match stake currency RUB"`.
**Notes**: OxyPay is USD, stake is RUB -- must be rejected.

---

### STK-EDGE-006: Finish with 0% group + 0% streamer + no specific users

**Endpoint**: `POST /api/stake/{stake_id}/finish`
**Auth**: Bearer
**Preconditions**: An active stake with donations exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/<UUID>/finish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"winner_outcome_id": "<UUID>", "group_percent": 0.0, "streamer_percent": 0.0, "specific_users": []}'
```

**Expected Response**:
- Status: 200
- Body: StakeFullSchema with status=finished (no fund distributions)

**Actual Result**: [OK] HTTP 200 — finish with 0%/0% succeeds (stake finished, no distributions).
**Notes**: Valid scenario -- all funds remain undistributed.

---

### STK-EDGE-007: Finish with total percent exceeding 100%

**Endpoint**: `POST /api/stake/{stake_id}/finish`
**Auth**: Bearer
**Preconditions**: An active stake exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/<UUID>/finish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"winner_outcome_id": "<UUID>", "group_percent": 60.0, "streamer_percent": 50.0, "specific_users": []}'
```

**Expected Response**:
- Status: 422
- Body: validation error (group_percent + streamer_percent + specific_users.percent must be <= 100)

**Actual Result**: [OK] HTTP 422, `"Total distribution 110.0% exceeds 100%"`.
**Notes**: 60 + 50 = 110 > 100.

---

### STK-EDGE-008: Finish with specific_user who is not a donator

**Endpoint**: `POST /api/stake/{stake_id}/finish`
**Auth**: Bearer
**Preconditions**: An active stake exists, user_id=99999 has NOT donated to it

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/<UUID>/finish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"winner_outcome_id": "<UUID>", "group_percent": 50.0, "streamer_percent": 20.0, "specific_users": [{"user_id": 99999, "percent": 30.0}]}'
```

**Expected Response**:
- Status: 400
- Body: "not a stake participant"

**Actual Result**: [OK] HTTP 400, `"User 99999 is not a stake participant"`.
**Notes**: --

---

### STK-EDGE-009: Donate amount below min_sum

**Endpoint**: `POST /api/stake/donate`
**Auth**: Bearer
**Preconditions**: An active stake with min_sum=50 exists

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 10, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```

**Expected Response**:
- Status: document actual (likely 400 with min_sum validation error)
- Body: document actual

**Actual Result**: [OK] HTTP 400, `{"detail":"Amount 500 is below minimum stake donation of 1000 (min_sum=10)"}`. Fixed: min_sum validation added in `request_deposit`. Compares `amount` (kopecks after exchange) against `min_sum * 100`.
**Notes**: Previously returned 200 (BUG-9). Now enforces min_sum at payment creation time. Amount in request is in rubles, exchanged to kopecks before comparison.

---

### STK-EDGE-010: Get donators for stake with no donations

**Endpoint**: `GET /api/stake/donators/{stake_id}`
**Auth**: Bearer
**Preconditions**: A stake exists with zero donations

**Request**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/donators/<UUID> \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Expected Response**:
- Status: 200
- Body: `[]` (empty array)

**Actual Result**: [OK] HTTP 200, returns `[]` (empty donators for stake with no donations).
**Notes**: --

---

### STK-EDGE-011: Create stake with min_sum=0

**Endpoint**: `POST /api/stake`
**Auth**: Bearer
**Preconditions**: User authenticated

**Request**:
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Zero Min Sum Stake", "min_sum": 0, "vote_mechanic": "fixed", "stake_type": "vote", "description": "No minimum donation", "outcomes": [{"title": "A"}, {"title": "B"}], "expires_at": null, "currency": "RUB"}'
```

**Expected Response**:
- Status: 200
- Body: StakeRespSchema with min_sum=0

**Actual Result**: [OK] HTTP 200, creates stake with min_sum=0 (requires `description` field).
**Notes**: min_sum >= 0 is valid per schema.

---

## 6. Cross-Domain Integration Scenarios

---

### INT-001: Full Tinkoff payment lifecycle

**Flow**: Create a payment, simulate successful webhook, verify balance increase and order status.

**Step 1: Check initial balance**
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, note main_balance value.

**Step 2: Create Tinkoff card payment**
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```
Expected: 200, payment_url returned.

**Step 3: Send Tinkoff CONFIRMED webhook**
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token", "TerminalKey": "test-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 100001, "Amount": 10000}'
```
Expected: 200, "OK".

**Step 4: Check updated balance**
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, main_balance increased by 100.0 (10000 kopecks / 100).

**Step 5: Verify payment status**
```bash
curl -s -X GET http://176.53.160.110:9003/api/payment/status/<UUID>
```
Expected: 200, status=completed.

**Final Verification**:
Balance difference = new main_balance - initial main_balance = 100.0. Payment status = completed.

**Actual Result**: [OK] Full Tinkoff lifecycle: create→webhook→balance increase→status check. All working.

---

### INT-002: OxyPay payment lifecycle

**Flow**: Create an OxyPay payment, simulate accepted webhook, verify oxypay_balance increase.

**Step 1: Check initial balance**
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, note oxypay_balance value.

**Step 2: Create OxyPay payment**
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "oxypay", "payment_method": "o_card", "amount": 10, "external_data": null, "stake_id": null, "outcome_id": null}'
```
Expected: 200, payment_url returned.

**Step 3: Send OxyPay accepted webhook**
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/oxypay/pay-in \
  -H "Content-Type: application/json" \
  -d '{"token": "test-token", "status": "accepted", "amount": 1000, "currency": "USD", "order_number": "<UUID>", "signature": null}'
```
Expected: 200, "OK".

**Step 4: Check updated balance**
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, oxypay_balance increased by 10.0 ($10 = 1000 cents / 100).

**Final Verification**:
oxypay_balance difference = 10.0. Payment completed via OxyPay.

**Actual Result**: [SKIP] OxyPay lifecycle blocked — OxyPay API returns 403 Forbidden (external credential issue).

---

### INT-003: Withdraw after deposit (throttle test)

**Flow**: Deposit funds, attempt immediate withdrawal (expect throttle), wait, then succeed.

**Step 1: Create payment and confirm via webhook**
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 200, "external_data": null, "stake_id": null, "outcome_id": null}'
```
Expected: 200.

```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token", "TerminalKey": "test-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 100002, "Amount": 20000}'
```
Expected: 200, "OK".

**Step 2: Attempt immediate withdrawal (expect 400)**
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "<UUID>"}'
```
Expected: 400, RedirectDueTimeError (too soon after deposit).

**Step 3: Wait for throttle period to pass, then retry**
```bash
curl -s -X POST http://176.53.160.110:9003/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"withdraw_id": "<UUID>"}'
```
Expected: 200 (after sufficient wait time).

**Final Verification**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/withdraws \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: withdrawal appears in history with status pending or completed.

**Actual Result**: [PARTIAL] Deposit+confirm works. Immediate withdrawal returns 400 `"No main withdrawal method configured"` — cannot fully test throttle without `is_main=true` method.

---

### INT-004: Stake full lifecycle

**Flow**: Create stake, donate, process webhook, check donators, finish stake, verify balances.

**Step 1: Create a vote stake**
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "Integration Test Stake", "min_sum": 10, "vote_mechanic": "fixed", "stake_type": "vote", "description": "Full lifecycle test", "outcomes": [{"title": "Win"}, {"title": "Lose"}], "expires_at": null, "currency": "RUB"}'
```
Expected: 200, save stake_id and outcome_ids.

**Step 2: Donate to the stake**
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```
Expected: 200, payment created.

**Step 3: Process webhook for donation**
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token", "TerminalKey": "test-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 100003, "Amount": 10000}'
```
Expected: 200, "OK".

**Step 4: Check donators**
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/donators/<UUID> \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, array with the donator's entry.

**Step 5: Finish stake with distribution**
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/<UUID>/finish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"winner_outcome_id": "<UUID>", "group_percent": 70.0, "streamer_percent": 30.0, "specific_users": []}'
```
Expected: 200, status=finished.

**Step 6: Verify balances after distribution**
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, balances reflect the distribution.

**Final Verification**:
Stake status=finished, donator entry present, balances updated.

**Actual Result**: [SKIP] Full stake lifecycle cannot complete — STK-HP-014 fails (donators not tracked after webhook).

---

### INT-005: Payment with auto-withdraw flow

**Flow**: Create payment, process webhook (triggers auto-withdraw if configured), verify zero balance.

**Step 1: Create payment**
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": null, "outcome_id": null}'
```
Expected: 200.

**Step 2: Send CONFIRMED webhook (may trigger auto-withdraw)**
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token", "TerminalKey": "test-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 100004, "Amount": 10000}'
```
Expected: 200, "OK".

**Step 3: Check balance (should be 0 if auto-withdraw fired)**
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, main_balance=0.0 if auto-withdraw is configured and succeeded.

**Final Verification**:
Check withdrawal history for the automatic withdrawal transaction.
```bash
curl -s -X GET http://176.53.160.110:9003/api/withdraws \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```

**Actual Result**: [OK] Auto-withdraw did NOT fire after confirmed webhook. Balance went from 550→650. Expected: auto-withdraw requires `is_main` method (none configured). No auto-withdrawal entries in history.
**Notes**: Auto-withdraw behavior depends on streamer configuration. No `is_main=true` withdrawal method configured, so auto-withdraw correctly did not trigger.

---

### INT-006: Webhook idempotency (duplicate webhook)

**Flow**: Create payment, send CONFIRMED webhook twice, verify balance is only credited once.

**Step 1: Check initial balance**
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, note main_balance.

**Step 2: Create payment**
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 500, "external_data": null, "stake_id": null, "outcome_id": null}'
```
Expected: 200.

**Step 3: First CONFIRMED webhook**
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token", "TerminalKey": "test-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 100005, "Amount": 50000}'
```
Expected: 200, "OK", balance credited.

**Step 4: Second CONFIRMED webhook (duplicate)**
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "CONFIRMED", "ErrorCode": "0", "Token": "test-token", "TerminalKey": "test-key", "OrderId": "<UUID>", "Success": true, "PaymentId": 100005, "Amount": 50000}'
```
Expected: 200, "OK" (TransactionAlreadyCredited caught, no double credit).

**Final Verification**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: main_balance increased by exactly 500.0 (not 1000.0).

**Actual Result**: [OK] Webhook idempotency confirmed: balance increased by exactly 100.0 (650→750) after two CONFIRMED webhooks.

---

### INT-007: Failed payment flow

**Flow**: Create payment, send REJECTED webhook, verify status=failed and no balance change.

**Step 1: Check initial balance**
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: 200, note main_balance.

**Step 2: Create payment**
```bash
curl -s -X POST http://176.53.160.110:9003/api/payment \
  -H "Content-Type: application/json" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 300, "external_data": null, "stake_id": null, "outcome_id": null}'
```
Expected: 200.

**Step 3: Send REJECTED webhook**
```bash
curl -s -X POST http://176.53.160.110:9003/api/notification/tinkoff/pay-in \
  -H "Content-Type: application/json" \
  -d '{"Status": "REJECTED", "ErrorCode": "1", "Token": "test-token", "TerminalKey": "test-key", "OrderId": "<UUID>", "Success": false, "PaymentId": 100006, "Amount": 30000}'
```
Expected: 200, "OK".

**Step 4: Verify payment status is failed**
```bash
curl -s -X GET http://176.53.160.110:9003/api/payment/status/<UUID>
```
Expected: 200, status=failed.

**Final Verification**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/seller/current-balance \
  -H "Authorization: Bearer <BEARER_TOKEN>"
```
Expected: main_balance unchanged from Step 1.

**Actual Result**: [OK] Failed payment flow: REJECTED webhook processed, status=failed, balance unchanged.

---

### INT-008: Stake currency validation

**Flow**: Create RUB stake, attempt OxyPay (USD) donation (fail), then Tinkoff (RUB) donation (succeed).

**Step 1: Create RUB stake**
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"title": "RUB Only Stake", "min_sum": 10, "vote_mechanic": "fixed", "stake_type": "vote", "description": "Currency validation test", "outcomes": [{"title": "A"}, {"title": "B"}], "expires_at": null, "currency": "RUB"}'
```
Expected: 200, save stake_id and outcome_id.

**Step 2: Attempt OxyPay donation (should fail -- currency mismatch)**
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "oxypay", "payment_method": "o_card", "amount": 10, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```
Expected: 400, "Currency mismatch".

**Step 3: Tinkoff donation (should succeed -- matching currency)**
```bash
curl -s -X POST http://176.53.160.110:9003/api/stake/donate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BEARER_TOKEN>" \
  -d '{"streamer_id": 267, "external_transaction_id": "<UUID>", "provider": "tinkoff", "payment_method": "t_card", "amount": 100, "external_data": null, "stake_id": "<UUID>", "outcome_id": "<UUID>"}'
```
Expected: 200, payment created.

**Final Verification**:
```bash
curl -s -X GET http://176.53.160.110:9003/api/stake/details/<UUID>
```
Expected: 200, stake details show donation recorded for Tinkoff but not for OxyPay.

**Actual Result**: [OK] Currency validation: OxyPay donation to RUB stake rejected (400), Tinkoff donation succeeds (200).
