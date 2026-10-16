"""Create a consistent, checked SQLite snapshot; never overwrite a database."""
import argparse
import pathlib
import sqlite3
import tempfile
from contextlib import closing

def backup(source, destination):
    source, destination = pathlib.Path(source).resolve(), pathlib.Path(destination).resolve()
    if not source.is_file():
        raise ValueError('The source database does not exist.')
    if source == destination or destination.exists():
        raise ValueError('Choose a new backup path; existing files are never overwritten.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Reserve destination atomically; another backup cannot overwrite this run.
    with destination.open('xb'):
        pass
    try:
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro', uri=True)) as live, closing(sqlite3.connect(destination)) as snapshot:
            live.backup(snapshot)
            if snapshot.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Backup integrity verification failed.')
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise

def verify_restore(source):
    """Restore into a temporary database and verify integrity/record counts."""
    with tempfile.TemporaryDirectory() as td:
        restored = backup(source, pathlib.Path(td)/'restored.sqlite3')
        with closing(sqlite3.connect(restored)) as db:
            tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            return {name: db.execute('SELECT COUNT(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name in tables}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('destination', nargs='?')
    parser.add_argument('--verify-restore', action='store_true')
    args=parser.parse_args()
    if args.verify_restore:
        print('Verified temporary restore:', verify_restore(args.source))
    elif args.destination:
        print('Verified backup:', backup(args.source,args.destination))
    else:
        parser.error('Supply a destination or --verify-restore.')
