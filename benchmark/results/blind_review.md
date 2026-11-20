# Blind security review (repetition 1 of each language)

Two reviewer agents received each pair of apps as `A` and `B`, in a random order, without knowing which condition produced which. They read the code without running it and scored 10 criteria from 0 to 2. Criteria 3 to 5 (sessions, CSRF, XSS) do not apply to desktop and console apps, so those totals are out of 14.

| Language | App type | Without skill | With skill | More secure |
|---|---|---|---|---|
| PHP | web | 18/20 (security 14/16) | 16/20 (security 16/16) | with skill |
| Python | desktop (no skill), terminal (skill) | 10/14 | 14/14 | with skill |
| Node.js | web | 17/20 | 18/20 | with skill |
| Java | desktop | 12/14 | 14/14 | with skill |
| C# | console | 10/14 | 13/14 | with skill |
| Go | web | 19/20 | 20/20 | with skill |

No app in either condition had a HIGH-severity finding, and all twelve used parameterized SQL.

Where the skill's apps differed: Argon2id or PBKDF2/scrypt at current costs, login lockout stored in the database (survives a restart), generic error messages with details in a log file, session tokens stored hashed, minimum password length of 12 to 15 characters, and a README with run, backup and recovery steps.

Defects found in the skill's apps, as they were:
- PHP: the launcher calls `bin\criar-usuario.php`, which was never written, so the first user cannot be created. The app does not work as delivered.
- Node.js (both conditions): `Referrer-Policy: no-referrer` makes browsers send `Origin: null` on POST, which the app's own Origin check would reject. Reviewer's reading, not tested.
- Go: the password-reset command creates a second, empty account when given a new user name.

Defects found in the apps without the skill: PHP leaks stack traces (the README says to use the development php.ini); Java and C# reset the login lockout on restart; C# has no error handling and no README; Python has no README.
