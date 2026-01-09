#!/usr/bin/env python3
"""Validate contacts emails and optionally delete invalid ones.

Usage:
  python scripts/validate_contacts.py [--mx] [--delete] [--timeout N]

Options:
  --mx       : Try MX lookup + SMTP RCPT check (requires dnspython for MX)
  --delete   : Delete invalid contacts from database (use with caution)
  --timeout N: Network timeout in seconds (default 10)

This script runs inside the Flask app context and uses the `Contact` model.
It first performs a robust regex check. If `--mx` provided it will attempt
an SMTP RCPT check against the mail server. If a contact is deemed invalid
it will be removed when `--delete` is specified. Otherwise it will print a
report of invalid contacts.
"""

import re
import sys
import time
import socket
import argparse
import os

# Ensure project root is on sys.path when running this script directly
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from extensions import db
from models import Contact

# Try to import dnspython for MX lookup
try:
    import dns.resolver
    HAVE_DNSPY = True
except Exception:
    HAVE_DNSPY = False

EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def check_format(email: str) -> bool:
    return EMAIL_RE.match(email) is not None


def mx_lookup(domain: str):
    if HAVE_DNSPY:
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(r.exchange).rstrip('.') for r in answers]
            return mx_hosts
        except Exception:
            return []
    else:
        # Fallback: try to use A record for domain
        try:
            return [domain]
        except Exception:
            return []


def smtp_check(email: str, timeout: int = 10) -> (bool, str):
    """Attempt to check recipient via SMTP RCPT TO.
    Returns (is_valid, reason)
    """
    domain = email.split('@')[-1]
    mx_hosts = mx_lookup(domain)
    if not mx_hosts:
        return False, f"no MX/A hosts for {domain}"

    # attempt RCPT TO on each MX host
    for host in mx_hosts:
        try:
            # Resolve host IPs
            addrinfo = socket.getaddrinfo(host, 25, proto=socket.IPPROTO_TCP)
            for family, socktype, proto, canonname, sockaddr in addrinfo:
                try:
                    s = socket.socket(family, socktype, proto)
                    s.settimeout(timeout)
                    s.connect(sockaddr)
                    # Simple SMTP handshake
                    f = s.makefile('rwb', buffering=0)
                    # read banner
                    banner = f.readline().decode(errors='ignore')
                    # send HELO
                    f.write(b"HELO validator\r\n")
                    _ = f.readline()
                    # MAIL FROM
                    f.write(b"MAIL FROM:<validator@example.com>\r\n")
                    _ = f.readline()
                    # RCPT TO
                    cmd = f"RCPT TO:<{email}>\r\n".encode()
                    f.write(cmd)
                    resp = f.readline().decode(errors='ignore')
                    # QUIT
                    f.write(b"QUIT\r\n")
                    f.readline()
                    f.close()
                    s.close()

                    if resp.startswith('250') or resp.startswith('251'):
                        return True, f"accepted by {host}: {resp.strip()}"
                    else:
                        # 550 etc means rejected
                        return False, f"rejected by {host}: {resp.strip()}"
                except socket.timeout:
                    # try next addr
                    continue
                except Exception as ex:
                    # try next addr
                    continue
        except Exception:
            continue
    return False, "no responsive MX servers"


def main():
    parser = argparse.ArgumentParser(description='Validate Contact emails')
    parser.add_argument('--mx', action='store_true', help='Perform MX+SMTP checks')
    parser.add_argument('--delete', action='store_true', help='Delete invalid contacts')
    parser.add_argument('--timeout', type=int, default=10, help='Network timeout in seconds')
    parser.add_argument('--dry-run', action='store_true', help='Do not delete even if --delete is given')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        contacts = Contact.query.all()
        print(f"Loaded {len(contacts)} contacts from database")

        invalid = []
        for c in contacts:
            email = (c.email or '').strip()
            if not check_format(email):
                invalid.append((c, 'invalid_format'))
                print(f"[FORMAT] {email} -> invalid format")
                continue
            if args.mx:
                valid, reason = smtp_check(email, timeout=args.timeout)
                if not valid:
                    invalid.append((c, reason))
                    print(f"[SMTP] {email} -> {reason}")
                else:
                    print(f"[SMTP] {email} -> OK ({reason})")
            else:
                # format-only check passed
                continue

        print('\nSummary:')
        print(f"Total contacts: {len(contacts)}")
        print(f"Invalid contacts detected: {len(invalid)}")

        if invalid and args.delete and not args.dry_run:
            print('\nDeleting invalid contacts...')
            for c, reason in invalid:
                print(f"Deleting {c.email} ({reason})")
                try:
                    db.session.delete(c)
                except Exception as e:
                    print(f"Failed to delete {c.email}: {e}")
            db.session.commit()
            print('Deleted and committed changes.')
        elif invalid and args.delete and args.dry_run:
            print('\nDry-run: not deleting because --dry-run set')
        elif invalid:
            print('\nRun with --delete to remove invalid contacts')

if __name__ == '__main__':
    main()
