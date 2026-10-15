# Running NBU-SuperAssistant on the laptop-server

NBU-SuperAssistant on the laptop-server is one Python process behind the
Cloudflare Tunnel that already carries the other apps on this machine,
CourseBench among them, one short run every morning that reminds
supervisors, and one every night that emails the owner a copy of the
applications. The records are a SQLite database and a few files in a folder
outside the clone. There is nothing to build and no database server to
install.

This follows CourseBench's `docs/deployment.md`, which read the host's
pattern off the machine itself: apps under `/home/victor/apps/`, one systemd
unit each, and the Cloudflare Tunnel `laptop-server` sending each hostname
**straight to a port on `127.0.0.1`**. Caddy is installed but is not in that
path; do not add anything to the Caddyfile.

The ports CourseBench's notes list as taken are 8000, 8001, 8002, 8003, 8012,
8501, 8787 and 8790 (CourseBench). NBU-SuperAssistant takes 8791.

## What runs where

| | |
|---|---|
| Clone | `/home/victor/apps/nbu-superassistant` |
| Records | `/home/victor/nbu-superassistant-data` (outside the clone, mode 700) |
| Settings | `/home/victor/apps/nbu-superassistant/.env.production` (chmod 600, never committed) |
| Port | `8791` on `127.0.0.1` (gunicorn) |
| Address | `https://nbu-superassistant.visiometrica.com` |
| Service | `nbu-superassistant` (`deploy/nbu-superassistant.service`) |
| Timer | `nbu-superassistant-remind.timer`, daily at 09:00 Europe/Sofia, which starts `nbu-superassistant-remind.service` |
| Timer | `nbu-superassistant-snapshot.timer`, nightly at 00:00 Europe/Sofia, which starts `nbu-superassistant-snapshot.service` |
| Mail | Resend's relay `smtp.resend.com`, port 587 with STARTTLS, sender `nbu-superassistant@visiometrica.com` |
| Tunnel | `laptop-server`, live configuration `/etc/cloudflared/config.yml` |

The pilot starts with a fresh records folder. Nothing from the Mac's
`~/superassistant-data` is copied.

Until constitution 8.7 is decided (NBU's agreement, a privacy notice and a
rule for deleting old records), the pilot's only users are **invented
students and supervisors who agreed to test**. Mail now goes to real
mailboxes, so every address the pilot uses must belong to somebody who
agreed: a student's sign-in address, a supervisor typed into an application,
and every entry in the professors list.

Nobody gives themselves a role. A supervisor has no account and acts only
through the links in the email the request comes in; a staff account sees
nothing until the owner approves it; the owner is the account the settings
name. What the pilot does not check yet is who signs in as a student and
which address is typed for a supervisor from outside the professors list
(another department, another university): a student who types one makes the
pilot mail that address the request and its reminders. Two lists the owner
will add later lock this down further: the department's supervisors with
their addresses, and the students with their faculty numbers and addresses
(`docs/reviews/milestone-2.md`).

Every command below runs on the laptop-server, as `victor`, in an ssh
session from the Mac (`ssh victor@192.168.1.102`), unless it says "on the
Mac".

## First install

### The repository on GitHub

The laptop clones the code from the owner's GitHub repository
`NBU-SuperAssistant`, the way it cloned CourseBench. If the repository is not
on GitHub yet, create it on github.com as an empty repository (no README,
licence or .gitignore), then, on the Mac:

```bash
cd /Users/victor/Documents/Projects/nbu-superassistant
git remote add origin git@github.com:quantumjazz/NBU-SuperAssistant.git
git push -u origin main
```

Nothing secret is in it: the settings file and the records are never
committed.

### The records folder and the code

```bash
mkdir -p /home/victor/nbu-superassistant-data
chmod 700 /home/victor/nbu-superassistant-data

cd /home/victor/apps
git clone git@github.com:quantumjazz/NBU-SuperAssistant.git nbu-superassistant
cd nbu-superassistant
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`python3` here is the host's Python 3.12.3. The Mac's is 3.9; the code runs
on both.

### The tests, once

They are offline, send no mail (a fake relay stands in for Resend) and work
in their own temporary folders. They are the only proof that the code works
on this machine's Python:

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

The browser tests are left out unless asked for. To run them as well, install
the browser they drive first (a download of a few hundred megabytes into
`~/.cache/ms-playwright`):

```bash
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest -q -m browser
```

If Chromium will not start, `sudo .venv/bin/python -m playwright install-deps
chromium` installs the system libraries it needs, as CourseBench's install
did.

### The settings file

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Every value is already right for this host except the Resend key, and one
line changes for the first start. The key is the one CourseBench already
uses. Copy it from CourseBench's settings file without ever showing it:

```bash
sed -i '/^SUPERASSISTANT_SMTP_PASSWORD=/d' .env.production && grep -m1 '^COURSEBENCH_SMTP_PASSWORD=' /home/victor/apps/coursebench/.env.production | sed 's/^COURSEBENCH_/SUPERASSISTANT_/' >> .env.production
grep -c '^SUPERASSISTANT_SMTP_PASSWORD=.' .env.production
```

The first line removes the empty password line and appends CourseBench's
under the new name, at the end of the file. The key travels only through the
pipe: it is never on the screen, in the shell history or on a command line.
The second line prints `1` when the key is there (a count, not the key). If
it prints `0`, CourseBench's file has no `COURSEBENCH_SMTP_PASSWORD` line with
a value, and nothing was copied. Running the first line again is harmless: it
still leaves exactly one password line.

Every value in this file is written bare: `KEY=value`, no quotes, no
`export`, no backslash. systemd removes quotes and backslashes and the host
commands would not, so a value written with them would give the service and
the commands different settings; the service and every command refuse such a
line, naming its number and setting (never its value).

### Prove the mail

Before anything depends on mail, send yourself one message. This needs only
the settings file, not the service or the address:

```bash
.venv/bin/python -m superassistant mail-test you@example.com
```

Use your own address. It says first what it will do (the mode, the relay's
host, port and security, the sender), then whether Resend accepted the
message. **Accepted is not delivered**: a relay that takes a message and
drops it looks the same as one that delivers it. Open the mailbox, and check
the spam folder. If Resend refuses, the command says why and ends with
status 1; a key that did not copy shows up here, not in front of a student.

Then, for the first start only, change one line:

```bash
nano .env.production
```

```
SUPERASSISTANT_BASE_URL=http://127.0.0.1:8791
```

and leave `SUPERASSISTANT_OWNER_USERNAME=` empty. *The owner's account*,
below, says why, and when both change.

### The port

This machine runs several apps. Check that nothing already holds 8791:

```bash
ss -ltn | grep 8791 || echo "8791 is free"
```

If something answers, choose another free port and change it in
`deploy/nbu-superassistant.service`, in the first-start address above and in
the tunnel entry below.

### The service

```bash
sudo cp deploy/nbu-superassistant.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nbu-superassistant
sleep 3
curl -s http://127.0.0.1:8791/healthz
```

The `sleep` matters. The worker does its start-up work (the checks, the
database, the lists) before it listens, and a `curl` fired the instant
`systemctl` returns gets "connection refused", which looks like a broken
install and is not one.

`{"status":"ok"}` means it runs and has just written a small file in the
records folder and removed it again. (The unit turns gunicorn's control
socket off: gunicorn 26 would otherwise open it at `~/.gunicorn/gunicorn.ctl`,
where CourseBench's gunicorn, running as the same user, already has its own.) Then read what it resolved:

```bash
sudo journalctl -u nbu-superassistant -n 20 --no-pager
```

One line, after the start, names the records folder, the address, the mail
mode (with the relay and the sender when it sends) and where the visitor's
address comes from. It never shows the key. This first start also writes the
four lists into the records folder (see *The lists*) and makes the session
key there.

## The owner's account, before the address is public

`/staff/register` is open to anyone who can reach the service, and the
account whose username `SUPERASSISTANT_OWNER_USERNAME` names becomes the
owner, with no approval. So the owner's account is registered while the
service answers only on this machine, before the address exists, and only
then named in the settings. The start also refuses an owner username that no
account has, which is why the setting is empty until now.

On the Mac, open a tunnel to the laptop and leave this window open:

```bash
ssh -L 8791:127.0.0.1:8791 victor@192.168.1.102
```

Open <http://127.0.0.1:8791/staff/register> in a browser on the Mac and
register: a username (it may not contain "@"), your email address and a
password, twice. The page says the account waits for approval and that no
owner is named yet; that is expected.

Then, on the laptop, set the two lines:

```bash
cd /home/victor/apps/nbu-superassistant
nano .env.production
```

```
SUPERASSISTANT_BASE_URL=https://nbu-superassistant.visiometrica.com
SUPERASSISTANT_OWNER_USERNAME=the-username-you-registered
```

and restart:

```bash
sudo systemctl restart nbu-superassistant
sleep 3
curl -s http://127.0.0.1:8791/healthz
sudo journalctl -u nbu-superassistant -n 20 --no-pager
```

The start line now names the https address. From here on, sign in at the
public address (next section): with an https address, the sign-in cookie is
sent over https only, so a browser on `http://127.0.0.1:8791` may not keep
you signed in. Your account is the owner's; `/owner` is where you approve
other staff accounts. Approve only people you know: once the address is
public, anybody can register, and the address will be found. The edge
certificate is the wildcard `*.visiometrica.com`, so the name does not appear
in certificate logs, but its DNS record is public and names get guessed.

## The address

There are **two files named `config.yml`** on this machine, and only one of
them is read:

- `/etc/cloudflared/config.yml`: the live one.
- `/home/victor/.cloudflared/config.yml`: a leftover. Editing it changes
  nothing, and the mistake is silent.

Confirm which one the tunnel reads before editing:

```bash
systemctl cat cloudflared | grep ExecStart
```

The path after `--config` is the file to edit. Add these two lines **before**
the catch-all `- service: http_status:404` entry, which must stay last, and
indent them like the entries already there:

```bash
sudo nano /etc/cloudflared/config.yml
```

```yaml
  - hostname: nbu-superassistant.visiometrica.com
    service: http://127.0.0.1:8791
```

Then create the DNS record and restart the tunnel:

```bash
cloudflared tunnel route dns laptop-server nbu-superassistant.visiometrica.com
sudo systemctl restart cloudflared
curl -s https://nbu-superassistant.visiometrica.com/healthz
```

Restarting `cloudflared` briefly interrupts **every** site on the tunnel,
CourseBench included, for the few seconds it takes to reconnect; do it when
nobody is in the middle of something. The DNS record can take a minute to
answer. If the curl fails, try `curl -s http://127.0.0.1:8791/healthz`: if
that answers, NBU-SuperAssistant is fine and the problem is the route.

Behind the tunnel, every request arrives from `127.0.0.1`. The limits on how
much mail one visitor may ask for therefore count the address Cloudflare
puts in `CF-Connecting-IP` (`SUPERASSISTANT_CLIENT_IP_HEADER`). That setting
is right only here: never set it on an installation reachable other than
through the tunnel, where anyone could write the header.

## Mail

With `SUPERASSISTANT_MAIL_MODE=send`, every message goes to its intended
recipient through Resend, unchanged, from
`NBU-SuperAssistant <nbu-superassistant@visiometrica.com>`. The pages no
longer show the development notice. The messages are: a student's sign-in
link and code, the request to a supervisor (when a student submits or
chooses another supervisor after a decline, or staff change the supervisor or
the graduation type), the reminders, and the notice to a student whose
supervisor confirmed or declined.

The relay is proved with `mail-test` during the first install (*Prove the
mail*); run it again whenever mail is in doubt.

**The sender's domain.** Resend sends only from a domain verified in the
account. The key is CourseBench's, so this is CourseBench's Resend account.
On 10 October 2026 `visiometrica.com` carried Resend's records (DKIM at
`resend._domainkey`, SPF and MX at `send.`), so any address at it can send;
Resend's dashboard, under Domains, says whether it is still verified. If it
is not, Resend refuses the test, and the command says so.

**The quota is shared.** Resend's free plan allows 100 messages a day and
3,000 a month, per account, and this account is CourseBench's too: both apps
spend the same 100. Every sign-in, request, reminder and notice counts.
NBU-SuperAssistant's own limits (3 sign-in messages an hour to one address,
10 from one visitor, an IPv6 visitor counting by its /64 block, 30 an hour to
one supervisor, 10 notices an hour to one student, 300 messages an hour in
all) do not keep it under Resend's 100 a day. A paid Resend plan is DEFERRED
(`docs/reviews/milestone-2.md`).

The 09:00 reminders count against the same 30 an hour to one supervisor as
new requests do. A supervisor with very many reminders due on one morning
could therefore refuse new requests until the hour has passed; at the
pilot's size this does not arise.

When Resend refuses a message (over the quota, or for any other reason),
nothing pretends it was sent:

- a student asking to sign in is told the message could not be sent, and to
  try again later;
- submitting an application, or choosing another supervisor after a
  decline, is refused: the page says the application was not submitted,
  because the message to the supervisor could not be sent;
- a staff change of supervisor or graduation type changes nothing, and the
  page says the request could not be sent;
- a supervisor's confirmation or decline is still recorded, and the page
  says the student was not told by mail; the student sees it on the
  application page;
- the reminder run names each reminder it could not send and ends with
  status 1. Nothing is recorded for those, so the next morning's run tries
  them again.

The relay is greeted with this machine's hostname. Set
`SUPERASSISTANT_SMTP_EHLO` only if a relay ever refuses that.

## The reminder timer

```bash
cd /home/victor/apps/nbu-superassistant
sudo cp deploy/nbu-superassistant-remind.service deploy/nbu-superassistant-remind.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nbu-superassistant-remind.timer
systemctl list-timers nbu-superassistant-remind.timer
```

Enable the timer, not the service: the service runs only when the timer
starts it. `list-timers` shows the next 09:00.

Run it once by hand, and read what it did:

```bash
sudo systemctl start nbu-superassistant-remind.service
sudo journalctl -u nbu-superassistant-remind -n 20 --no-pager
```

`systemctl start` waits until the run ends. The journal shows how many
reminders it sent (none, on a fresh install) and a line for each one it
could not send. A run by hand follows the same rule as the timer's, so on a
day the timer has already run it sends nothing more, except the reminders
that run could not send: those are tried again by any later run.

**The rule.** Reminders count calendar days in Sofia; the time of day does
not matter. A request is due for a reminder when today's Sofia date is at
least `SUPERASSISTANT_REMINDER_DAYS` (3) days after the Sofia date of its last
mail, which is the request or its latest reminder, and it has had fewer than
`SUPERASSISTANT_REMINDER_COUNT` (2) reminders. A request that is answered or
replaced is never reminded. A second run on the same Sofia day sends nothing
more.

The owner's example: a request sent on Monday at 14:00 is reminded on
Thursday at 09:00 and again on Sunday at 09:00, and then never again.

If the laptop was off at 09:00, the timer runs once at the next boot
(`Persistent=true`), and the next reminder counts from the day the late one
was actually sent: a Thursday reminder sent on Friday is followed by one on
Monday.

The timer runs the clone's current code each time, so an update needs
nothing for it, unless the update changed its unit files (see *Updating*).

## The nightly copy

```bash
cd /home/victor/apps/nbu-superassistant
sudo cp deploy/nbu-superassistant-snapshot.service deploy/nbu-superassistant-snapshot.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nbu-superassistant-snapshot.timer
systemctl list-timers nbu-superassistant-snapshot.timer
```

Enable the timer, not the service. `list-timers` shows the next 00:00.

Run it once by hand, and read what it did:

```bash
sudo systemctl start nbu-superassistant-snapshot.service
sudo journalctl -u nbu-superassistant-snapshot -n 20 --no-pager
```

Every night at 00:00, Sofia time, the run writes every submitted
application, those in the bin included and marked, to
`/home/victor/nbu-superassistant-data/snapshots/zaiavlenia-YYYY-MM-DD.csv`,
readable by `victor` only, and emails it as an attachment to the address of
the owner's account, the one `SUPERASSISTANT_OWNER_USERNAME` names, through
the relay like every message: one of Resend's 100 a day. It then removes
the copies 30 days old or older, so the folder holds the last 30 days. The
journal says where the file is, how many applications it holds and which
old copies went.

An application deleted from the bin is gone from the database file at once
and from the next night's copy. It stays in the nightly copies of the
previous 30 days in the `snapshots` folder (fewer if nights were missed, as
a run removes old copies only when it runs), in the messages already
received until the owner deletes them, in the Word files of reports, kept
or in the bin, and in every backup taken before the deletion.

Resend refuses a message above its size limit (its documentation gives the
current figure; an attachment grows by about a third on the way). The
journal says the size of each night's file; a refused copy fails the unit,
and deleting old applications from the bin makes the file smaller.

The file opens in Excel on the Mac: semicolons between cells, as Excel
expects where numbers have a decimal comma, and the UTF-8 mark, so Cyrillic
reads right. A phone number, a grade or a date shows exactly as typed, and
nothing typed into an application runs as a formula.

If the laptop was off at 00:00, the timer runs once at the next boot
(`Persistent=true`). A second run on the same day writes that day's file
again and sends it again. When the relay refuses the message, the file
stays, the run ends with status 1, and the unit shows failed until the
next night.

## The lists

The owner's lists are four CSV files in
`/home/victor/nbu-superassistant-data/lists`:

| File | Holds | Header row |
|---|---|---|
| `titles.csv` | academic titles | `звание` |
| `faculties.csv` | faculties and their deans | `код,факултет,звание на декана,декан` |
| `programmes.csv` | programmes, degree, form and faculty | `код,степен,програма,форма,факултет` |
| `professors.csv` | supervisors students can choose | `код,звание,име,email` |

They are UTF-8, one entry per line, separated by commas, under that header,
which must stay as it is. The first start writes them from the values in
`domain.md`. `programmes.csv` starts with the owner's 17 programmes of 13
October 2026, one row per programme and form, each with its code in Locus:
BSNADM01, BSNADM04, BSNBUB04, BSNDIU01, BSNTUR01, BSNDIT01, BSNDIT04,
MSNADM21, MSNALH03, MSNHRB05, MSNHRE08, MSNMBA01, MSNMBA12, MSNMBA81,
MSNMBA80, MSNSMQ11 and MSNSMQ09. Students choose a programme by its name and
form; staff see its code. **`professors.csv` starts empty**, with its header
only. Until 8.7 is decided, it lists only supervisors who agreed to test,
with their own addresses: a student who chooses one makes
NBU-SuperAssistant mail them. A professor's title must be one in
`titles.csv`.

Edit them on the laptop:

```bash
nano /home/victor/nbu-superassistant-data/lists/professors.csv
```

or on the Mac, and copy the file over:

```bash
scp professors.csv victor@192.168.1.102:/home/victor/nbu-superassistant-data/lists/
```

A spreadsheet set to Bulgarian may save semicolons instead of commas; the
start then refuses the file, naming the line.

The service reads the lists when it starts, so **restart after editing**:

```bash
sudo systemctl restart nbu-superassistant
sleep 3
curl -s http://127.0.0.1:8791/healthz
```

A list that cannot be read (a changed header, a missing column, a code used
twice, a title not in `titles.csv`, or an entry an application still uses
taken out) stops the start, and the journal names the file and the line. Put
the line right and restart. No answer from the `curl` means it did not start:
read the journal. The reminder run and the nightly copy read the lists too,
so a broken list also stops that morning's reminders and that night's copy.

## Everyday commands

```bash
sudo systemctl status nbu-superassistant
sudo systemctl restart nbu-superassistant
sudo systemctl stop nbu-superassistant
sudo journalctl -u nbu-superassistant -n 100 --no-pager
sudo journalctl -u nbu-superassistant -f
systemctl list-timers nbu-superassistant-remind.timer
sudo journalctl -u nbu-superassistant-remind -n 50 --no-pager
systemctl list-timers nbu-superassistant-snapshot.timer
sudo journalctl -u nbu-superassistant-snapshot -n 50 --no-pager
```

After a restart, the start line says what the process actually resolved: the
records folder, the address, the mail mode and where the visitor's address
comes from. When something behaves oddly, read it before anything else. It
is the process's own answer, not what the settings file appears to say.

After editing `.env.production`, restart the service. The timers and the
host commands read the file each time they run.

### Host commands

```bash
cd /home/victor/apps/nbu-superassistant
.venv/bin/python -m superassistant remind
.venv/bin/python -m superassistant owner-password
.venv/bin/python -m superassistant mail-test you@example.com
.venv/bin/python -m superassistant snapshot
```

- `remind` sends the reminders due now, by the same rule as the timer.
- `owner-password` sets a new password for the owner's account. It asks for
  it twice, never takes it on the command line, and signs every browser on
  that account out. No emailed code or link exists for the owner.
- `mail-test` sends one test message (see *Mail*).
- `snapshot` writes and sends the copy of the applications now, as the
  nightly timer does (see *The nightly copy*).

They read `.env.production` from the clone themselves, the same file the
service is pointed at, so they open the same records; a variable already
exported in the shell wins. Run them from the clone, as `victor`, and never
with `sudo`: a file a root process makes in the records folder is one the
service cannot write.

## Updating

```bash
cd /home/victor/apps/nbu-superassistant
git fetch origin
git diff --stat HEAD origin/main -- deploy/ .env.production.example
git pull --ff-only origin main
.venv/bin/pip install -r requirements.txt
sudo systemctl restart nbu-superassistant
sleep 3
curl -s https://nbu-superassistant.visiometrica.com/healthz
```

The `git diff` line shows, before anything changes, whether the update
touches the unit files or the settings template. If a unit file changed,
copy it again (the `sudo cp` lines above) and run `sudo systemctl
daemon-reload` before the restart. If the update adds a unit, install it as
its own section says, timer enabled, before the restart: the update of 15
October 2026 adds the nightly copy's two units (*The nightly copy*), and the
backup and restore lines below expect both timers installed. If the
template changed, compare it with your `.env.production`.

The records are untouched by this, which is why they sit outside the clone.
A version that changes the database migrates it at its start, keeping every
row. The `pip install` line is how a new dependency arrives.

## Backups

`/home/victor/nbu-superassistant-data` is the only thing that matters. The
clone is disposable: it can be deleted and cloned again.

Three programs write in the records folder: the service; the reminder run,
which its timer starts at 09:00; and the nightly copy, which its timer starts
at 00:00. Each timer also catches up a time it missed, at the next boot or
when it is started again. A backup and a restore therefore stop all three.
First the two timers, so they start no new run. Then they wait for a run
already under way to end, so no reminder is cut off between its mail and its
record. Then the service.

### Taking a backup

```bash
sudo systemctl stop nbu-superassistant-remind.timer nbu-superassistant-snapshot.timer
while systemctl show -p ActiveState --value nbu-superassistant-remind.service nbu-superassistant-snapshot.service | grep -qx -e activating -e deactivating; do sleep 2; done
sudo systemctl stop nbu-superassistant
backup=/home/victor/nbu-superassistant-backup-$(date +%Y%m%d-%H%M%S).tgz
(umask 077; set -o noclobber; tar czf - -C /home/victor nbu-superassistant-data > "$backup.partial") && test ! -e "$backup" && mv "$backup.partial" "$backup" && ls -l "$backup"
sudo systemctl start nbu-superassistant
sudo systemctl start nbu-superassistant-remind.timer nbu-superassistant-snapshot.timer
```

Every backup gets a name of its own, to the second, and `noclobber` refuses
to write over a file that already exists, so a backup never replaces an
earlier one. It is written as `….tgz.partial` and gets its `.tgz` name only
once `tar` has finished without an error, so a backup cut short never looks
like a whole one; a `.partial` file left behind is a failed backup, to be
deleted. `umask 077` makes the archive yours alone from the moment it exists:
it holds everything people entered and the session key. If 09:00 passed while
the timers were stopped, starting them again sends that morning's reminders
at once, and if 00:00 passed, that night's copy.

Keep a copy off the laptop as well; a backup on the same disk goes with the
disk. On the Mac:

```bash
scp 'victor@192.168.1.102:/home/victor/nbu-superassistant-backup-*.tgz' .
```

### Restoring a backup

A restore keeps the current records under a new name, so a restore can
itself be undone. Write the name of the backup to restore in the first line:

```bash
backup=/home/victor/nbu-superassistant-backup-YYYYMMDD-HHMMSS.tgz
sudo systemctl stop nbu-superassistant-remind.timer nbu-superassistant-snapshot.timer
while systemctl show -p ActiveState --value nbu-superassistant-remind.service nbu-superassistant-snapshot.service | grep -qx -e activating -e deactivating; do sleep 2; done
sudo systemctl stop nbu-superassistant
kept=/home/victor/nbu-superassistant-data.before-restore-$(date +%Y%m%d-%H%M%S)
test -f "$backup" && test ! -e "$kept" && staging=$(mktemp -d /home/victor/nbu-superassistant-restore-XXXXXX) && tar xzf "$backup" -C "$staging" nbu-superassistant-data && test -d "$staging/nbu-superassistant-data" && test ! -L "$staging/nbu-superassistant-data" && mv /home/victor/nbu-superassistant-data "$kept" && mv "$staging/nbu-superassistant-data" /home/victor/nbu-superassistant-data && rmdir "$staging" && chmod 700 /home/victor/nbu-superassistant-data && ls -ld "$kept" /home/victor/nbu-superassistant-data && sudo systemctl start nbu-superassistant && sudo systemctl start nbu-superassistant-remind.timer nbu-superassistant-snapshot.timer
curl -s http://127.0.0.1:8791/healthz
```

The backup is first unpacked into a private folder of its own,
`nbu-superassistant-restore-…` (mode 700), and `tar` takes only the records
folder out of it, so a wrong archive writes nothing anywhere else. The
current records are moved aside only once the unpacking succeeded and gave a
real folder. The long line stops at the first step that fails, and nothing
starts. So if the backup's name was wrong, or the backup is damaged, the
current records have not moved: whatever was unpacked stays in the
`restore-…` folder to be looked at, then deleted (it holds the session key),
and `sudo systemctl start nbu-superassistant && sudo systemctl start
nbu-superassistant-remind.timer nbu-superassistant-snapshot.timer` brings
everything back as it was; or
correct the first line and run the rest again. Delete the kept folder only
once the restored records are confirmed.

To undo a restore, or if the line stopped after moving the current records
aside, put the kept records back, setting aside whatever is at the records
path:

```bash
failed=/home/victor/nbu-superassistant-data.failed-restore-$(date +%Y%m%d-%H%M%S)
test -n "$kept" && test -d "$kept" && sudo systemctl stop nbu-superassistant-remind.timer nbu-superassistant-snapshot.timer && { while systemctl show -p ActiveState --value nbu-superassistant-remind.service nbu-superassistant-snapshot.service | grep -qx -e activating -e deactivating; do sleep 2; done; } && sudo systemctl stop nbu-superassistant && { test ! -e /home/victor/nbu-superassistant-data || { test ! -e "$failed" && mv /home/victor/nbu-superassistant-data "$failed" && chmod 700 "$failed"; }; } && test ! -e /home/victor/nbu-superassistant-data && mv "$kept" /home/victor/nbu-superassistant-data && ls -ld /home/victor/nbu-superassistant-data* && sudo systemctl start nbu-superassistant && sudo systemctl start nbu-superassistant-remind.timer nbu-superassistant-snapshot.timer
```

It does nothing unless the kept folder is there. Then, like a backup and a
restore, and before it moves anything, it stops the timers, waits for a
run under way to end, and stops the service: after a restore that
succeeded, all are running again. It moves whatever is at the records path
to a failed-restore name of its own, private (mode 700) like the records,
where it stays to be looked at, never into another folder. It moves the kept
records back only to an empty path, and it starts the service and the timers
only once they are back. Like the restore, it stops at the first step that
fails, with both still stopped. Run it in the same window as the
restore; in a new one, first set `kept` to the folder `ls -d
/home/victor/nbu-superassistant-data.before-restore-*` shows for that
restore.

## What is public without signing in

- `/`, the students' sign-in page; `/sign-in`, which sends the link and the
  code; and `/sign-in/code`, which takes the code.
- `/link/<token>`, the page a sign-in link opens. Opening it spends nothing,
  because mail scanners open links; its button signs the student in.
- `/staff/sign-in`, and `/staff/register`, which anyone can use: a new
  account waits until the owner approves it on `/owner`, except the one
  `SUPERASSISTANT_OWNER_USERNAME` names.
- `/answer/<token>/confirm` and `/answer/<token>/decline`, a supervisor's
  answer pages from the links in a request or reminder. Opening one records
  nothing; its button records the answer.
- `/healthz`: `{"status":"ok"}` or not. It never names a path.
- `/static/`: the stylesheet.

Everything else requires signing in: a student's application and forms
(`/application`), the staff pages and reports (`/staff`) and the owner's page
(`/owner`).

The sign-in links and the answer pages carry their tokens in the address.
That is why the service writes no access log (see the comment in
`deploy/nbu-superassistant.service`), and why an unexpected error is logged
with its route (`/link/<token>`) rather than its address.

Until the owner's lists of students and supervisors are added, anyone with
a mailbox can sign in as a student, and a supervisor typed from outside the
professors list is mailed at the address typed. See the pilot's users at the
top.

## If it will not start

```bash
sudo journalctl -u nbu-superassistant -n 50 --no-pager
```

**"NBU-SuperAssistant cannot start: …"** is a deliberate refusal, and the
sentence names the setting. systemd tries again every five seconds
(`Restart=always`), so the line repeats until the setting is fixed. Fix
`.env.production`, then `sudo systemctl restart nbu-superassistant`.

| The sentence names | Fix in `.env.production` |
|---|---|
| `SUPERASSISTANT_BASE_URL` as more than an address | just `https://nbu-superassistant.visiometrica.com`: scheme and host, no path, query, `#`, user or password, and a port only from 1 to 65535 |
| `SUPERASSISTANT_BASE_URL` as not https | `https://`; `http://` is only for `127.0.0.1` or `localhost`, as in the first start |
| `SUPERASSISTANT_DATA_DIR` as not set | `SUPERASSISTANT_DATA_DIR=/home/victor/nbu-superassistant-data` |
| `SUPERASSISTANT_DATA_DIR` as inside the clone | a folder beside the clone, not in it |
| `SUPERASSISTANT_MAIL_MODE` as unset or console | `SUPERASSISTANT_MAIL_MODE=send`; otherwise students' sign-in links would only be printed |
| `SUPERASSISTANT_SMTP_HOST` or `SUPERASSISTANT_MAIL_FROM`, with mail mode send | `smtp.resend.com`; `nbu-superassistant@visiometrica.com` |
| `SUPERASSISTANT_MAIL_MODE` as an unknown mode | `send` |
| `SUPERASSISTANT_OWNER_USERNAME` as naming no account | the username exactly as registered; or leave it empty, register the account (*The owner's account*), then set it |
| `SUPERASSISTANT_REMINDER_DAYS` or `SUPERASSISTANT_REMINDER_COUNT` | a whole number, at least 1 and at least 0; or take the line out for the defaults |
| a line of `.env.production` and a setting, as written with quotes or a backslash | write the value bare, `KEY=value` |
| a list file and a line | put that line right (*The lists*) |

**"Failed to load environment files"**: `.env.production` is missing from
the clone, or misnamed.

**"connection refused" straight after a restart**: usually just impatience;
see the `sleep 3` above. If it persists, read the journal: a start that
fails is tried again every five seconds, so `systemctl status` can look
normal at a glance while nothing answers. The public address then shows
Cloudflare's error page.

**`status=203/EXEC`**: the path in `ExecStart` is wrong, usually because the
clone or its `.venv` moved, or `pip install -r requirements.txt` was not run.
A virtual environment records its own location: rebuild it rather than
copying it.

**`status=217/USER`**: `User=` in the unit does not match a real account.

**`{"status":"data directory is not writable"}`**: the records folder is
missing or its permissions changed. `ls -ld
/home/victor/nbu-superassistant-data` should start with `drwx------` and name
`victor` as its owner. A host command run with `sudo` can leave a file the
service cannot write; `find /home/victor/nbu-superassistant-data ! -user
victor` lists any.

**The reminder unit shows failed**: a reminder could not be sent, or the
start refused (a setting, a list). `sudo journalctl -u
nbu-superassistant-remind -n 50 --no-pager` says which. The timer still runs
the next morning.

**The nightly copy's unit shows failed**: the copy could not be sent, the
owner's account is not named, or the start refused. `sudo journalctl -u
nbu-superassistant-snapshot -n 50 --no-pager` says which; a copy written
but not sent is in the `snapshots` folder. The timer still runs the next
night.
