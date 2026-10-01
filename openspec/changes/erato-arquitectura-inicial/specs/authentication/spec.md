# Authentication Specification

## Purpose

Defines the behavioral contract for user registration, login, credential storage, and token
issuance/validation, per confirmed decision 3 (self-rolled email/password + JWT, backend-enforced).
This spec covers identity only — the composition-level sharing/visibility rules are specified
separately in the Sharing and Visibility specification.

## Requirements

### Requirement: Users MUST be able to register with email and password

The system MUST allow a new user to register using an email address and a password, and MUST
reject registration attempts with invalid or already-registered emails.

#### Scenario: Successful registration with a new email

- GIVEN no account exists for a given email address
- WHEN a user submits registration with that email and a valid password
- THEN the system MUST create the account
- AND MUST NOT store the submitted password in plain text

#### Scenario: Registration is rejected for an already-registered email

- GIVEN an account already exists for a given email address
- WHEN a registration request is submitted with that same email
- THEN the system MUST reject the request with a structured error
- AND MUST NOT create a duplicate account

#### Scenario: Registration is rejected for a malformed email or weak password

- GIVEN a registration request contains an invalid email format or a password that does not meet
  the minimum strength policy
- WHEN the request is submitted
- THEN the system MUST reject the request with a structured validation error
- AND MUST NOT create an account

### Requirement: Passwords MUST be stored using a secure, salted hash

The system MUST hash passwords with a modern, salted hashing algorithm (e.g. bcrypt or argon2)
before persisting them, and MUST NOT store or log plaintext passwords at any point.

#### Scenario: Password is hashed before persistence

- GIVEN a user registers or changes their password
- WHEN the credential is persisted
- THEN the stored value MUST be a salted hash, not the plaintext password
- AND the hashing algorithm MUST use a per-user (or per-hash) salt

#### Scenario: Plaintext password never appears in logs

- GIVEN a registration or login request is processed
- WHEN the backend logs request handling (errors, access logs, etc.)
- THEN the logged output MUST NOT contain the plaintext password

### Requirement: Users MUST be able to log in and receive a JWT

The system MUST allow a registered user to authenticate with email and password and, on success,
MUST issue a signed JWT bearer token. On failure, the system MUST reject the attempt without
revealing which part (email or password) was incorrect.

This design is stateless by choice: JWT validation needs no database round trip, which helps the
backend stay within the Vercel 10-second execution budget and avoids adding load to Atlas M0's
connection and operation-rate limits — serving the zero-recurring-cost constraint indirectly by
avoiding pressure that would otherwise justify a paid tier upgrade.

#### Scenario: Successful login issues a valid JWT

- GIVEN a registered user submits their correct email and password
- WHEN the login request is processed
- THEN the system MUST verify the password against the stored hash
- AND MUST issue a signed JWT containing the user's identity and an expiration claim

#### Scenario: Login fails without revealing which field was wrong

- GIVEN a login request has either an unregistered email or an incorrect password
- WHEN the request is processed
- THEN the system MUST reject the request with a generic authentication-failure error
- AND MUST NOT indicate whether the email exists or specifically which field was incorrect

### Requirement: The backend MUST validate the JWT on every request to a protected endpoint

Every request to a protected endpoint MUST include a valid, non-expired JWT. The backend MUST
verify the token's signature and expiration before executing any protected handler logic.

#### Scenario: Valid, unexpired token grants access to a protected endpoint

- GIVEN a request includes a JWT that is correctly signed and not expired
- WHEN the request reaches a protected endpoint
- THEN the backend MUST accept the token, extract the user identity, and proceed to handler logic

#### Scenario: Expired or invalid token is rejected

- GIVEN a request includes a JWT that is expired, has an invalid signature, or is malformed
- WHEN the request reaches a protected endpoint
- THEN the backend MUST reject the request with a 401 status code
- AND MUST NOT execute the protected handler logic

#### Scenario: Missing token on a protected endpoint is rejected

- GIVEN a request to a protected endpoint includes no JWT at all
- WHEN the backend processes the request
- THEN the backend MUST reject the request with a 401 status code
