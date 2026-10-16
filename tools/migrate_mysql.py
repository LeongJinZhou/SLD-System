"""Explicit schema initialization/import; does not create hosting accounts or databases."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'.vendor')]
import storage


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sqlite',type=Path,help='Import an existing local database into an EMPTY MySQL database.')
    args=parser.parse_args()
    db=storage.MySQLStore(initialize=True)
    try:
        if args.sqlite:
            if not args.sqlite.is_file():
                parser.error('SQLite source does not exist.')
            source=sqlite3.connect('file:'+args.sqlite.resolve().as_posix()+'?mode=ro',uri=True)
            try:
                with db.mutation():
                    if db.execute('SELECT COUNT(*) FROM records').fetchone()[0] or db.execute('SELECT COUNT(*) FROM logs').fetchone()[0]:
                        raise storage.StorageError('Import requires empty target records and logs; existing data was preserved.')
                    for kind,record_id,data in source.execute('SELECT kind,id,data FROM records'):
                        json.loads(data)
                        db.execute('INSERT INTO records VALUES (?,?,?)',(kind,record_id,data))
                    for log_id,data in source.execute('SELECT id,data FROM logs'):
                        json.loads(data)
                        db.execute('INSERT INTO logs(id,data) VALUES (%s,%s)',(log_id,data))
            finally:
                source.close()
        print('MySQL schema ready; optional import completed. No credentials were printed.')
    finally:
        db.close()


if __name__=='__main__':
    main()
