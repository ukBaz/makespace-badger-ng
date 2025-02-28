#!/usr/bin/env python3

from db import Database
from label import Label
from tagreader import TagReader
from fakereader import FakeTagReader
from printer import DisplayPrinter, RotatePrinter
from printer_d450 import PrinterDymo450
from printer_tspl import PrinterVretti420B
from app_ui import BadgerApp
from sound import SoundThread
import argparse
import datetime
import time
import tkinter as tk
import multiprocessing
from tkinter import ttk

def open_db(args):
    if not args.init:
        # Check if the DB file exists
        try:
            db = Database(f'file:{args.database}?mode=ro')
            db.close()
        except Exception as e:
            raise

    db = Database(args.database)
    if args.init:
        try:
            db.initialise()
        except Exception as e:
            raise

    return db

def enrol(args):
    db = open_db(args)

    tag = bytes.fromhex(args.tag)
    print(f'Enrolling tag: {tag.hex()}, name: {args.name}, contact: {args.contact}')
    db.insert(tag, args.name, args.contact)

def update(args):
    db = open_db(args)

    tag = bytes.fromhex(args.tag)
    print(f'Updating tag: {tag.hex()}, name: {args.name}, contact: {args.contact}')
    db.update(tag, args.name, args.contact)

def lookup(args):
    db = open_db(args)

    tag = bytes.fromhex(args.tag)
    name, contact = db.lookup(tag)
    print(f'Lookup tag:{tag.hex()}, name:{name}, contact:{contact}')

def reader(args):
    tagreader = TagReader(args.port)

    db = None
    if args.database:
        db = Database(args.database)

    now = datetime.datetime.now()
    end = now + datetime.timedelta(seconds = args.timeout)
    while True:
        time.sleep(0.1)
        tag = tagreader.read_tag()
        if tag:
            print("tag:", tag.hex())
            print("buttons:", tagreader.read_buttons())
            if db:
                try:
                    name, comment = db.lookup(tag)
                    print(f"name: {name}\ncomment: {comment}")
                except ValueError:
                    print("Not found in database")
            if not args.loop:
                break

        if datetime.datetime.now() > end:
            print("Timeout reached.")
            break

def label(args):
    lbl = Label(args.lines, args.dpi, (args.width_mm, args.height_mm))

    img = lbl.image()
    if args.out is None:
        img.show()
    else:
        img.save(args.out)

def run_ui(args):
    root = tk.Tk()

    if args.database:
        db = open_db(args)
    else:
        db = None

    if args.printer == 'display':
        printer = DisplayPrinter()
    elif args.printer == 'display_r90':
        printer = RotatePrinter(DisplayPrinter())
    elif args.printer == 'd450':
        printer = RotatePrinter(PrinterDymo450())
    elif args.printer == 'vretti':
        printer = RotatePrinter(PrinterVretti420B())
    else:
        raise ValueError("No printer?")

    if args.port == "fake":
        reader_window = tk.Toplevel(root)
        tagreader = FakeTagReader(reader_window)
    else:
        try:
            tagreader = TagReader(args.port)
        except:
            tagreader = None
            print("Couldn't open tag reader (did you specify the correct --port?)")

    if args.sound:
        queue = multiprocessing.Queue()
        sound = SoundThread(queue)
        soundproc = multiprocessing.Process(target=sound.run)
        soundproc.start()
    else:
        sound = None

    root.resizable(False,False)
    app = BadgerApp(root, printer=printer, tagreader=tagreader, db=db, sound=sound)
    app.mainloop()
    sound.stop()
    soundproc.join()

def main():
    parser = argparse.ArgumentParser(
                        prog='badger-ng',
                        description='Makespace Badger')

    subparsers = parser.add_subparsers(title="Sub-commands")

    # Command arguments for db commands
    db_cmd_parser = argparse.ArgumentParser(description="parent parser for db commands", add_help = False)
    db_cmd_parser.add_argument('--init', action='store_true')
    db_cmd_parser.add_argument('-d', '--database', help='sqlite3 database file', required=True)

    # Common arguments for tag handling commands
    tag_cmd_parser = argparse.ArgumentParser(description="parent parser for tag commands", add_help = False)
    tag_cmd_parser.add_argument('tag', help='Tag ID')
    tag_cmd_parser.add_argument('name', help='Tag owner name')
    tag_cmd_parser.add_argument('contact', help='Tag owner contact')

    enrol_parser = subparsers.add_parser('enrol', add_help=True,
                                         parents=[db_cmd_parser, tag_cmd_parser],
                                         description='Add a tag in the database',
                                         help='Add a tag to the database')
    enrol_parser.set_defaults(func=enrol)

    update_parser = subparsers.add_parser('update', add_help=True,
                                          parents=[db_cmd_parser, tag_cmd_parser],
                                          description='Update a tag in the database',
                                          help='Update a tag in the database')
    update_parser.set_defaults(func=update)

    lookup_parser = subparsers.add_parser('lookup', add_help=True,
                                          parents=[db_cmd_parser],
                                          description='Look up a tag in the database',
                                          help='Look up a tag in the database')
    lookup_parser.add_argument('tag', help='Tag ID')
    lookup_parser.set_defaults(func=lookup)

    label_parser = subparsers.add_parser('label', add_help=True,
                                          description='Generate a label image',
                                          help='Generate a label image')
    label_parser.add_argument('--dpi', help='Image DPI', type=int, default=300)
    label_parser.add_argument('--width_mm', help='Label width (mm)', type=int, default=89)
    label_parser.add_argument('--height_mm', help='Label height (mm)', type=int, default=36)
    label_parser.add_argument('--out', help='Output filename (default: preview)', default=None)
    label_parser.add_argument('lines', help='Text lines to put on label', nargs='*')
    label_parser.set_defaults(func=label)

    reader_parser = subparsers.add_parser('reader', add_help=True,
                                          description='Read a tag',
                                          help='Read a tag')
    reader_parser.add_argument('--port', help='Serial port for the tag reader', default='/dev/ttyUSB0')
    reader_parser.add_argument('--timeout', help='Timeout before giving up (seconds)', type=int, default=5)
    reader_parser.add_argument('--loop', help='Loop reading, otherwise exit after first read', action='store_true')
    reader_parser.add_argument('-d', '--database', help='sqlite3 database file')
    reader_parser.set_defaults(func=reader)

    ui_parser = subparsers.add_parser('ui', add_help=True,
                                          description='Run the badger UI',
                                          help='Run the badger UI')
    ui_parser.add_argument('--port', help='Serial port for the tag reader', default='/dev/ttyUSB0')
    ui_parser.add_argument('-d', '--database', help='sqlite3 database file', default=None)
    ui_parser.add_argument('--init', help="Initialise the database", action='store_true')
    ui_parser.add_argument('--sound', help="Run the sound thread", action='store_true')
    ui_parser.add_argument('--printer', help='Printer to use', choices=['display', 'display_r90', 'd450', 'vretti'], default='display')
    ui_parser.set_defaults(func=run_ui)

    args = parser.parse_args()

    try:
        args.func(args)
    except Exception as e:
        print("Error:", e)
        exit(1)


if __name__ == "__main__":
    main()
