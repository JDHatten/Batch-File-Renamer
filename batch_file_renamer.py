#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Batch File Renamer by JDHatten
    
    This script will rename one or more files either by adding new text or replacing text in the file names.
    Adding text can be placed at the start, end, or both sides of either matched text or the entire file name itself.
    Replacing text will replace the first or all instances of matched text in a file name including the extension.
    Renaming will just rename the entire file, but an iterating number or some other modify option should be used.
    
    Extra Features: 
    - Update any text based files that that have links to the renamed files to prevent broken links in whatever apps
      that use the those files.
    - Revert any file name changes by dropping the generated log file back into the script.
    - Sort groups of files before renaming using file meta data.

Usage:
    Simply drag and drop one or more files or directories onto the script. Create your own custom presets for more
    complex renaming tasks.

TODO:
    [] Rename directories too
    [DONE] Create a log of files renamed, time of completion, etc.
    [DONE] Loop script after finishing and ask to drop another file before just closing.
    [DONE] When replacing only one or more but not all matched strings start searching from the right/end of string.
    [DONE] Preset options
    [DONE] Display preset options and allow user to choose from cmd prompt
    [DONE] Better handling of overwriting files
    [DONE] Sort files in a particular way before renaming
    [DONE] Update one or more texted based files after a file has been renamed
    [DONE] Use more than one search/modify option at a time.
    [DONE] Option to revert name changes back to original names.
    [DONE] Ignore text option that will skip files that match the ignore text.
    [] Match file contents.
    [DONE] Match file meta data.
    [] Import separate settings and/or preset files.
    [] Special search and edits. Examples:
        [X] Find file names with a string then add another string at end of the file name.
        [X] Find file names with a string then rename entire file name and stop/return/end.
        [X] Find file names with a string then add another string specifically next to matched string.
        [X] Add an iterated number to file names.
        [X] Find specific file name extensions and only change (or add to) the extension
        [X] Generate random characters that can be added to file names.
        [X] A List of Strings to search for or add to file names.
        [] Make use of regular expressions.
'''


from datetime import datetime
try:
    import ffmpeg
    ffmpeg_installed = True
except ModuleNotFoundError:
    ffmpeg_installed = False
try:
    import filetype
    filetype_installed = True
except ModuleNotFoundError:
    filetype_installed = False
import math
import mimetypes
from pathlib import Path, PurePath
import os
import random
#import re
import sys
if sys.platform == "linux" or sys.platform == "linux2":
    print('Linux')
elif sys.platform == "darwin":
    print('OS X')
elif sys.platform == "win32":
    print('Windows')
    from ctypes import windll
import time as delay

#CUR_VERSION_STR = ".".join(map(str, sys.version_info[:3]))
MIN_VERSION = (3,8,0)
MIN_VERSION_STR = '.'.join([str(n) for n in MIN_VERSION])

### EDIT_DETAILS Keys
EDIT_TYPE = 0           # The type of edit to make on a file name: ADD text, REPLACE text or RENAME entire file name. [Required]
MATCH_TEXT = 1          # The text to search for and match before renaming a file name.
IGNORE_TEXT = 2         # The text to search for and if found in a file name skip that file renaming, effectively renaming every other file not matched.
MATCH_FILE_CONTENTS = 3 ## TODO: Match text in the contents of a file before renaming it.
MATCH_FILE_META = 4     # Match specific meta data from a file before renaming it.
INSERT_TEXT = 5         # The text used in renaming files. This can be static text or dynamic text that changes depending on the OPTIONS used. [Required]
SOFT_RENAME_LIMIT = 6   # A soft limit stops renaming files once hit and resets after changing to a new sub-directory, directory drop, or group of individual files dropped.
HARD_RENAME_LIMIT = 7   # A hard limit stops renaming files once hit and ends all further renaming tasks.
LINKED_FILES = 8        # Full file path to text based files that that have links to the renamed files to prevent broken links in whatever apps that use the those files.
INCLUDE_SUB_DIRS = 9    # When a directory (folder) is dropped and searched through also search any sub-directories as well for files to rename.
PRESORT_FILES = 10      # Before renaming any group of files, sort them using the file's meta data.
TRACKED_DATA = 99       # Internal use only, do not use.

### EDIT_TYPE Options
ADD = 0
REPLACE = 1
RENAME = 2

### Search and Modify Keys
TEXT = 0
META = 1
OPTIONS = 2
PLACEMENT = 3

# TRACKED_DATA
FILES_REVIEWED = 0
FILES_RENAMED = 1
DIRECTORY_FILES_RENAMED = 2
INDIVIDUAL_FILES_RENAMED = 3
INDIVIDUAL_FILE_GROUP = 4
FILE_NAME_COUNT = 5
FILE_NAME_COUNT_LIMIT = 6
CURRENT_LIST_INDEX = 7
CURRENT_FILE_NAME = 8
CURRENT_FILE_META = 8
CURRENT_FILE_RENAME = 9
USED_RANDOM_CHARS = 10
SKIPPED_FILES = 11
SKIP_WARNINGS = 12
LOG_DATA = 13
ORG_FILE_PATHS = 20
NEW_FILE_PATHS = 21
LINKED_FILES_UPDATED = 22
START_TIME = 23
END_TIME = 24

AMOUNT = 0
INDEX_POINTER = 0
LIMIT = 1
UPDATE_COUNT = 1
UPDATE_LIMIT = 1
UPDATE_SKIP = 1
FULL_AMOUNT = 2

# Constants
ALL = 999
NONE = -1
NO = -1
NO_LIMIT = -1
CANCEL = 0
OK = 1
YES = 1
TRY_AGAIN = 2
SKIP = 3
CONTINUE = 3
SAME_NAME = 4
SAME = 4
NO_CHANGE = 4
LOWER = 101
UPPER = 110
LOWER_AND_UPPER = 111

# Dynamic Text
STARTING_TEXT = 0
DYNAMIC_TEXT = 1
ENDING_TEXT = 2

STARTING_COUNT = 0
ENDING_COUNT = 1

### File Meta Data
FILE_META_PATH = 0                  # DATA: 'Text'
FILE_META_SIZE = 1                  # GB/MB/KB/BYTES : Number
FILE_META_ACCESS = 2                # YEAR/MONTH/... : Number
FILE_META_MODIFY = 3                # YEAR/MONTH/... : Number
FILE_META_CREATE = 4                # YEAR/MONTH/... : Number
FILE_META_METADATA = 4              # YEAR/MONTH/... : Number
FILE_META_TYPE = 5                  # DATA : File Types (MIME)
FILE_META_MIME = 6                  # DATA : 'Text'
FILE_META_FORMAT = 7                # DATA : 'Text'
FILE_META_FORMAT_LONG = 8           # DATA : 'Text'
FILE_META_HEIGHT = 9                # DATA : Number
FILE_META_WIDTH = 10                # DATA : Number
FILE_META_LENGTH = 11               # HOUR/MINUTE/... : Number
FILE_META_BIT_DEPTH = 12            # DATA : Number
FILE_META_RATE = 13                 # DATA : Number
FILE_META_VIDEO_BITRATE = 14        # DATA : Number
FILE_META_VIDEO_FRAME_RATE = 15     # DATA : Number
FILE_META_AUDIO_BITRATE = 16        # DATA : Number
FILE_META_AUDIO_SAMPLE_RATE = 17    # DATA : Number
FILE_META_AUDIO_CHANNELS = 18       # DATA : Number
FILE_META_AUDIO_CHANNEL_LAYOUT = 19 # DATA : 'Text'
FILE_META_AUDIO_TITLE = 20          # DATA : 'Text'
FILE_META_AUDIO_ALBUM = 21          # DATA : 'Text'
FILE_META_AUDIO_ARTIST = 22         # DATA : 'Text'
FILE_META_AUDIO_YEAR = 23           # YEAR : Number
FILE_META_AUDIO_GENRE = 24          # DATA : 'Text'
FILE_META_AUDIO_PUBLISHER = 25      # DATA : 'Text'
FILE_META_AUDIO_TRACK = 26          # DATA : Number

### META_MATCH
EXACT_MATCH = 0         # An exact perfect match of a entire piece of text or number.
LOOSE_MATCH = 1         ## TODO: A close but not exact match. If text, match any part of a larger piece of text; if a number, match any number wihtin a 5% range.
SKIP_EXACT_MATCH = 2    ## TODO: 
SKIP_LOOSE_MATCH = 2    ## TODO: 
                        # Note: If using a list and SAME_MATCH_INDEX take note of the order of skipped data. For example if you always want to skip matched data, then make sure its added first.
LESS_THAN = 3           # A number
MORE_THAN = 4           # A number
WITHIN_THE_PAST = 3     # Date and/or time
OLDER_THAN = 4          # Date and/or time

### File Types (MIME)
TYPE_APPLICATION = 0    # This is basically everything not categorized below.
TYPE_AUDIO = 2          # Some examples files: .aac .mp3 .ogg
TYPE_FONT = 4           # Some examples files: .otf .ttf .woff
TYPE_IMAGE = 5          # Some examples files: .bmp .jpg .png
TYPE_MESSAGE = 6        # Some examples files: .cl .u8hdr .wsc  (Uncommon)
TYPE_MODEL = 7          # Some examples files: .obj .usd .x3dv  (Uncommon)
TYPE_MULTIPART = 8      # Some examples files: .vpm .bmed       (Uncommon)
TYPE_TEXT = 9           # Some examples files: .cvs .html .txt
TYPE_VIDEO = 10         # Some examples files: .flv .mp4 .mpeg

### Categorized Application Types (MIME) (not a complete list)
TYPE_ARCHIVE = 1        # Some examples files: .7z .rar .zip
TYPE_DOCUMENT = 3       # Some examples files: .doc .potx .xlsx

### Date and Time
YEAR = 200
MONTH = 201
DAY = 202
HOUR = 203
MINUTE = 204
SECOND = 205
MILLISECOND = 206
MICROSECOND = 206
TIMESTAMP = 207

### File Sizes
BYTES = 300
KB = 301
MB = 302
GB = 303
IN_BYTES_ONLY = 304

# Actual File Sizes
KILOBYTE = 1024
MEGABYTE = 1024 * 1024
GIGABYTE = 1024 * 1024 * 1024

### Other
DATA = 400


### Search Options
MATCH_CASE = 0          # Case sensitive search. [Default]
NO_MATCH_CASE = 1       # Not a case sensitive search.
SEARCH_FROM_RIGHT = 2   # Start searching from right to left.
MATCH_LIMIT = 3         # Matches to make (or text inserts) per file name. Default: (MATCH_LIMIT, NO_LIMIT)
SAME_MATCH_INDEX = 4    # When a match is made from the "MATCH_TEXT List" use the same index when choosing text from the "INSERT_TEXT List".
                        # Useful when making a long lists of specific files to find and rename.
                        # Note: Use only one per preset. Also if list (match/insert) sizes differ then you may get undesirable results.

### Search or Modify Options
EXTENSION = 10          # ADD (to the END of the file name plus extension) REPLACE (just the extension) or RENAME (the entire file name if a '.' is in text).
                        # Use EXTENSION in search options for matching "only" the exact file extension (.doc != .docx).
                        # Using EXTENSION in modify options means only the extension will be replaced or added to (END), unless RENAME where the entire file name may be rewritten.
                        # Note: You don't need to use EXTENSION in all cases where you wish to match or modify the extension.
REGEX = 11              ## TODO: Regular Expressions

### Modify Options
COUNT = 20              # Iterate a number that is added to a file name. (Starting Number, Ending Number) Ending number is optional.
                        # NOTE: Resets after each directory change.
COUNT_TO = 21           # Max amount of renames to make before stopping. Similar to COUNT's ending number without adding an iterating number to a file name.
MINIMUM_DIGITS = 23     # Minimum digits for any dynamic text used, i.e. 3 = 003
RANDOM_NUMBERS = 24     # Generate random numbers.              (All random generators can be used together.)
RANDOM_LETTERS = 25     # Generate random letters.              (Edit which characters randomly selected in below varaibles "list_leters")
RANDOM_SPECIALS = 26    # Generate random special characters.   ('text', Random String Length, 'text')
RANDOM_OTHER = 27       # Generate random other (uncommon, unique, or foreign) characters.
RANDOM_SEED = 28        # Starting seed number to use in random generators. Default: (RANDOM_SEED, None)
#REPEAT_TEXT_LIST = 29   # Once the end of a text list is reached, repeat it.  Text should be dynamic, i.e. COUNT, RANDOM_NUMBERS, etc.
NO_REPEAT_TEXT_LIST = 29# Once the end of a text list is reached, do not repeat it. List size will become a soft rename limit. Note: SAME_MATCH_INDEX takes precedent.
INSERT_META_DATA = 30   ## TODO: ('Text', TIME/HEIGHT/WIDTH/LENGTH/FILE_SIZE?, 'Text')

### Placement Options
START = 40              # Place at the start of...
LEFT = 40               # Place at the left of...
END = 41                # Place at the end of... [Default]
RIGHT = 41              # Place at the right of...
BOTH = 42               # Place at both sides of...
BOTH_ENDS = 42          # Place at both ends of...

OF_FILE_NAME = 50       # Placed at file name minus extension [Default]
OF_MATCH = 51           # Placed at one or more matches found

### Sort Options        ## TODO: add more sorting options, image sizes, format/extension, video length, etc.
ASCENDING = 60          # 0-9, A-Z [Default]
DESCENDING = 61         # 9-0, Z-A
ALPHABETICALLY = 62     # File name [Default]
FILE_SIZE = 63          # File size in bytes
DATE_ACCESSED = 64      # Date file last opened.
DATE_MODIFIED = 65      # Date file last changed.
DATE_CREATED = 66       # Date file created. (Windows Only)
DATE_META_MODIFIED = 66 # Date file's meta data last updated. (UNIX)


### Edit characters used in random generators. You may also choose to use an even amount/weight
### of characters in each list when using multiple random lists.
### Note: Some characters can't be used in file names and are not included here.
list_numbers = list('1234567890')
list_leters = list('abcdefghijklmnopqrstuvwxyz')
list_capital_leters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
list_special = list("~`!@#$%^&()-_=+[{]};',.") # ASCII
list_other = list("¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ") # UTF-8 Unicode
#list_other = list("") # Add special foreign language or other characters not included above. Or use this as a custom list of random characters.
even_weighted_random_char_list = True   # If more than one random generator list used.
no_repeat_random_chars = False          # Ex. True = 13254, False = 13223
reset_random_seed = True                # Reset random seed after each directory change.
letter_cases = LOWER_AND_UPPER          # Use list_leters "and/or" list_capital_leters

### Create a log file for each rename task ran, and include edit details or preset used.
### Directory name can be relative to this script or an absolute path.
### The amount of log files created can be limited from 0 to NO_LIMIT.
### NOTE: You can revert file name changes by dropping log files back into the script.
###       Those log file names must match these name variables though.
create_log_file = True
log_edit_details = True
log_dir_name = 'Logs of File Renames'
log_file_limit = 10
log_file_name_suffix = '__log.txt'

### If False the script will just run after file(s) dropped with current selected preset and quit.
### If True the script will ask for a selected preset and ask for additional file drops after initial drop.
loop = True

### Presets provide complex renaming possibilities and can be customized to your needs.
### Select the default preset to use here. Can be changed again once script is running.
selected_preset = 24

preset0 = {         # Defaults
  EDIT_TYPE         : ADD,      # ADD or REPLACE or RENAME (entire file name, minus extension) [Required]
  MATCH_TEXT        : '',       # 'Text' to Find  -OR- Dict{ TEXT : 'Text', OPTIONS : Search Options }
  IGNORE_TEXT       : None,     # 'Text' to Find and Skip -OR- Dict{ TEXT : 'Text', OPTIONS : Search Options }
  MATCH_FILE_META   : None,     # { 'Specific Meta' : 'How To Match', 'What To Match' : 'Data', ... } -OR- Dict{ META : [ {}, {}, ... ], OPTIONS : Search Options }
  INSERT_TEXT       : '',       # 'Text' to Add or Replace -OR- Dict{ TEXT : 'Text', OPTIONS : Modify Options, PLACEMENT : (PLACE, OF_) } [TEXT Required]
  SOFT_RENAME_LIMIT : NO_LIMIT, # Max number of file renames to make per directory or group of individual files dropped. (0 to NO_LIMIT)
  HARD_RENAME_LIMIT : NO_LIMIT, # Hard limit on how many files to rename each time script is ran, no matter how many directories or group of individual files dropped. (0 to NO_LIMIT)
  LINKED_FILES      : [],       # File Paths of files that need to be updated of any file name changes to prevent broken links in apps. (Use double slashes "//")
  INCLUDE_SUB_DIRS  : False,    # Search Sub-Directories (True or False)
  PRESORT_FILES     : None      # Sort before renaming files.  Dict{ Sort Option : ASCENDING or DESCENDING }
}                               # Note: Dynamic Text Format = Tuple('Starting Text', Integer/Tuple, 'Ending Text') -OR- a List['Text',...]
preset1 = {
  EDIT_TYPE         : REPLACE,
  MATCH_TEXT        : { TEXT : '(Text)', OPTIONS : [ (MATCH_LIMIT, 1), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT       : { TEXT : '[Text]' },
  INCLUDE_SUB_DIRS  : True
}
preset2 = {
  EDIT_TYPE         : REPLACE,
  MATCH_TEXT        : '123',
  INSERT_TEXT       : 'abc',
  INCLUDE_SUB_DIRS  : False
}
preset3 = {
  EDIT_TYPE         : ADD,
  INSERT_TEXT       : { TEXT : '-W', PLACEMENT : END },
  INCLUDE_SUB_DIRS  : True
}
preset4 = {
  EDIT_TYPE         : RENAME,
  MATCH_TEXT        : { TEXT : '', OPTIONS : NO_MATCH_CASE },
  INSERT_TEXT       : { TEXT : ('TextTextText-[', (1,7), ']'), OPTIONS : COUNT },
  INCLUDE_SUB_DIRS  : True
}
preset5 = {
  EDIT_TYPE         : ADD,
  MATCH_TEXT        : { TEXT : 'Text', OPTIONS : MATCH_CASE },
  INSERT_TEXT       : { TEXT : ('--(', 1, ')'), OPTIONS : COUNT, PLACEMENT : END },
  INCLUDE_SUB_DIRS  : True
}
preset6 = {
  EDIT_TYPE         : REPLACE,
  MATCH_TEXT        : { TEXT : 'Tex', OPTIONS : [ MATCH_CASE, (MATCH_LIMIT, 4), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT       : { TEXT : ('(', 0, ')'), OPTIONS : COUNT },
  INCLUDE_SUB_DIRS  : False
}
preset7 = {
  EDIT_TYPE         : REPLACE,
  MATCH_TEXT        : { TEXT : '.rar', OPTIONS : [ NO_MATCH_CASE, EXTENSION ] },
  INSERT_TEXT       : { TEXT : '.txt', OPTIONS : EXTENSION },
}
preset8 = {
  EDIT_TYPE         : ADD,
  MATCH_TEXT        : { TEXT : '.bin', OPTIONS : [EXTENSION] },
  INSERT_TEXT       : { TEXT : '.bin', OPTIONS : [], PLACEMENT : ( END, OF_MATCH ) },
}
preset9 = {
  EDIT_TYPE         : REPLACE,
  MATCH_TEXT        : { TEXT        : 'text',
                        OPTIONS     : [ MATCH_CASE, (MATCH_LIMIT, 2), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT       : { TEXT        : 'XXX',
                        PLACEMENT   : ( BOTH_ENDS, OF_MATCH ) },
}
preset10 = {
  EDIT_TYPE         : ADD,
  MATCH_TEXT        : { TEXT : 'text', OPTIONS : [ NO_MATCH_CASE, (MATCH_LIMIT, 1), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT       : { TEXT : ('-XXX', 3), OPTIONS : COUNT_TO, PLACEMENT : (END, OF_MATCH) },
}
preset11 = {
  EDIT_TYPE         : RENAME,
  MATCH_TEXT        : { TEXT : '', OPTIONS : NO_MATCH_CASE },
  INSERT_TEXT       : { TEXT : ('Text-[', (1,7), ']'), OPTIONS : COUNT },
  LINKED_FILES      : [ 'V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt' ],
  PRESORT_FILES     : { DATE_MODIFIED : DESCENDING }
}
preset12 = {
  EDIT_TYPE         : ADD,
  INSERT_TEXT       : { TEXT : ' (U)', PLACEMENT : END },
  SOFT_RENAME_LIMIT : 3,
  HARD_RENAME_LIMIT : 5,
  LINKED_FILES      : [ 'V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt' ],
  INCLUDE_SUB_DIRS  : True
}
preset13 = {
  EDIT_TYPE         : REPLACE,
  MATCH_TEXT        : { TEXT : ' (U)', OPTIONS : [ MATCH_CASE, (MATCH_LIMIT, 10), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT       : { TEXT : ' (u)' },
  LINKED_FILES      : [ 'V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt' ],
  INCLUDE_SUB_DIRS  : True
}
preset14 = {
  EDIT_TYPE         : RENAME,
  MATCH_TEXT        : { TEXT        : ['[1].txt','[2].txt','[3].txt','[4].txt','[5].txt'],
                        OPTIONS     : [MATCH_CASE, SAME_MATCH_INDEX] },
  INSERT_TEXT       : { TEXT        : ['NewName-01','ThisName-02','AName-03','NotAName-04','NameName-05'],
                        OPTIONS     : None },
  LINKED_FILES      : [ 'V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt' ],
}
preset15 = {
  EDIT_TYPE         : ADD,
  MATCH_TEXT        : { TEXT        : [ 'text', 'name' ],
                        OPTIONS     : [ NO_MATCH_CASE, (MATCH_LIMIT, 3), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT       : { TEXT        : [ ('-(', (1,2), ')-'), ('--[', (1,2), ']--') ],
                        OPTIONS     : [ COUNT, NO_REPEAT_TEXT_LIST ],
                        PLACEMENT   : ( END, OF_MATCH ) },
  SOFT_RENAME_LIMIT : NO_LIMIT,
  LINKED_FILES      : [ 'V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt' ],
}
preset16 = {
  EDIT_TYPE         : REPLACE,
  MATCH_TEXT        : { TEXT        : [ '.rar', '.zip', '.7' ],
                        OPTIONS     : [ NO_MATCH_CASE, EXTENSION, SAME_MATCH_INDEX ] },
  INSERT_TEXT       : { TEXT        : [ ('.r', (0), ''), ('.z', (0), ''), '.7z' ],
                        OPTIONS     : [ COUNT, EXTENSION, (MINIMUM_DIGITS, 2) ] },
  SOFT_RENAME_LIMIT : NO_LIMIT,
}
preset17 = {
  EDIT_TYPE         : RENAME,
  MATCH_TEXT        : { TEXT : '.rar', OPTIONS : [ NO_MATCH_CASE, EXTENSION ] },
  INSERT_TEXT       : { TEXT : ('WinRAR File Part-',1,'.rar'), OPTIONS : [ EXTENSION, COUNT] },
}
preset18 = {
  EDIT_TYPE         : ADD, # (This is the desired behavior when) Using ADD...
  MATCH_TEXT        : { TEXT : '.rar', OPTIONS : [ NO_MATCH_CASE, EXTENSION ] }, # With EXTENSION search option...
  INSERT_TEXT       : { TEXT : '-123-', OPTIONS : None, PLACEMENT : (START, OF_MATCH) }, # OF_MATCH is ignored, only OF_FILE_NAME is used
}
preset19 = {
  EDIT_TYPE         : ADD,
  MATCH_TEXT        : { TEXT        : [ '.jpg', '.png' ],
                        OPTIONS     : [ NO_MATCH_CASE, EXTENSION, SAME_MATCH_INDEX ] },
  INSERT_TEXT       : { TEXT        : [ ('-', (1,200), ''), ('-', (1000,2200), '') ],
                        OPTIONS     : [ COUNT, (MINIMUM_DIGITS, 4) ],
                        PLACEMENT   : ( END, OF_FILE_NAME ) },
  LINKED_FILES      : [ 'V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt' ],
}
preset20 = {
  EDIT_TYPE         : ADD,
  MATCH_TEXT        : { TEXT        : 'tXt',
                        OPTIONS     : [ NO_MATCH_CASE, EXTENSION ] },
  IGNORE_TEXT       : { TEXT        : [ 'skIp', 'fIle' ],
                        OPTIONS     : [ NO_MATCH_CASE ] },
  INSERT_TEXT       : { TEXT        : ('-', (1,20), ''),
                        OPTIONS     : [ COUNT, (MINIMUM_DIGITS, 4) ],
                        PLACEMENT   : ( END, OF_FILE_NAME ) }
}
preset21 = {
  EDIT_TYPE         : REPLACE,
  MATCH_TEXT        : { TEXT        : 'Text',
                        OPTIONS     : [ MATCH_CASE ] },
  IGNORE_TEXT       : 'skIp',
  INSERT_TEXT       : { TEXT        : ('-', (10,20), ''),
                        OPTIONS     : [ COUNT ] }
}
preset22 = {
  EDIT_TYPE         : RENAME,
  MATCH_TEXT        : { TEXT        : ['tXt'],
                        OPTIONS     : [ NO_MATCH_CASE, EXTENSION ] },
  INSERT_TEXT       : { TEXT        : [ ('RandomS-', 4, ''), ('RandomL-[', (7), ']') ],
                        OPTIONS     : [ RANDOM_NUMBERS, RANDOM_LETTERS, (RANDOM_SEED, None), NO_REPEAT_TEXT_LIST ] }
}
preset23 = {
  EDIT_TYPE         : RENAME,
  MATCH_TEXT        : { TEXT        : ['tXt'],
                        OPTIONS     : [ NO_MATCH_CASE, EXTENSION ] },
  MATCH_FILE_META   : { META        : [ { FILE_META_MODIFY : EXACT_MATCH, YEAR : 2022, MONTH : 8, DAY : 3 },
                                        { FILE_META_CREATE : EXACT_MATCH, YEAR : 2022, MONTH : 8, DAY : 31 },
                                        { FILE_META_CREATE : WITHIN_THE_PAST,  YEAR : 1 },
                                        { FILE_META_SIZE   : LESS_THAN, KB : 7, BYTES : 219 } ],
                        OPTIONS     : [ SAME_MATCH_INDEX ] },
  #MATCH_FILE_META   : { FILE_META_CREATE : WITHIN_THE_PAST,  YEAR : 1 },
  INSERT_TEXT       : { TEXT        : [ ('RandomS-', 4, ''), ('RandomL-[', (7), ']') ],
                        OPTIONS     : [ RANDOM_NUMBERS, RANDOM_LETTERS, (RANDOM_SEED, None) ] }
}
preset24 = {
  EDIT_TYPE         : RENAME,
  MATCH_FILE_META   : { META        : [ { FILE_META_TYPE : EXACT_MATCH, DATA : TYPE_VIDEO },
                                        { FILE_META_FORMAT : LOOSE_MATCH, DATA : 'h264' },
                                        { FILE_META_HEIGHT : EXACT_MATCH,  DATA : 720 },
                                        { FILE_META_VIDEO_BITRATE : LOOSE_MATCH, DATA : 1000 } ],
                        OPTIONS     : [ NO_MATCH_CASE ] }, ## TODO Case Matches
  INSERT_TEXT       : { TEXT        : [ ('Video-(', 4, ')'), ('Video-[', (7), ']') ],
                        OPTIONS     : [ RANDOM_NUMBERS, RANDOM_LETTERS, NO_REPEAT_TEXT_LIST ] }
}
### Add any newly created presets to this preset_options List.
preset_options = [preset0,preset1,preset2,preset3,preset4,preset5,preset6,preset7,preset8,preset9,preset10,
                  preset11,preset12,preset13,preset14,preset15,preset16,preset17,preset18,preset19,preset20,
                  preset21,preset22,preset23,preset24]

### Show/Print tracking data and maybe some other variables.
### Log data is separated out as it can grow quite large and take up a lot of space in prompt.
debug = False
show_log_data = False


### Check for any use of excluded or illegal file name characters.
###     (edit_details) All the details on how to proceed with the file name edits.
###     --> Returns a [Boolean] 
def illegalCharacterCheck(edit_details):
    
    illegal_characters_found = False
    illegal_characters = list('\\|:"<>/?')
    
    match_text = getText(edit_details.get(MATCH_TEXT))
    ignore_text = getText(edit_details.get(IGNORE_TEXT))
    insert_text = getText(edit_details.get(INSERT_TEXT))
    before = ', ...'
    after = '..., '
    
    for char in illegal_characters:
        
        i = -1
        for text in match_text:
            i += 1
            
            if char in text:
                if not illegal_characters_found: print('')
                text_mistake = '\'' + str(text) + '\''
                if i > 0: text_mistake = after + text_mistake
                if i < len(match_text): text_mistake += before
                print('Found  %s  in  MATCH_TEXT  : [ %s ]' % (char, text_mistake))
                illegal_characters_found = True
        
        i = -1
        for text in ignore_text:
            i += 1
            
            if char in text:
                if not illegal_characters_found: print('')
                text_mistake = '\'' + str(text) + '\''
                if i > 0: text_mistake = after + text_mistake
                if i < len(ignore_text): text_mistake += before
                print('Found  %s  in  IGNORE_TEXT : [ %s ]' % (char, text_mistake))
                illegal_characters_found = True
        
        i = -1
        for text in insert_text:
            i += 1
            
            if type(text) == tuple:
                
                text_mistake = str(text)
                if i > 0: text_mistake = after + text_mistake
                if i < len(insert_text): text_mistake += before
                
                if char in text[STARTING_TEXT]:
                    if not illegal_characters_found: print('')
                    print('Found  %s  in  INSERT_TEXT : [ %s ]' % (char, text_mistake))
                    illegal_characters_found = True
                
                if len(text) > 2 and char in text[ENDING_TEXT]:
                    if not illegal_characters_found: print('')
                    print('Found  %s  in  INSERT_TEXT : [ %s ]' % (char, text_mistake))
                    illegal_characters_found = True
            
            else:
                if char in text:
                    if not illegal_characters_found: print('')
                    text_mistake = '\'' + str(text) + '\''
                    if i > 0: text_mistake = after + text_mistake
                    if i < len(insert_text): text_mistake += before
                    print('Found  %s  in  INSERT_TEXT : [ %s ]' % (char, text_mistake))
                    illegal_characters_found = True
    
    if illegal_characters_found:
        print('\nWARNING: Excluded or illegal file name characters were found in [ Preset #%s ].' % selected_preset)
        print('These characters can not be used in file names and need to be removed before this preset can be used.')
    
    return illegal_characters_found


### Display one or all file rename preset options.
###     (preset) A List of file rename presets. Or a single preset Dictionary.
###     (number) Only show specific preset in List.
###     (log_preset) Return preset in a List for use in log file.
###     --> Returns a [None] 
def displayPreset(presets, number = -1, log_preset = False):
    log_lines = [] if log_preset else None
    
    if type(presets) == list and number == -1:
        for ps in presets:
            number += 1
            if not log_preset: print('\nPreset %s' % str(number))
            for option, mod in ps.items():
                opt_str = intToStrText(option, 'Preset Options')
                mod_str = ''
                if type(mod) == dict:
                    for key, value in mod.items():
                        mod_str += intToStrText(key, value, option) + '  '
                else:
                    mod_str = intToStrText(None, mod, option)
                if not log_preset: print('    %s : %s' % (opt_str, mod_str))
            
            if math.remainder(number, 5) == 0 and number != 0:
                input('Show More...')
    
    else:
        if type(presets) == dict:
            if not log_preset: print('\nCurrent Preset In Use')
        else:
            presets = presets[number]
            if not log_preset: print('\nCurrent Preset #%s' % str(number))
        for option, mod in presets.items():
            opt_str = intToStrText(option, 'Preset Options')
            mod_str = ''
            if type(mod) == dict:
                for key, value in mod.items():
                    mod_str += intToStrText(key, value, option) + '  '
            else:
                mod_str = intToStrText(None, mod, option)
            if log_preset:
                if option != TRACKED_DATA:
                    log_lines.append('    %s : %s' % (opt_str, mod_str))
            else:
                print('    %s : %s' % (opt_str, mod_str))
    
    if not log_preset: print('\n')
    
    return log_lines


### Starting file rename procedures using the edit details.
###     (files_meta_data) A List of directories and/or files with meta data included (although not really used outside of sorting).
###     (edit_details) A Dictionary of all the details on how to proceed with the file name edits.
###                    Dictionary[EDIT_TYPE, MATCH_TEXT, INSERT_TEXT, SOFT_RENAME_LIMIT, HARD_RENAME_LIMIT, LINKED_FILES, INCLUDE_SUB_DIRS, PRESORT_FILES]
###     (include_sub_dirs) Search sub-directories for more files.  Boolean(True) or Boolean(False)
###     --> Returns a [Dictionary] edit_details
def startingFileRenameProcedure(files_meta_data, edit_details, include_sub_dirs = False):
    
    if illegalCharacterCheck(edit_details):
        return edit_details # Full Stop
    
    edit_details_copy = edit_details
    
    # Keep tracked data from previous drops (Note: Not being used anymore, but will still return default values so keeping it in.)
    files_reviewed = getTrackedData(edit_details_copy, FILES_REVIEWED, [AMOUNT])
    files_renamed = getTrackedData(edit_details_copy, FILES_RENAMED, [AMOUNT])
    individual_files_renamed = getTrackedData(edit_details_copy, INDIVIDUAL_FILES_RENAMED, [AMOUNT])
    skip_warnings = getTrackedData(edit_details_copy, SKIP_WARNINGS)
    log_data = getTrackedData(edit_details_copy, LOG_DATA)
    
    # Set the seed for random character generators
    random_seed = getOptions(edit_details_copy[INSERT_TEXT], RANDOM_SEED, None)
    random.seed(random_seed)
    
    for meta in files_meta_data:
        
        # Directories
        if type(meta) == tuple:
            
            dir_path = meta[FILE_META_PATH]
            
            hard_limit_hit = False
            
            for root, dirs, files in os.walk(dir_path):
                
                print('\n-Root: %s\n' % (root))
                
                #for dir in dirs:
                    #print('--Directory: [ %s ]' % (dir))
                
                # Sort Files
                files_meta = getFileMetaData(files, edit_details.get(PRESORT_FILES, None), root)
                
                # Prepare Edit Details and add Tracker
                if not log_data:
                    skip_warnings = getTrackedData(edit_details_copy, SKIP_WARNINGS)
                    log_data = getTrackedData(edit_details_copy, LOG_DATA)
                edit_details_copy = copyEditDetails(edit_details, files_reviewed, files_renamed, individual_files_renamed, False, skip_warnings, log_data)
                #if debug: displayPreset(edit_details_copy)
                
                for file in files_meta:
                    #print('--File: [ %s ]' % (file[FILE_META_PATH].name))
                    
                    hard_rename_limit = getTrackedData(edit_details_copy, FILES_REVIEWED, [LIMIT])
                    soft_rename_limit = getTrackedData(edit_details_copy, DIRECTORY_FILES_RENAMED, [LIMIT])
                    directory_files_renamed = getTrackedData(edit_details_copy, DIRECTORY_FILES_RENAMED, [AMOUNT])
                    all_files_renamed = getTrackedData(edit_details_copy, FILES_RENAMED, [FULL_AMOUNT])
                    
                    if hard_rename_limit != NO_LIMIT and all_files_renamed >= hard_rename_limit:
                        hard_limit_hit = True
                        break # Hard rename limit hit, stop and do not move on to the next directory.
                    if soft_rename_limit != NO_LIMIT and directory_files_renamed >= soft_rename_limit:
                        break # Soft rename limit hit, stop and move on to next directory.
                    if allCountLimitsHitCheck(getTrackedData(edit_details_copy)):
                        break # File count limit hit, stop and move on to next directory.
                    
                    file_path = Path(file[FILE_META_PATH])
                    edit_details_copy = updateTrackedData(edit_details_copy, { CURRENT_FILE_META : file, CURRENT_FILE_RENAME : file[FILE_META_PATH].name })
                    
                    edit_details_copy = createNewFileName(file_path, edit_details_copy)
                    edit_details_copy = updateTrackedData(edit_details_copy, { FILES_REVIEWED : +1 })
                    if debug: displayPreset(edit_details_copy)
                
                # Save some tracked data for next directory loop or individually grouped files.
                files_reviewed = getTrackedData(edit_details_copy, FILES_REVIEWED, [AMOUNT])
                files_renamed += getTrackedData(edit_details_copy, DIRECTORY_FILES_RENAMED, [AMOUNT])
                skip_warnings = getTrackedData(edit_details_copy, SKIP_WARNINGS)
                log_data = getTrackedData(edit_details_copy, LOG_DATA)
                
                if not include_sub_dirs or hard_limit_hit:
                    break
        
        # Individually Grouped Files
        elif type(meta) == list:
            
            # Prepare Edit Details and add Tracker
            edit_details_copy = copyEditDetails(edit_details, files_reviewed, files_renamed, individual_files_renamed, True, skip_warnings, log_data)
            
            limit_reached = False
            hard_rename_limit = getTrackedData(edit_details_copy, FILES_REVIEWED, [LIMIT])
            soft_rename_limit = getTrackedData(edit_details_copy, INDIVIDUAL_FILES_RENAMED, [LIMIT])
            
            for file in meta:
            
                file_path = file[FILE_META_PATH]
                edit_details_copy = updateTrackedData(edit_details_copy, { CURRENT_FILE_META : file, CURRENT_FILE_RENAME : file[FILE_META_PATH].name })
                
                individual_files_renamed = getTrackedData(edit_details_copy, INDIVIDUAL_FILES_RENAMED, [AMOUNT])
                all_files_renamed = getTrackedData(edit_details_copy, FILES_RENAMED, [AMOUNT])
                
                if hard_rename_limit != NO_LIMIT and all_files_renamed >= hard_rename_limit:
                    limit_reached = True # Hard or soft rename limit hit (whichever is first for groups of individual files)
                if soft_rename_limit != NO_LIMIT and individual_files_renamed >= soft_rename_limit:
                    limit_reached = True # Hard or soft rename limit hit (whichever is first for groups of individual files)
                if allCountLimitsHitCheck(getTrackedData(edit_details_copy)):
                    limit_reached = True # File count limit hit
                
                if not limit_reached:
                    edit_details_copy = createNewFileName(file_path, edit_details_copy)
                    edit_details_copy = updateTrackedData(edit_details_copy, { FILES_REVIEWED : +1 })
                
                if debug: displayPreset(edit_details_copy)
    
    edit_details_copy = updateTrackedData(edit_details_copy, { END_TIME : datetime.now().timestamp() })
    
    return edit_details_copy


### Build a list of files and edit details using a log file (generated by this script) for the purpose of reverting the renames recored in that log file.
###     (log_file) Path to a log file.
###     --> Returns a [List] and [Dictionary]
def getRenameRevertFilesAndEditDetails(log_file):
    
    file_list = []
    edit_details = {
        EDIT_TYPE         : RENAME,
        MATCH_TEXT        : { TEXT : [], OPTIONS : [MATCH_CASE, SAME_MATCH_INDEX] },
        INSERT_TEXT       : { TEXT : [], OPTIONS : [EXTENSION] },
        LINKED_FILES      : []
    }
    
    try:
        text_encoding = 'ascii'
        read_log_file = log_file[FILE_META_PATH].read_text(encoding=text_encoding)
    except:
        try:
            text_encoding = 'utf-8'
            read_log_file = log_file[FILE_META_PATH].read_text(encoding=text_encoding)
        except:
            print('Failed to open log file: [ %s ]' % log_file[FILE_META_PATH])
            print('Posible text encoding issue. Script only supports ascii and utf-8 text encoding.')
            return False
    
    log_file_lines = read_log_file.splitlines()
    i = -1
    n = 1
    eof = len(log_file_lines)
    root_path = ''
    
    while i < eof:
        i += 1
        line = log_file_lines[i]
        
        linked_files_index = line.find('Linked Files Updated:')
        if linked_files_index > -1: # Found
            
            while i < eof:
                
                i += 1
                line = log_file_lines[i]
                num = str(n)+'. '
                num_index_end = len(num)
                
                link_index = line.find(num)
                if link_index > -1: # Found
                
                    edit_details[LINKED_FILES].append(line[link_index+num_index_end:])
                    n += 1
                
                else:
                    
                    i += 1
                    while i < eof:
                        line = log_file_lines[i]
                        
                        root_index = line.find('Root Path: ')
                        if root_index > -1: # Found
                            
                            root_path = line[root_index+11:]
                            
                            i += 1
                            file_found = True
                            while file_found:
                            
                                line = log_file_lines[i]
                                if line.find('--> ') > -1: # Found
                                    
                                    file = line[4:].split(' --> ')
                                    file_new = file[1].split('  | ')[0]
                                    file_org = file[0]
                                    edit_details[MATCH_TEXT][TEXT].append( file_new )
                                    edit_details[INSERT_TEXT][TEXT].append( file_org )
                                    file_list.append( Path(PurePath().joinpath(root_path, file_new)) )
                                    i += 1
                                
                                else:
                                    file_found = False
                                if i >= eof: # End of File Reached?
                                    file_found = False
                        else:
                            i += 1
    
    file_meta_data = getFileMetaData(file_list)
    
    return file_meta_data, edit_details


### Copy and add a data tracker to edit_details
###     (edit_details) All the details on how to proceed with the file name edits.
###     (files_reviewed) Keep files reviewed when creating additional edit details copies.
###     (directory_files_renamed) Keep directory files renamed when creating additional edit details copies.
###     (individual_files_renamed) Keep individual files renamed when creating additional edit details copies.
###     (individual_file_group) File group to use when updating rename values.
###     (skip_warnings) Keep skip warnings when creating additional edit details copies.
###     (log_data) Keep log data when creating additional edit details copies.
###     --> Returns a [Dictionary] 
def copyEditDetails(edit_details, files_reviewed = 0, directory_files_renamed = 0, individual_files_renamed = 0, individual_file_group = False, skip_warnings = [], log_data = {}):
    start_time = datetime.now().timestamp()
    
    edit_details_copy = edit_details.copy()
    
    soft_rename_limit = edit_details_copy.get(SOFT_RENAME_LIMIT, NO_LIMIT)
    hard_rename_limit = edit_details_copy.get(HARD_RENAME_LIMIT, NO_LIMIT)
    modify_options = getOptions(edit_details_copy[INSERT_TEXT])
    search_options = getOptions(edit_details_copy.get(MATCH_TEXT, ''))
    search_meta_options = getOptions(edit_details_copy.get(MATCH_FILE_META, None))
    
    same_match_index = SAME_MATCH_INDEX in search_options or SAME_MATCH_INDEX in search_meta_options
    
    fnc = []
    fncl = []
    value_reset = 0
    
    if type(edit_details_copy[INSERT_TEXT]) == dict:
        
        if type(edit_details_copy[INSERT_TEXT][TEXT]) == tuple:
            if type(edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT]) == tuple:
                if COUNT in modify_options:
                    fnc.append( edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT][STARTING_COUNT] )
                    fncl.append( edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT][ENDING_COUNT] )
            else:
                if COUNT in modify_options or RANDOM_NUMBERS in modify_options:
                    fnc.append( edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT] )
                    fncl.append( NO_LIMIT )
                elif COUNT_TO in modify_options:
                    fnc.append( 1 )
                    fncl.append( edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT] )
        
        elif type(edit_details_copy[INSERT_TEXT][TEXT]) == list:
            #soft_rename_limit = NO_LIMIT if NO_REPEAT_TEXT_LIST not in modify_options or same_match_index else len(edit_details_copy[INSERT_TEXT][TEXT])
            soft_rename_limit = len(edit_details_copy[INSERT_TEXT][TEXT]) if NO_REPEAT_TEXT_LIST in modify_options and not same_match_index else NO_LIMIT
            
            for text in edit_details_copy[INSERT_TEXT][TEXT]:
                if type(text) == tuple:
                    if type(text[DYNAMIC_TEXT]) == tuple:
                        if COUNT in modify_options:
                            fnc.append( text[DYNAMIC_TEXT][STARTING_COUNT] )
                            fncl.append( text[DYNAMIC_TEXT][ENDING_COUNT] )
                    else:
                        if COUNT in modify_options:
                            fnc.append( text[DYNAMIC_TEXT] )
                            fncl.append( NO_LIMIT )
                        elif COUNT_TO in modify_options:
                            fnc.append( 1 )
                            fncl.append( text[DYNAMIC_TEXT] )
                else:
                    fnc.append( value_reset )
                    fncl.append( NO_LIMIT )
    
    # Reset the seed for random character generators
    if reset_random_seed:
        random_seed = getSpecificOption(modify_options, RANDOM_SEED, None)
        random.seed(random_seed)
    
    # Defaults
    if not fnc:
        fnc.append(value_reset)
    if not fncl:
        fncl.append(NO_LIMIT)
    if not skip_warnings:
        skip_warnings = [False]
    if not log_data:
        log_data = { ORG_FILE_PATHS : [], NEW_FILE_PATHS : [], LINKED_FILES_UPDATED : [], START_TIME : start_time, END_TIME : value_reset }
    
    edit_details_copy.update( { TRACKED_DATA : { FILES_REVIEWED : [files_reviewed, hard_rename_limit],
                                                 DIRECTORY_FILES_RENAMED : [value_reset, soft_rename_limit, directory_files_renamed],
                                                 INDIVIDUAL_FILES_RENAMED : [individual_files_renamed, soft_rename_limit],
                                                 INDIVIDUAL_FILE_GROUP : individual_file_group,
                                                 FILE_NAME_COUNT : fnc,
                                                 FILE_NAME_COUNT_LIMIT : fncl,
                                                 CURRENT_LIST_INDEX : NONE,
                                                 CURRENT_FILE_META : [],
                                                 CURRENT_FILE_RENAME : '',
                                                 USED_RANDOM_CHARS : [],
                                                 SKIPPED_FILES : [], ## TODO should this be updated each copy? what if a directory file and an individual file are the same?
                                                 SKIP_WARNINGS : skip_warnings,
                                                 LOG_DATA : log_data
                                               } } )
    
    return edit_details_copy


### Get tracker data with specific values and defaults when missing.
###     (edit_details) The edit details with the TRACKED_DATA key added.
###     (specific_data) A key in the tracked data Dictionary.
###     (key_index) A List of additional keys or index to nested Directories or Lists values.
###     --> Returns a [Dictionary] or [List] or [String] or [Integer] or [Boolean]
def getTrackedData(edit_details, specific_data = None, key_index = []):
    tracked_data = edit_details.get(TRACKED_DATA, {})
    
    if specific_data != None:
        
        if specific_data == FILES_RENAMED:
            td1 = tracked_data.get(DIRECTORY_FILES_RENAMED, [0, NO_LIMIT, 0])
            td2 = tracked_data.get(INDIVIDUAL_FILES_RENAMED, [0, NO_LIMIT])
            td = [td1[AMOUNT] + td2[AMOUNT], td1[LIMIT], td1[FULL_AMOUNT] + td2[AMOUNT]]
            for i in key_index:
                td = td[i]
                break #no further keys/indexes here
        
        elif specific_data == FILES_REVIEWED or specific_data == DIRECTORY_FILES_RENAMED or specific_data == INDIVIDUAL_FILES_RENAMED:
            td = tracked_data.get(specific_data, [0, NO_LIMIT])
            for i in key_index:
                td = td[i]
                break #no further keys/indexes here
        
        elif specific_data == INDIVIDUAL_FILE_GROUP:
            td = tracked_data.get(specific_data, False)
        
        elif (specific_data == FILE_NAME_COUNT or specific_data == FILE_NAME_COUNT_LIMIT or specific_data == SKIPPED_FILES 
              or specific_data == SKIP_WARNINGS or specific_data == USED_RANDOM_CHARS or specific_data == CURRENT_FILE_META):
            td = tracked_data.get(specific_data, [])
            for i in key_index:
                if i < len(td):
                    td = td[i]
                    break
                else:
                    td = None
                    break
        
        elif specific_data == CURRENT_LIST_INDEX:
            td = tracked_data.get(specific_data, NONE)
        
        elif specific_data == CURRENT_FILE_RENAME:
            td = tracked_data.get(specific_data, '')
        
        elif specific_data == LOG_DATA:
            td = tracked_data.get(specific_data, {})
            #if len(key_index) > -1:
            if key_index:
                td = td.get(key_index[0], None)
                if td != None and len(key_index) > 1:
                    if len(td) < key_index[1]:
                        td = td[key_index[1]]
                    else:
                        td = None
        else:
            td = None
    else:
        td = tracked_data
    
    return td


### Update edit details tracker with new values.
###     (edit_details) The edit details with the TRACKED_DATA key added.
###     (update_data) A Dictionary of all keys to be updated in tracker.
###     (append_values) Update (add to) values or change them.
###     --> Returns a [Dictionary]
def updateTrackedData(edit_details, update_data, append_values = True):
    
    if edit_details.get(TRACKED_DATA, None) == None:
        print('Tracker Not Found. Something likely went wrong.')
        return edit_details
    
    if FILES_REVIEWED in update_data:
        if append_values:
            edit_details[TRACKED_DATA][FILES_REVIEWED][AMOUNT] = edit_details[TRACKED_DATA][FILES_REVIEWED][AMOUNT] + update_data[FILES_REVIEWED]
        else:
            edit_details[TRACKED_DATA][FILES_REVIEWED][AMOUNT] = update_data[FILES_REVIEWED]
    
    if FILES_RENAMED in update_data:
        if getTrackedData(edit_details, INDIVIDUAL_FILE_GROUP):
            if append_values:
                edit_details[TRACKED_DATA][INDIVIDUAL_FILES_RENAMED][AMOUNT] = edit_details[TRACKED_DATA][INDIVIDUAL_FILES_RENAMED][AMOUNT] + update_data[FILES_RENAMED]
            else:
                edit_details[TRACKED_DATA][INDIVIDUAL_FILES_RENAMED][AMOUNT] = update_data[FILES_RENAMED]
        else: # Directory File Group
            if append_values:
                edit_details[TRACKED_DATA][DIRECTORY_FILES_RENAMED][AMOUNT] = edit_details[TRACKED_DATA][DIRECTORY_FILES_RENAMED][AMOUNT] + update_data[FILES_RENAMED]
                edit_details[TRACKED_DATA][DIRECTORY_FILES_RENAMED][FULL_AMOUNT] = edit_details[TRACKED_DATA][DIRECTORY_FILES_RENAMED][FULL_AMOUNT] + update_data[FILES_RENAMED]
            else:
                edit_details[TRACKED_DATA][DIRECTORY_FILES_RENAMED][AMOUNT] = update_data[FILES_RENAMED]
                edit_details[TRACKED_DATA][DIRECTORY_FILES_RENAMED][FULL_AMOUNT] = update_data[FILES_RENAMED]
    
    if FILE_NAME_COUNT in update_data:
        index = update_data[FILE_NAME_COUNT][INDEX_POINTER]
        update_count = update_data[FILE_NAME_COUNT][UPDATE_COUNT]
        if index < len(edit_details[TRACKED_DATA][FILE_NAME_COUNT]):
            edit_details[TRACKED_DATA][FILE_NAME_COUNT][index] = edit_details[TRACKED_DATA][FILE_NAME_COUNT][index] + update_count
    
    if FILE_NAME_COUNT_LIMIT in update_data:
        index = update_data[FILE_NAME_COUNT_LIMIT][INDEX_POINTER]
        update_count_limit = update_data[FILE_NAME_COUNT_LIMIT][UPDATE_LIMIT]
        edit_details[TRACKED_DATA][FILE_NAME_COUNT_LIMIT][index] = edit_details[TRACKED_DATA][FILE_NAME_COUNT_LIMIT][index] + update_count_limit
    
    if CURRENT_LIST_INDEX in update_data:
        edit_details[TRACKED_DATA][CURRENT_LIST_INDEX] = update_data[CURRENT_LIST_INDEX]
    
    if CURRENT_FILE_META in update_data:
        edit_details[TRACKED_DATA][CURRENT_FILE_META] = update_data[CURRENT_FILE_META]
    
    if CURRENT_FILE_RENAME in update_data:
        edit_details[TRACKED_DATA][CURRENT_FILE_RENAME] = update_data[CURRENT_FILE_RENAME]
    
    if USED_RANDOM_CHARS in update_data:
        if append_values:
            edit_details[TRACKED_DATA][USED_RANDOM_CHARS].append( update_data[USED_RANDOM_CHARS] )
        else:
            edit_details[TRACKED_DATA][USED_RANDOM_CHARS].pop()
    
    if SKIPPED_FILES in update_data:
        edit_details[TRACKED_DATA][SKIPPED_FILES].append( update_data[SKIPPED_FILES] )
    
    if SKIP_WARNINGS in update_data:
        index = update_data[SKIP_WARNINGS][INDEX_POINTER]
        edit_details[TRACKED_DATA][SKIP_WARNINGS][index] = update_data[SKIP_WARNINGS][UPDATE_SKIP]
    
    if ORG_FILE_PATHS in update_data:
        edit_details[TRACKED_DATA][LOG_DATA][ORG_FILE_PATHS].append( update_data[ORG_FILE_PATHS] )
    
    if NEW_FILE_PATHS in update_data:
        edit_details[TRACKED_DATA][LOG_DATA][NEW_FILE_PATHS].append( update_data[NEW_FILE_PATHS] )
    
    if LINKED_FILES_UPDATED in update_data:
        if update_data[LINKED_FILES_UPDATED]:
            edit_details[TRACKED_DATA][LOG_DATA][LINKED_FILES_UPDATED].append( update_data[LINKED_FILES_UPDATED] )
    
    if START_TIME in update_data:
        edit_details[TRACKED_DATA][LOG_DATA][START_TIME] = update_data[START_TIME]
    
    if END_TIME in update_data:
        edit_details[TRACKED_DATA][LOG_DATA][END_TIME] = update_data[END_TIME]
    
    return edit_details


### Get all the meta data from a list of files and sort the list in various ways before renaming.
###     (files) A List of file names or paths.
###     (sort_option) A Dictionary with a file sorting option.
###     (root) Root path if files List has only names.
###     --> Returns a [List]
def getFileMetaData(files, sort_option = None, root = ''):
    files_meta = []
    directory_list = []
    individual_file_list = []
    
    for file in files:
        
        if root == '':
            file_path = Path(file)
        else:
            file_path = Path(PurePath().joinpath(root, file))
        
        if Path.exists(file_path):
            file_meta = os.stat(file_path)
            
            if ffmpeg_installed and filetype_installed:
                #print(file_path)
                try:
                    file_type = filetype.guess(file_path)
                    is_audio = filetype.is_audio(file_path)
                    is_font = filetype.is_font(file_path)
                    is_image = filetype.is_image(file_path)
                    is_video = filetype.is_video(file_path)
                    is_app = None
                    is_message = None
                    is_model = None
                    is_multipart = None
                    is_text = None
                    is_archive = filetype.is_archive(file_path)
                    is_doc = None
                    is_presentation = None
                    is_spead_sheet = None
                except:
                    file_type = None
                    is_audio = None
                    is_font = None
                    is_image = None
                    is_video = None
                    is_app = None
                    is_message = None
                    is_model = None
                    is_multipart = None
                    is_text = None
                    is_archive = None
                    is_doc = None
                    is_presentation = None
                    is_spead_sheet = None
                
                mime_type = mimetypes.guess_type(file_path)
                
                if debug:
                    print('file_type: %s' % file_type)
                    print('mime_type: (%s, %s)' % (mime_type[0], mime_type[1]))
                
                archive_mimes = ['application/x-7z-compressed','application/x-unix-archive','application/x-bzip2','application/vnd.ms-cab-compressed',
                                 'application/x-google-chrome-extension','application/dicom','application/vnd.debian.binary-package','application/x-executable',
                                 'application/octet-stream','application/epub+zip','application/vnd.microsoft.portable-executable','application/gzip',
                                 'application/x-iso9660-image','application/x-lzip','application/x-nintendo-nes-rom','application/pdf','application/postscript',
                                 'application/vnd.rar','application/x-rpm','application/rtf','application/vnd.sqlite3','application/x-shockwave-flash',
                                 'application/x-tar','application/x-xz','application/x-compress','application/zip','application/zstd','application/x-zip-compressed']
                document_mimes = ['application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-powerpoint',
                                  'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.ms-excel',
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
                
                file_meta_type = None
                file_meta_mime = None
                if file_type:
                    #print('File extension: %s' % file_type.extension)
                    #print('File MIME type: %s' % file_type.mime)
                    file_meta_mime = file_type.mime
                
                #print('is_archive: %s' % is_archive)
                
                # Last chance to find mime
                if mime_type[0] and not file_meta_mime:
                    file_meta_mime = mime_type[0]
                
                if file_meta_mime:
                    
                    file_type_basic = file_meta_mime.split('/')[0]
                    #print(file_type_basic)
                    
                    # Basic Types
                    if file_type_basic == 'application':
                        file_meta_type = TYPE_APPLICATION
                    elif is_audio or file_type_basic == 'audio':
                        file_meta_type = TYPE_AUDIO
                    elif is_font or file_type_basic == 'font':
                        file_meta_type = TYPE_FONT
                    elif is_image or file_type_basic == 'image':
                        file_meta_type = TYPE_IMAGE
                    elif file_type_basic == 'message':
                        file_meta_type = TYPE_MESSAGE
                    elif file_type_basic == 'model':
                        file_meta_type = TYPE_MODEL
                    elif file_type_basic == 'multipart':
                        file_meta_type = TYPE_MULTIPART
                    elif file_type_basic == 'text':
                        file_meta_type = TYPE_TEXT
                    elif is_video or file_type_basic == 'video':
                        file_meta_type = TYPE_VIDEO
                    
                    # Application Types (TYPE_APPLICATION will still match these)
                    if is_archive or file_type_basic in archive_mimes:
                        file_meta_type = TYPE_ARCHIVE
                    if file_type_basic in document_mimes:
                        file_meta_type = TYPE_DOCUMENT
                    
                    # Basic Types
                    is_app = file_type_basic == 'application'
                    is_audio = file_type_basic == 'audio'
                    is_font = file_type_basic == 'font'
                    is_image = file_type_basic == 'image'
                    is_message = file_type_basic == 'message'
                    is_model = file_type_basic == 'model'
                    is_multipart = file_type_basic == 'multipart'
                    is_text = file_type_basic == 'text'
                    is_video = file_type_basic == 'video'
                    
                    # Application Types
                    if not is_archive:
                        is_archive = file_meta_mime in archive_mimes
                    is_doc = file_meta_mime in document_mimes
                    
                    #is_doc = mime_type[0] == 'application/msword' or mime_type[0] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    #is_presentation = mime_type[0] == 'application/vnd.ms-powerpoint' or mime_type[0] == 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    #is_spead_sheet = mime_type[0] == 'application/vnd.ms-excel' or mime_type[0] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                
                if debug:
                    print('file_meta_type: %s' % file_meta_type)
                    print('file_meta_mime: %s' % file_meta_mime)
                    print('is_app: %s' % is_app)
                    print('is_archive: %s' % is_archive)
                    print('is_audio: %s' % is_audio)
                    print('is_font: %s' % is_font)
                    print('is_image: %s' % is_image)
                    print('is_text: %s' % is_text)
                    print('is_doc: %s' % is_doc)
                    print('is_spead_sheet: %s' % is_spead_sheet)
                    print('is_presentation: %s' % is_presentation)
                    print('is_video: %s' % is_video)
                
                probe = None
                try:
                    probe = ffmpeg.probe(file_path)
                    #probe.append(ffmpeg.probe(file_path, select_streams = "v"))
                    #probe.append(ffmpeg.probe(file_path, select_streams = "a"))
                    #video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
                    #print(probe)
                    if debug:
                        print('-Probe Good')
                except ffmpeg.Error as e:
                    #print(e.stderr)
                    if debug:
                        print('-Probe Failed')
                
                format_short, format_long, height, width, duration, bit_depth = None,None,None,None,None,None
                video_bit_rate, frame_rate, audio_bit_rate, sample_rate, channels, channel_layout = None,None,None,None,None,None
                title, album, artist, date, genre, publisher, track_number = None,None,None,None,None,None,None
                
                if probe:
                    stream = probe.get('streams')
                    format = probe.get('format')
                    
                    format_short = stream[0].get('codec_name')
                    format_long = stream[0].get('codec_long_name')
                    
                    height = stream[0].get('height') # alt: 'coded_height'
                    width = stream[0].get('width') # alt: 'coded_width'
                    duration = stream[0].get('duration')
                    
                    bit_depth = stream[0].get('bits_per_raw_sample')
                    if bit_depth: bit_depth = int(bit_depth)
                    
                    if is_video:
                        video_bit_rate = stream[0].get('bit_rate')
                        audio_bit_rate = stream[1].get('bit_rate')
                    else:
                        video_bit_rate = None
                        audio_bit_rate = stream[0].get('bit_rate')
                    if video_bit_rate: video_bit_rate = float(video_bit_rate) / 1000
                    if audio_bit_rate: audio_bit_rate = float(audio_bit_rate) / 1000
                    
                    sample_rate = stream[1].get('sample_rate') if is_video else stream[0].get('sample_rate')
                    if sample_rate: sample_rate = float(sample_rate) / 1000
                    
                    frame_rate = stream[0].get('r_frame_rate') #alt: 'avg_frame_rate'
                    if frame_rate and is_video:
                        frame_rate_split = frame_rate.split('/')
                        frame_rate = int(frame_rate_split[0]) / int(frame_rate_split[1])
                    
                    channels = stream[1].get('channels') if is_video else stream[0].get('channels')
                    if channels: channels = int(channels)
                    channel_layout = stream[1].get('channel_layout') if is_video else stream[0].get('channel_layout')
                    
                    if is_audio:
                        audio_tags = format.get('tags')
                        title = audio_tags.get('title')
                        album = audio_tags.get('album')
                        artist = audio_tags.get('artist') # alt: album_artist
                        date = audio_tags.get('date')
                        if date: date = int(date)
                        genre = audio_tags.get('genre')
                        publisher = audio_tags.get('publisher')
                        track_number = audio_tags.get('track')
                        if track_number: track_number = int(track_number)
                
                if debug:
                    print('format_short: %s' % format_short)
                    print('format_long: %s' % format_long)
                    print('height: %s' % height)
                    print('width: %s' % width)
                    print('duration: %s' % duration)
                    print('bit_depth: %s' % bit_depth)
                    print('video_bit_rate: %s' % video_bit_rate)
                    print('frame_rate: %s' % frame_rate)
                    print('audio_bit_rate: %s' % audio_bit_rate)
                    print('sample_rate: %s' % sample_rate)
                    print('channels: %s' % channels)
                    print('channel_layout: %s' % channel_layout)
                    print('title: %s' % title)
                    print('album: %s' % album)
                    print('artist: %s' % artist)
                    print('date: %s' % date)
                    print('genre: %s' % genre)
                    print('publisher: %s' % publisher)
                    print('track_number: %s' % track_number)
            
            #if debug: input('...')
            
            if Path.is_file(file_path):
                individual_file_list.append( (file_path, file_meta.st_size, file_meta.st_atime, file_meta.st_mtime, file_meta.st_ctime,
                                              file_meta_type, file_meta_mime, format_short, format_long, height, width, duration, bit_depth,
                                              video_bit_rate, frame_rate, audio_bit_rate, sample_rate, channels, channel_layout, title,
                                              album, artist, date, genre, publisher, track_number) )
            elif Path.is_dir(file_path):
                directory_list.append( (file_path, file_meta.st_size, file_meta.st_atime, file_meta.st_mtime, file_meta.st_ctime) )
            else:
                print("\nSkipping This: [ %s ]" % file_path)
                print("\nThis is not a normal file or directory.")
    
    ## TODO Sort using new meta added
    
    if type(sort_option) == dict:
        descending = False if list(sort_option.values())[0] == ASCENDING else True
        if ALPHABETICALLY in sort_option:
            directory_list.sort(reverse=descending, key=sortFilesAlphabetically)
            individual_file_list.sort(reverse=descending, key=sortFilesAlphabetically)
        elif FILE_SIZE in sort_option:
            directory_list.sort(reverse=descending, key=sortFilesByFileSize)
            individual_file_list.sort(reverse=descending, key=sortFilesByFileSize)
        elif DATE_ACCESSED in sort_option:
            directory_list.sort(reverse=descending, key=sortFilesByAccessDate)
            individual_file_list.sort(reverse=descending, key=sortFilesByAccessDate)
        elif DATE_MODIFIED in sort_option:
            directory_list.sort(reverse=descending, key=sortFilesByModifyDate)
            individual_file_list.sort(reverse=descending, key=sortFilesByModifyDate)
        elif DATE_CREATED in sort_option: # or DATE_META_MODIFIED in sort_option:
            directory_list.sort(reverse=descending, key=sortFilesByCreationDate)
            individual_file_list.sort(reverse=descending, key=sortFilesByCreationDate)
    
    if directory_list:
        files_meta.extend(directory_list) # [dirs]
    if individual_file_list and root == '':
        files_meta.append(individual_file_list) # [dirs, [files]] or [[files]]
    elif not directory_list and individual_file_list:
        files_meta.extend(individual_file_list) # [files] (Used in directory walks)
    
    return files_meta


### Sort file functions.
###     (file) A Tuple with the [0]full file path,  [1]file size,       [2]access date,
###                             [3]modify date      [4]creation date (UNIX: meta data modified date).
###     --> Returns a [String] or [Integer]
def sortFilesAlphabetically(file):
    return file[0].name
def sortFilesByFileSize(file):
    return file[2]
def sortFilesByAccessDate(file):
    return file[3]
def sortFilesByModifyDate(file):
    return file[4]
def sortFilesByCreationDate(file):
    return file[5]


### Using the edit details create a new file name and try renaming file and updating any linked files.
###     (some_file) The full path to a file.
###     (edit_details) All the details on how to proceed with the file name edits.
###     --> Returns a [Dictionary]
def createNewFileName(some_file, edit_details):
    
    ## TODO: get file_path from edit_details moving forward
    file_path = Path(some_file)
    assert Path.is_file(file_path) # Error if not a file or doen't exist
    file_name_changed = False
    
    skip_file = checkForSkippedFiles(file_path, getTrackedData(edit_details, SKIPPED_FILES))
    
    # Create The New File Name
    if not skip_file:
        edit_details = insertTextIntoFileName(file_path, edit_details)
        new_file_name = getTrackedData(edit_details, CURRENT_FILE_RENAME)
        file_name_changed = False if new_file_name == file_path.name else True
    
    # Now Rename The File
    if file_name_changed:
        new_file_path = Path(file_path.parent, new_file_name)
        edit_details = renameFile(file_path, new_file_path, edit_details)
        
        skip_file = checkForSkippedFiles(new_file_path, getTrackedData(edit_details, SKIPPED_FILES))
        
        if not skip_file:
            linked_files = edit_details.get(LINKED_FILES, [])
            linked_files_updates = []
            for file in linked_files:
                links_updated = updateLinksInFile(file, str(file_path), str(new_file_path))
                linked_files_updates.append(links_updated)
                if links_updated:
                    if debug: print('----Link File Updated: [ %s ]' % (file))
                #else:
                    #if debug: print('----Link File Not Updated: [ %s ]' % (file))
            
            edit_details = updateTrackedData(edit_details, { LINKED_FILES_UPDATED : linked_files_updates })
    
    else:
        print('--File Not Renamed: %s' % (file_path))
    
    return edit_details


### Skip any files that already had a name matching previous rename attempts (and not overwritten).
### Note: This keeps the starting and ending COUNT exactly as typed with no skipping numbers.
### (3,9) will always be (3,9) and not (5,9) due to files with that same name/count already existing.
###     (file_path) The full path to a file to check.
###     (skipped_files) A list of files flagged to skip.
###     --> Returns a [Boolean]
def checkForSkippedFiles(file_path, skipped_files):
    skip_file = False
    for file in skipped_files:
        if file == file_path:
            skip_file = True
            break
    return skip_file


### Get the text from a Tuples() that requires an OPTION on how to handle it.
###     (dynamic_text_data) The dynamic text Tuple.
###     (the_dynamic_text) The dynamic text/number to insert into the regular text.
###     (modify_options) 
###     --> Returns a [String]
def getDynamicText(dynamic_text_data, the_dynamic_text, modify_options = None):
    
    if type(dynamic_text_data) != tuple:
        return dynamic_text_data
    
    starting_text = dynamic_text_data[STARTING_TEXT]
    middle_text = ''
    
    digits = len(str(the_dynamic_text))
    min_digits = getSpecificOption(modify_options, MINIMUM_DIGITS, 0)
    min_digits -= digits - 1
    
    while min_digits > 1:
        middle_text += '0'
        min_digits -= 1
    
    middle_text += str(the_dynamic_text)
    ending_text = dynamic_text_data[ENDING_TEXT] if len(dynamic_text_data) > 2 else ''
    dynamic_text = starting_text + middle_text + ending_text
    
    return dynamic_text


### Get all text needed to make a proper search.
###     (search_data) All the search or match data.
###     (ignore_data) All the ignore data.
###     (file_path) The file path with a file name that will be searched through.
###     --> Returns a [List] and [String] and [List] and [String]
def getSearchData(search_data, ignore_data, file_path):
    
    match_text_list = getText(search_data)
    ignore_text_list = getText(ignore_data, [])
    search_options = getOptions(search_data)
    ignore_options = getOptions(ignore_data)
    searchable_match_file_name = [file_path.name]
    searchable_ignore_file_name = [file_path.name]
    
    data_loop = [[match_text_list, search_options, searchable_match_file_name],
                 [ignore_text_list, ignore_options, searchable_ignore_file_name]]
    
    for data in data_loop:
        if REGEX in data[1]: ## TODO
            print('TODO REGEX')
        #else: ## this should override every other option, when added.
        
        # Default MATCH_CASE
        if NO_MATCH_CASE in data[1]:
            
            i = 0
            while i < len(data[0]):
                text = data[0].pop(i)
                data[0].insert(i, text.casefold())
                i += 1
            
            data[2][0] = file_path.name.casefold()
        
        if EXTENSION in data[1]:
            
            i = 0
            while i < len(data[0]):
                if data[0][i] != '' and data[0][i].find('.') != 0 :
                    text = data[0].pop(i)
                    data[0].insert(i, '.'+text) # Add a '.' if missing
                i += 1
            
            if NO_MATCH_CASE in data[1]:
                ext = file_path.suffix
                data[2][0] = ext.casefold()
            else:
                data[2][0] = file_path.suffix
    
    return match_text_list, searchable_match_file_name[0], ignore_text_list, searchable_ignore_file_name[0]


### Search current file meta data for any specific meta data in edit_details. Return -1 or 0+ (meta_list_index).
###     (file_meta_data) The current file meta data.
###     (match_file_meta_list) The meta search and match data.
###     (match_file_meta_options) The meta search and match options.
###     --> Returns a [Integer]
def getMetaSearchResults(file_meta_data, match_file_meta_list, match_file_meta_options):
    #match_file_meta_data = edit_details.get(MATCH_FILE_META, None)
    #match_file_meta_list = getMeta(match_file_meta_data)
    #match_file_meta_options = getOptions(match_file_meta_data)
    #file_meta_data = getTrackedData(edit_details, CURRENT_FILE_META)
    same_meta_match_index = SAME_MATCH_INDEX in match_file_meta_options
    
    meta_list_index, i = -1, -1
    for meta_data in match_file_meta_list:
        i += 1
        #print('Current Meta: %s' % meta_data)
        
        select_meta_data = next(iter(meta_data))
        how_to_match = meta_data[select_meta_data]
        
        if select_meta_data == FILE_META_SIZE:
            #print('Size Meta')
            file_meta_size = file_meta_data[select_meta_data]
            
            # Serarate file size out into GB / MB / KB / Bytes
            file_gb, file_mb, file_kb, file_bytes = file_meta_size,file_meta_size,file_meta_size,file_meta_size
            if file_meta_size > GIGABYTE:
                file_gb = math.floor(file_meta_size / GIGABYTE)
            if file_meta_size > MEGABYTE:
                file_mb = math.floor(file_gb / MEGABYTE)
            if file_meta_size > KILOBYTE:
                file_kb = math.floor(file_mb / KILOBYTE)
                #file_bytes = math.floor(math.remainder(file_mb, KILOBYTE))
                file_bytes = int(math.remainder(file_mb, KILOBYTE))
            
            # Get file sizes to match
            bytes = meta_data.get(BYTES, None)
            kb = meta_data.get(KB, None)
            mb = meta_data.get(MB, None)
            gb = meta_data.get(GB, None)
            file_size_match = 0
            if gb: file_size_match += gb * GIGABYTE
            if mb: file_size_match += mb * MEGABYTE
            if kb: file_size_match += kb * KILOBYTE
            if bytes: file_size_match += bytes
            
            if debug: print('file_meta_size: %s' % file_meta_size)
            if debug: print('file_size_match: %s' % file_size_match)
            
            # Check if file meta matches all meta data in preset or break on first match found if same_meta_match_index
            if how_to_match == EXACT_MATCH:
                if gb and gb != file_gb:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if mb and mb != file_mb:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if kb and kb != file_kb:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if bytes and bytes != file_bytes:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            
            elif how_to_match == LESS_THAN:
                if file_size_match < file_meta_size:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            
            elif how_to_match == MORE_THAN:
                if file_size_match > file_meta_size:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            
            ##TODO elif how_to_match == LOOSE_MATCH: elif how_to_match == SKIP_EXACT_MATCH: elif how_to_match == SKIP_LOOSE_MATCH:
            
            # A Match Made
            meta_list_index = i
            if same_meta_match_index: break
            else: continue # To Match All
        
        if (select_meta_data == FILE_META_ACCESS
         or select_meta_data == FILE_META_MODIFY
         or select_meta_data == FILE_META_CREATE
         or select_meta_data == FILE_META_LENGTH
         or select_meta_data == FILE_META_AUDIO_YEAR): # or FILE_META_METADATA
            #print('Time Meta')
            
            file_meta_timestamp = file_meta_data[select_meta_data]
            file_meta_date_time = datetime.fromtimestamp(file_meta_timestamp)
            #timestamp_now = getTrackedData(edit_details, LOG_DATA, [START_TIME])
            timestamp_now = datetime.now().timestamp()
            
            year = meta_data.get(YEAR, None)
            if not year: year = meta_data.get(DATA, None)
            month = meta_data.get(MONTH, None)
            #if month: month = int(month) ## TODO: force int on number if user entered them as strings?
            day = meta_data.get(DAY, None)
            hour = meta_data.get(HOUR, None)
            minute = meta_data.get(MINUTE, None)
            second = meta_data.get(SECOND, None)
            millisecond = meta_data.get(MILLISECOND, None)
            microsecond = meta_data.get(MICROSECOND, None)
            
            # Get length of time for comparision to today's date.
            time_delta_match = 0
            if year:
                time_delta_match += year * 31536000
            if month:
                time_delta_match += month * 30 * 86400
            if day:
                time_delta_match += day * 86400
            if hour:
                time_delta_match += hour * 3600
            if minute:
                time_delta_match += minute * 60
            if second:
                time_delta_match += second
            if millisecond:
                time_delta_match += millisecond / 1000
            elif microsecond:
                time_delta_match += microsecond / 1000 / 1000
            if debug: print('time_delta_match: %s' % time_delta_match)
            
            # Check if file meta matches all meta data in preset or break on first match found if same_meta_match_index
            if how_to_match == EXACT_MATCH:
                if year and year != file_meta_date_time.year:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if month and month != file_meta_date_time.month:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if day and day != file_meta_date_time.day:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if hour and hour != file_meta_date_time.hour:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if minute and minute != file_meta_date_time.minute:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if second and second != file_meta_date_time.second:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if millisecond and millisecond != file_meta_date_time.microsecond:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
                if microsecond and microsecond != file_meta_date_time.microsecond:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            
            ##TODO elif how_to_match == LOOSE_MATCH: elif how_to_match == SKIP_EXACT_MATCH: elif how_to_match == SKIP_LOOSE_MATCH:
            
            elif how_to_match == WITHIN_THE_PAST: # or LESS_THAN
                if timestamp_now - file_meta_timestamp > time_delta_match:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            
            elif how_to_match == OLDER_THAN: # or MORE_THAN
                if timestamp_now - file_meta_timestamp < time_delta_match:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            
            # A Match Made
            meta_list_index = i
            if same_meta_match_index: break
            else: continue # To Match All
        
        if select_meta_data == FILE_META_TYPE:
            print('Integer Constant DATA')
            
            file_meta_constant = file_meta_data[select_meta_data]
            file_meta_constant = None if file_meta_constant == '' else file_meta_constant
            match_meta_constant = meta_data.get(DATA, None)
            match_meta_constant = None if match_meta_constant == '' else match_meta_constant
            
            # If searching for TYPE_APPLICATION, force match all custom sub catigories too.
            if match_meta_constant == TYPE_APPLICATION:
                if file_meta_constant == TYPE_ARCHIVE:
                    match_meta_constant = TYPE_ARCHIVE
                elif file_meta_constant == TYPE_DOCUMENT:
                    match_meta_constant = TYPE_DOCUMENT
            
            if how_to_match == EXACT_MATCH or how_to_match == LOOSE_MATCH: # Only EXACT_MATCH works here
                if file_meta_constant != match_meta_constant:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            elif how_to_match == SKIP_EXACT_MATCH or how_to_match == SKIP_LOOSE_MATCH: # Only SKIP_EXACT_MATCH works here
                if file_meta_constant == match_meta_constant:
                    meta_list_index = -1
                    break
            
            # A Match Made
            meta_list_index = i
            if same_meta_match_index: break
            else: continue # To Match All
        
        if (select_meta_data == FILE_META_HEIGHT
         or select_meta_data == FILE_META_WIDTH
         or select_meta_data == FILE_META_BIT_DEPTH
         or select_meta_data == FILE_META_VIDEO_BITRATE
         or select_meta_data == FILE_META_VIDEO_FRAME_RATE
         or select_meta_data == FILE_META_AUDIO_BITRATE
         or select_meta_data == FILE_META_AUDIO_SAMPLE_RATE
         or select_meta_data == FILE_META_AUDIO_CHANNELS
         or select_meta_data == FILE_META_AUDIO_TRACK):
            print('Number DATA')
            
            file_meta_number = file_meta_data[select_meta_data]
            file_meta_number = None if file_meta_number == '' else file_meta_number
            match_meta_number = meta_data.get(DATA, None)
            match_meta_number = None if match_meta_number == '' else match_meta_number
            
            if how_to_match == EXACT_MATCH:
                if file_meta_number != match_meta_number:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            elif how_to_match == LOOSE_MATCH:
                file_meta_number_high = file_meta_number + (file_meta_number * 0.05)
                file_meta_number_low = file_meta_number - (file_meta_number * 0.05)
                if file_meta_number > file_meta_number_high or file_meta_number < file_meta_number_low:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            elif how_to_match == SKIP_EXACT_MATCH:
                if file_meta_number == match_meta_number:
                    meta_list_index = -1
                    break
            elif how_to_match == SKIP_LOOSE_MATCH:
                file_meta_number_high = file_meta_number + (file_meta_number * 0.05)
                file_meta_number_low = file_meta_number - (file_meta_number * 0.05)
                if file_meta_number < file_meta_number_high and file_meta_number > file_meta_number_low:
                    meta_list_index = -1
                    break
            if how_to_match == LESS_THAN:
                if file_meta_number < match_meta_number:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            if how_to_match == MORE_THAN:
                if file_meta_number > match_meta_number:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            
            # A Match Made
            meta_list_index = i
            if same_meta_match_index: break
            else: continue # To Match All
        
        if (select_meta_data == FILE_META_MIME
         or select_meta_data == FILE_META_FORMAT
         or select_meta_data == FILE_META_FORMAT_LONG
         or select_meta_data == FILE_META_AUDIO_CHANNEL_LAYOUT
         or select_meta_data == FILE_META_AUDIO_TITLE
         or select_meta_data == FILE_META_AUDIO_ALBUM
         or select_meta_data == FILE_META_AUDIO_ARTIST
         or select_meta_data == FILE_META_AUDIO_GENRE
         or select_meta_data == FILE_META_AUDIO_PUBLISHER):
            print('Text DATA')
            
            file_meta_text = file_meta_data[select_meta_data]
            file_meta_text = None if file_meta_text == '' else file_meta_text
            match_meta_text = meta_data.get(DATA, None)
            match_meta_text = None if match_meta_text == '' else match_meta_text
            
            if how_to_match == EXACT_MATCH:
                if file_meta_text != match_meta_text:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            elif how_to_match == LOOSE_MATCH:
                if file_meta_text.find(match_meta_text) == -1:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            elif how_to_match == SKIP_EXACT_MATCH:
                if file_meta_text == match_meta_text:
                    meta_list_index = -1
                    break
            elif how_to_match == SKIP_LOOSE_MATCH:
                if file_meta_text.find(match_meta_text) > -1:
                    if same_meta_match_index: continue
                    else:
                        meta_list_index = -1
                        break
            
            # A Match Made
            meta_list_index = i
            if same_meta_match_index: break
            else: continue # To Match All
    
    if debug: print('meta_list_index: %s' % meta_list_index)
    
    return meta_list_index


### Return the TEXT or META value from a Dictionary.
###     (data) A Dictionary that has a TEXT or META key.
###     (default) If text not found return default
###     --> Returns a [List]
def getText(data, default = [''], key = TEXT):
    if type(data) == dict:
        text = data.get(key, default)
        # If no key but there's still data, just return the data assuming it's a single item with no options or placement.
        if text == default and data:
            text = data
        if type(text) != list:
            text = [text]
    elif data == None or data == '':
        text = default
    else:
        text = data if type(data) == list else [data]
    return text

def getMeta(data, default = []):
    return getText(data, default, META)


### Return all or a specific option's value from a Dictionary.
###     (data) A Dictionary that has an OPTIONS key.
###     (specific_option) Return True (or a value) if specific option found
###     (default) If specific option not found return default
###     --> Returns a [List] or [Boolean] or [Integer]
def getOptions(data, specific_option = None, default = False):
    if type(data) == dict:
        options = data.get(OPTIONS, [])
        if type(options) != list:
            options = [options]
    else:
        options = []
    if specific_option != None:
        return getSpecificOption(options, specific_option, default)
    return options

def getSpecificOption(options, specific_option, default = False):
    if type(options) != list:
        options = [options]
    for option in options:
        if type(option) == tuple:
            if option[0] == specific_option:
                return option[1] # A value, likely a number
        elif option == specific_option:
            return True
    return default


### Return the placement, always returning it as a Tuple
###     (data) A Dictionary that has a PLACEMENT key.
###     --> Returns a [Tuple] 
def getPlacement(data):
    placement = data.get(PLACEMENT, END)
    if type(placement) == tuple and len(placement) == 1:
        placement = (placement[0], NONE)
    elif type(placement) != tuple:
        placement = (placement, NONE)
    return placement


### Returns +0 finding an index not currently limited, "-1" if index hit limit and no other indexes are avalible, or -2 when all avalible indexes in list hit limit.
###     (tracked_data) 
###     (list_index) 
###     (insert_text_list_size) 
###     (same_match_index) 
###     (no_repeat_text_list) 
###     --> Returns a [Integer] 
def checkAllAvalibleCountLimits(tracked_data, list_index, insert_text_list_size = -1, same_match_index = False, no_repeat_text_list = False, recursive_count = 0):
    dynamic_count = tracked_data[FILE_NAME_COUNT][list_index]
    dynamic_count_limit = tracked_data[FILE_NAME_COUNT_LIMIT][list_index]
    
    if dynamic_count_limit > NO_LIMIT and dynamic_count > dynamic_count_limit:
        # Then check the next index...
        next_list_index = list_index + 1
        
        if same_match_index:
            list_index = -1 # No choosing another index to return, will either be -1 or -2 in the end
            next_list_index = 0 if next_list_index >= insert_text_list_size else next_list_index
            recursive_count += 1
            if recursive_count <= insert_text_list_size:
                list_index = checkAllAvalibleCountLimits(tracked_data, next_list_index, insert_text_list_size, same_match_index, no_repeat_text_list, recursive_count)
                if list_index > -2: # Only checking if all limits hit, if not go with first called index check, which we alreayd know is -1
                    list_index = -1
            else:
                list_index = -2
        
        elif next_list_index >= insert_text_list_size:
            recursive_count += 1
            if recursive_count <= insert_text_list_size:
                list_index = checkAllAvalibleCountLimits(tracked_data, next_list_index, insert_text_list_size, same_match_index, no_repeat_text_list, recursive_count)
            else:
                list_index = -2
        
        elif not no_repeat_text_list:
            recursive_count += 1
            if recursive_count <= insert_text_list_size:
                list_index = checkAllAvalibleCountLimits(tracked_data, 0, insert_text_list_size, same_match_index, no_repeat_text_list, recursive_count)
            else:
                list_index = -2
        
        else:
            list_index = -1
        
    return list_index


### Check if all count limits hit in any dynamic text used.
###     (tracked_data) A Dictionary with file name COUNT data.
###     --> Returns a [Boolean] 
def allCountLimitsHitCheck(tracked_data):
    all_limits_hit = False
    i = 0
    for file_name_count in tracked_data[FILE_NAME_COUNT]:
        if tracked_data[FILE_NAME_COUNT_LIMIT][i] == NO_LIMIT:
            all_limits_hit = False
            break
        elif file_name_count <= tracked_data[FILE_NAME_COUNT_LIMIT][i]:
            all_limits_hit = False
            break
        else:
            all_limits_hit = True
        i += 1
    
    return all_limits_hit


### Get the text that is to be inserted into file name.
###     (edit_details) All the details on how to proceed with the file name edits.
###     (list_index) Current index of looping list.
###     --> Returns a [String] 
def getInsertText(edit_details, list_index = -1):
    
    edit_type = edit_details[EDIT_TYPE] # No get, force error if missing
    modify_data = edit_details[INSERT_TEXT] # No get, force error if missing
    search_options = getOptions(edit_details.get(MATCH_TEXT, ''))
    same_match_index = SAME_MATCH_INDEX in search_options
    insert_text = getText(modify_data) # Always a List
    modify_options = getOptions(modify_data)
    no_repeat_text_list = NO_REPEAT_TEXT_LIST in modify_options
    tracked_data = getTrackedData(edit_details)
    
    insert_text_list_size = len(insert_text)
    
    if list_index > -1 and list_index < insert_text_list_size:
        
        if type(insert_text[list_index]) == tuple: # Dynamic Text
            
            if COUNT in modify_options or COUNT_TO in modify_options:
                
                dynamic_count = getTrackedData(edit_details, FILE_NAME_COUNT, [list_index])
                
                list_index = checkAllAvalibleCountLimits(tracked_data, list_index, insert_text_list_size, same_match_index, no_repeat_text_list)
                
                if list_index > -1:
                    dynamic_count = getTrackedData(edit_details, FILE_NAME_COUNT, [list_index])
                    
                    if COUNT in modify_options:
                        insert_text = getDynamicText(insert_text[list_index], dynamic_count, modify_options)
                    
                    elif COUNT_TO in modify_options:
                        insert_text = insert_text[list_index][STARTING_TEXT]
                
                else:
                    insert_text = False
                    #print('A max count limit hit.')
            
            elif RANDOM_NUMBERS in modify_options or RANDOM_LETTERS in modify_options or RANDOM_SPECIALS in modify_options or RANDOM_OTHER in modify_options:
                
                random_characters = getRandomCharacters(edit_details, list_index)
                
                insert_text = getDynamicText(insert_text[list_index], random_characters, modify_options)
                
                edit_details = updateTrackedData(edit_details, { USED_RANDOM_CHARS : random_characters })
            
            elif REGEX in modify_options: ## TODO
                print('TODO REGEX')
            
            else:
                print('/nYour using dynamic text "(text,1,text)" without using an OPTION informing how to handle it.')
                insert_text = False
        
        else: # Plain Text
            insert_text = insert_text[list_index]
    
    else: ## TODO Index Out Of Bounds, Warn User?
        insert_text = False
    
    if EXTENSION in modify_options and edit_type != RENAME and type(insert_text) != bool:
        if insert_text != '' and insert_text.find('.') != 0:
            insert_text = '.'+insert_text # Add a '.' if missing
    
    #print(insert_text)
    
    return insert_text, edit_details


### Get random characters to be used in creating a new file name.
###     (edit_details) All the details on how to proceed with the file name edits.
###     (list_index) If text list is used provide current index.
###     --> Returns a [String] 
def getRandomCharacters(edit_details, list_index = -1):
    
    if list_index > -1:
        dynamic_text = getText(edit_details[INSERT_TEXT])[list_index][DYNAMIC_TEXT]
    else:
        dynamic_text = getText(edit_details[INSERT_TEXT])[DYNAMIC_TEXT]
    
    modify_options = getOptions(edit_details[INSERT_TEXT])
    random_list = []
    random_characters = ''
    smallest_char_list = None
    
    if even_weighted_random_char_list:
        length_numbers, length_leters, length_special, length_other = 999, 999, 999, 999
        if RANDOM_NUMBERS in modify_options:
            length_numbers = len(list_numbers)
        if RANDOM_LETTERS in modify_options:
            length_letters = len(list_leters)
        if RANDOM_SPECIALS in modify_options:
            length_special = len(list_special)
        if RANDOM_OTHER in modify_options:
            length_other = len(list_other)
        smallest_char_list = min(length_numbers, length_leters, length_special, length_other)
    
    if RANDOM_NUMBERS in modify_options:
        random.shuffle(list_numbers)
        random_list.extend( list_numbers[:smallest_char_list] )
    if RANDOM_LETTERS in modify_options:
        if letter_cases == LOWER:
            random.shuffle(list_leters)
            random_list.extend( list_leters[:smallest_char_list] )
        elif letter_cases == UPPER:
            random.shuffle(list_capital_leters)
            random_list.extend( list_capital_leters[:smallest_char_list] )
        elif letter_cases == LOWER_AND_UPPER:
            list_leters.extend(list_capital_leters)
            random.shuffle(list_leters)
            random_list.extend( list_leters[:smallest_char_list] )
    if RANDOM_SPECIALS in modify_options:
        random.shuffle(list_special)
        random_list.extend( list_special[:smallest_char_list] )
    if RANDOM_OTHER in modify_options:
        random.shuffle(list_other)
        random_list.extend( list_other[:smallest_char_list] )
    
    if type(dynamic_text) == tuple:
        random_length = dynamic_text[0]
    else:
        random_length = int(dynamic_text)
    
    if no_repeat_random_chars:
        random_characters = random.shuffle(random_list)[:random_length]
    else:
        length = 0
        while length < random_length:
            random_characters += random.choice(random_list)
            length += 1
    
    # Check if string of random characters has been used already in current group of file renames.
    used_random_chars = getTrackedData(edit_details, USED_RANDOM_CHARS)
    if random_characters in used_random_chars:
        random_characters = getRandomCharacters(edit_details, insert_text_data)
    
    return random_characters


### Prepare the text to be inserted into file making and changes or text matches before renaming.
### If the same file name is returned then the original file did not match the criteria in the edit details.
###     (file_path) The full path to a file.
###     (edit_details) All the details on how to proceed with the file name edits.
###     --> Returns a [String] 
def insertTextIntoFileName(file_path, edit_details):
    
    match_text = edit_details.get(MATCH_TEXT, '')
    ignore_text = edit_details.get(IGNORE_TEXT, None)
    file_meta_data = getTrackedData(edit_details, CURRENT_FILE_META)
    match_file_meta_data = edit_details.get(MATCH_FILE_META, None)
    match_file_meta_list = getMeta(match_file_meta_data)
    match_file_meta_options = getOptions(match_file_meta_data)
    
    match_text_list, searchable_match_file_name, ignore_text_list, searchable_ignore_file_name = getSearchData(match_text, ignore_text, file_path)
    if match_file_meta_data:
        meta_list_index = getMetaSearchResults(file_meta_data, match_file_meta_list, match_file_meta_options)
    else:
        meta_list_index = 0
    
    insert_text_data = edit_details[INSERT_TEXT]
    text_list_size = 1
    if type(insert_text_data) == dict:
        is_text_list = True if type(insert_text_data.get(TEXT)) == list else False
        if is_text_list:
            text_list_size = len(insert_text_data.get(TEXT))
    if type(insert_text_data) == list:
        is_text_list = True
        text_list_size = len(insert_text_data.get(TEXT))
    else:
        is_text_list = False
    
    search_options = getOptions(match_text)
    ignore_options = getOptions(ignore_text)
    modify_options = getOptions(insert_text_data)
    no_repeat_text_list = NO_REPEAT_TEXT_LIST in modify_options
    
    match_limit = getOptions(match_text, MATCH_LIMIT, ALL)
    match_limit = ALL if match_limit <= NO_LIMIT else match_limit
    same_match_text_index = SAME_MATCH_INDEX in search_options
    same_meta_match_index = SAME_MATCH_INDEX in match_file_meta_options
    
    tracked_data = edit_details[TRACKED_DATA]
    
    renamed_number = getTrackedData(edit_details, FILES_RENAMED, [AMOUNT])
    renamed_limit = getTrackedData(edit_details, FILES_RENAMED, [LIMIT])
    skip_warning_smi = getTrackedData(edit_details, SKIP_WARNINGS, [0])
    
    new_file_name = file_path.name # Start with orginal current file name
    
    i = -1
    for match_text in match_text_list: # Loop breaks on first match found
        i += 1
        
        if same_match_text_index or same_meta_match_index:
            ## TODO: Which is best order of importance? Or warn user if multple SAME_MATCH_INDEX in use.
            if same_meta_match_index:
                match_index = meta_list_index
                match_list_size = len(match_file_meta_list)
            if same_match_text_index:
                match_index = i
                match_list_size = len(match_text_list)
            
            # Fix out of bound indexes
            if match_list_size > text_list_size:
                match_index = resetIfMaxed(match_index, text_list_size)
            
            #if match_list_size != text_list_size and not repeat_text_list and not skip_warning_smi:
            if match_list_size != text_list_size and not skip_warning_smi:
                ## TODO: use a windows message box?
                print('\nYour using the SAME_MATCH_INDEX option, but your MATCH_ list is larger or smaller than your INSERT_TEXT list.')
                print('This may lead to undesirable results if you\'re trying to line up your matches and text lists.')
                #print('Try using the REPEAT_TEXT_LIST (INSERT_TEXT) option next time if your using dynamic text like COUNT, RANDOM, etc.')
                input('If you wish to continue anyways press [ Enter ]...')
                skip_warning_smi = True
        
        elif is_text_list:
            if not no_repeat_text_list:
                renamed_number = resetIfMaxed(renamed_number, text_list_size)
            match_index = renamed_number # Move index forward +1 after a rename.
        
        else:
            match_index = 0
        
        #if debug: print('match_index: %s' % match_index)
        insert_text, edit_details = getInsertText(edit_details, match_index)
        
        if type(insert_text) != bool and searchable_match_file_name.find(match_text) > -1 and meta_list_index > -1 :
            
            match_size = len(match_text)
            index_matches = []
            index_match = 0
            start = 0
            end = None
            if match_size > 0:
                while index_match > -1:
                    index_match = searchable_match_file_name.rfind(match_text, start, end) # Reverse Find
                    end = index_match
                    index_matches.append(index_match)
                index_matches.pop(-1)
            
            ingnore = len(index_matches) - match_limit
            ingnore = 0 if ingnore < 0 else ingnore
            while ingnore > 0:
                if SEARCH_FROM_RIGHT in search_options:
                    index_matches.pop(-1)
                else:
                    index_matches.pop(0)
                ingnore -= 1
            #if debug: print(index_matches)
            
            placement = getPlacement(insert_text_data)
            
            # Look for ignore text in file name.
            ignore_match = False
            for ignore_text in ignore_text_list:
                if EXTENSION in ignore_options:
                    if searchable_ignore_file_name == ignore_text:
                        ignore_match = True # Ignore match made, skip this file rename.
                        break
                else:
                    if searchable_ignore_file_name.find(ignore_text) > -1:
                        ignore_match = True # Ignore match made, skip this file rename.
                        break
            
            if not ignore_match:
                if edit_details[EDIT_TYPE] == ADD:
                    
                    # Add extension if...
                    if EXTENSION in modify_options:
                        if EXTENSION in search_options:
                            if match_text == searchable_match_file_name: # A perfect match is made
                                new_file_name = file_path.name + insert_text # Only to the end, placement is ignored.
                        else:
                            new_file_name = file_path.name + insert_text # Only to the end, placement is ignored.
                    
                    # Add extension if...
                    elif EXTENSION in search_options:
                        if match_text == searchable_match_file_name: # A perfect match is made
                            new_file_name = addToFileName(file_path, insert_text, placement[0]) # Simple placement OF_FILE_NAME only
                    
                    # Else use normal placement options...
                    elif placement[1] == OF_MATCH:
                        for index in index_matches:
                            
                            if placement[0] == START: # or LEFT
                                new_file_name = new_file_name[:index] + insert_text + new_file_name[index:]
                            
                            elif placement[0] == END: # or RIGHT
                                new_file_name = new_file_name[:index + match_size] + insert_text + new_file_name[index + match_size:]
                            
                            elif placement[0] == BOTH:
                                new_file_name = new_file_name[:index] + insert_text + new_file_name[index:index + match_size] + insert_text + new_file_name[index + match_size:]
                    
                    else: # placement[1] == OF_FILE_NAME: # Default
                        new_file_name = addToFileName(file_path, insert_text, placement[0])
                
                elif edit_details[EDIT_TYPE] == REPLACE:
                    
                    # Replace extension only if...
                    if EXTENSION in search_options:
                        if match_text == searchable_match_file_name: # A perfect match is made
                            new_file_name = file_path.stem + insert_text
                    
                    elif EXTENSION in modify_options: # Any match is made
                        new_file_name = file_path.stem + insert_text
                    
                    else:
                        for index in index_matches:
                            new_file_name = new_file_name[:index] + insert_text + new_file_name[index + match_size:]
                
                elif edit_details[EDIT_TYPE] == RENAME:
                    
                    # Rename entire file name plus extension if...
                    if EXTENSION in search_options:
                        if match_text == searchable_match_file_name: # A perfect match is made
                        
                            if EXTENSION in modify_options and insert_text.find('.') > -1: # An .extension is included
                                new_file_name = insert_text
                            else:
                                new_file_name = insert_text + file_path.suffix
                        
                        #else: # No perfect match, no rename
                    
                    elif EXTENSION in modify_options and insert_text.find('.') > -1: # An .extension is included
                        new_file_name = insert_text
                    else:
                        new_file_name = insert_text + file_path.suffix
            
            break # If here then a match was found so break loop
    
    edit_details = updateTrackedData(edit_details, { CURRENT_LIST_INDEX : match_index, CURRENT_FILE_RENAME : new_file_name, SKIP_WARNINGS : [0, skip_warning_smi] })
    
    #if debug: print(new_file_name)
    
    return edit_details


### Add text to file name using a simple placement.
###     (file_path) The full path to a file.
###     (add_text) The text to add to the file name.
###     (placement) Where to place the added text.
###     --> Returns a [String] 
def addToFileName(file_path, add_text, placement):
    if placement == START: # or LEFT
        new_file_name = f'{add_text}{file_path.stem}{file_path.suffix}'
    elif placement == END: # or RIGHT
        new_file_name = f'{file_path.stem}{add_text}{file_path.suffix}'
    elif placement == BOTH:
        new_file_name = f'{add_text}{file_path.stem}{add_text}{file_path.suffix}'
    elif placement == EXTENSION:
        new_file_name = f'{file_path.name}{add_text}'
    else:
        new_file_name = file_path.name
    return new_file_name


### Check if a file alredy exists and if it does, ask user how to proceed.
###     (file_path) The full path to a file.
###     (org_file_path) The full path the file before it's rename to check if it's the same name.
###     --> Returns a [Integer] Constant
def checkIfFileExist(file_path, org_file_path = None):
    does_file_exist = TRY_AGAIN
    
    if str(file_path) == str(org_file_path):
        does_file_exist = SAME_NAME
    
    while does_file_exist == TRY_AGAIN:
        if Path.exists(file_path):
            
            if file_path == org_file_path: # If here the file rename must have had a letter case change.
                does_file_exist = NO
            
            else:
                if sys.platform == 'win32':
                    print('--File Name Already Exists: %s' % (file_path))
                    file_already_exist_text = ('File Already Exists: "%s" \n\nSkip this file and continue?' % (file_path))
                    file_already_exist_user_input = windll.user32.MessageBoxW(0, file_already_exist_text, "File Renaming Failed!", 0x00001016)
                else:
                    print('--File Name Already Exists: %s' % (file_path))
                    file_already_exist_user_input = input('Skip this file and continue? [ (C)ancel / (T)ryAgain / (S)kip ]')
                
                does_file_exist = strToIntConstant(file_already_exist_user_input, 'file_saving')
        else:
            does_file_exist = NO
    
    return does_file_exist


### Rename a file...
###     (file_path) The full path to file.
###     (new_file_path) The full path to file.
###     (edit_details) All the details on how to proceed with the file name edits. 
###     --> Returns a [Dictionary] 
def renameFile(file_path, new_file_path, edit_details):
    
    current_list_index = getTrackedData(edit_details, CURRENT_LIST_INDEX)
    
    does_file_exist = checkIfFileExist(new_file_path, file_path)
    
    if does_file_exist == CANCEL: # Will throw error, but will stop any further renaming.
        print('Canceling any further renaming and closing...')
        new_file_path = file_path.rename(new_file_path) # Error
    
    elif does_file_exist == NO: # Actually renaming file
        new_file_path = file_path.rename(new_file_path)
        edit_details = updateTrackedData(edit_details, { FILES_RENAMED : +1, ORG_FILE_PATHS : file_path, NEW_FILE_PATHS : new_file_path })
        file_renamed = True
    
    elif does_file_exist == CONTINUE: # Skip this count (+1) and try renaming file again (recursively).
        file_renamed = False
        edit_details = updateTrackedData(edit_details, { FILE_NAME_COUNT : [current_list_index, +1], SKIPPED_FILES : new_file_path })
        
        edit_details = createNewFileName(file_path, edit_details)
        
        does_file_exist = NO
    
    elif does_file_exist == SAME_NAME: # Skip this file and continue count, but don't add to renamed files.
        file_renamed = True
    
    if file_renamed:
        if does_file_exist == CONTINUE:
            print('--File Name Already Exists: %s\\ [ %s ]' % (new_file_path.parent, new_file_path.name))
        if does_file_exist == SAME_NAME:
            print('--File Already Renamed: %s\\ [ %s ]' % (new_file_path.parent, new_file_path.name))
            print('--You may have ran this script twice in a row.')
        else:
            print('--File Renamed From: %s\\%s to [ %s ]' % (new_file_path.parent, file_path.name, new_file_path.name))
        
        edit_details = updateTrackedData(edit_details, { FILE_NAME_COUNT : [current_list_index, +1] })
    
    elif does_file_exist != NO:
        print('--File Not Renamed: %s' % (file_path))
    
    return edit_details


### Update any files that have links to the renamed files to prevent broken links in whatever app that use the renamed files.
###     (linked_file) The full path to a file with links.
###     (old_file_path) A String of the full path to a file before renaming.
###     (new_file_path) A String of the full path to a file after renaming.
###     --> Returns a [Boolean] 
def updateLinksInFile(linked_file, old_file_path, new_file_path):
    linked_file = Path(linked_file)
    
    ##TODO: Check file extensions and pick the proper encoding. xml, json = utf-8, txt = ascii
    try:
        text_encoding = 'ascii'
        read_data = linked_file.read_text(encoding=text_encoding)
    except:
        try:
            text_encoding = 'utf-8'
            read_data = linked_file.read_text(encoding=text_encoding)
        except:
            print('Failed to open linked file: [ %s ]' % linked_file)
            print('Posible text encoding issue. Script only supports ascii and utf-8 text encoding.')
            return False
    
    write_data = read_data
    
    # Check for all style of slashes in links
    old_file_path_esc = old_file_path.replace('\\', '\\\\')
    new_file_path_esc = new_file_path.replace('\\', '\\\\')
    old_file_path_rev = old_file_path.replace('\\', '/')
    new_file_path_rev = new_file_path.replace('\\', '/')
    
    links_find = [old_file_path, old_file_path_esc, old_file_path_rev]
    links_replace = [new_file_path, new_file_path_esc, new_file_path_rev]
    
    # Check for special characters & = &amp;
    if old_file_path.find('&') > -1:
        old_file_path_amp = old_file_path.replace('&', '&amp;')
        new_file_path_amp = new_file_path.replace('&', '&amp;')
        old_file_path_amp_esc = old_file_path_amp.replace('\\', '\\\\')
        new_file_path_amp_esc = new_file_path_amp.replace('\\', '\\\\')
        old_file_path_amp_rev = old_file_path_amp.replace('\\', '/')
        new_file_path_amp_rev = new_file_path_amp.replace('\\', '/')
        links_find.append(old_file_path_amp)
        links_find.append(old_file_path_amp_esc)
        links_find.append(old_file_path_amp_rev)
        links_replace.append(new_file_path_amp)
        links_replace.append(new_file_path_amp_esc)
        links_replace.append(new_file_path_amp_rev)
    
    i = 0
    while i < len(links_find):
        if read_data.find(links_find[i]) > -1:
            write_data = read_data.replace(links_find[i], links_replace[i])
            i = 99
        i += 1
    
    if read_data == write_data:
        data_changed = False
    else:
        data_changed = True
        linked_file.write_text(write_data, encoding=text_encoding)
    
    return data_changed


### Update log file and record files renamed.
###     (edit_details) The edit details with the TRACKED_DATA key added.
###     (log_revert) Is this a file rename revert log drop?
###     --> Returns a [Boolean] 
def updateLogFile(edit_details, log_revert = False):
    
    tracked_data = edit_details.get(TRACKED_DATA)
    if not tracked_data:
        return False
    
    files_reviewed = getTrackedData(edit_details, FILES_REVIEWED, [AMOUNT])
    files_renamed = getTrackedData(edit_details, FILES_RENAMED, [FULL_AMOUNT])
    
    if files_renamed > 0:
        file_updated = True
    else:
        print('Log File Not Created. Files Renamed: 0')
        return False
    
    linked_files = edit_details.get(LINKED_FILES, [])
    org_file_paths = getTrackedData(edit_details, LOG_DATA, [ORG_FILE_PATHS])
    new_file_paths = getTrackedData(edit_details, LOG_DATA, [NEW_FILE_PATHS])
    linked_files_updated = getTrackedData(edit_details, LOG_DATA, [LINKED_FILES_UPDATED])
    completion_time = getTrackedData(edit_details, LOG_DATA, [END_TIME]) - getTrackedData(edit_details, LOG_DATA, [START_TIME])
    #completion_time = 0
    
    timestamp = datetime.now().timestamp()
    date_time = datetime.fromtimestamp(timestamp)
    time = datetime.fromtimestamp(completion_time)
    str_date_time = date_time.strftime('On %m/%d/%Y at %I:%M:%S %p')
    str_date_time_file_name = date_time.strftime('%Y-%m-%d_%H.%M.%S')
    str_completion_time = time.strftime('%S.%f')
    text_lines = []
    text_lines.append( '============================' )
    text_lines.append( str_date_time )
    text_lines.append( '============================' )
    
    text_lines.append( '\nTotal File Names Reviewed: [ ' + str(files_reviewed) + ' ]' )
    text_lines.append( 'Amount of Files Renamed: [ ' + str(files_renamed) + ' ]' )
    text_lines.append( 'Amount of Files Not Renamed: [ ' + str(files_reviewed - files_renamed) + ' ]' )
    text_lines.append( 'Task Completed In: [ ' + str_completion_time + ' ]' )
    
    print_text_lines = text_lines.copy()
    print('\n')
    print('\n'.join(print_text_lines))
    
    if create_log_file:
        
        this_file = Path(__file__)
        
        if Path(log_dir_name).is_absolute():
            log_dir_path = Path(log_dir_name)
        else:
            log_dir_path = Path(PurePath().joinpath(this_file.parent, log_dir_name))
        
        log_dir_path.mkdir(parents=True, exist_ok=True)
        
        if not Path.exists(log_dir_path):
            print('Failed to create log directory.')
            ## TODO ask to save logs in root dir?
            return False
        
        log_file_name = str_date_time_file_name + log_file_name_suffix
        log_file_name_path = Path(PurePath().joinpath(log_dir_path, log_file_name))
        
        text_lines.append( '\n\nLinked Files Updated:' )
        n = 0
        for linked_file in linked_files:
            n += 1
            text_lines.append( '    ' + str(n) + '. ' + str(linked_file) )
        if not linked_files:
            text_lines.append( '    None' )
        
        if log_revert:
            text_lines.append( '\n\nFiles Renamed (Reverted):' )
        else:
            text_lines.append( '\n\nFiles Renamed:' )
        
        i = 0
        root = ''
        links = ''
        links_updated_str = ''
        while i < len(org_file_paths):
            if org_file_paths[i].parent != root:
                root = org_file_paths[i].parent
                text_lines.append( '\nRoot Path: ' + str(root))
            if len(linked_files) > 0:
                x = 0
                links_updated_str = '  | Links Updated In File #: '
                links_updated = ''
                while x < len(linked_files_updated[i]):
                    links_updated += str(x+1) + ', ' if linked_files_updated[i][x] else ''
                    x += 1
                links_updated = links_updated.rstrip(', ')
                links_updated_str = links_updated_str + links_updated if links_updated != '' else ''
            text_lines.append( '--> ' + str(org_file_paths[i].name) + ' --> ' + str(new_file_paths[i].name) + links_updated_str )
            i += 1
        
        # Add edit details or preset used to log file.
        if log_edit_details and not log_revert:
            #preset_str = ' (preset' + str(preset_options.index(preset)) + ')' if use_preset else ''
            preset_str = ' (preset' + str(selected_preset) + ')'
            text_lines.append( '\n\nEdit Criteria Used:' + preset_str)
            text_lines.extend(displayPreset(edit_details, -1, True))
        
        # Write Log File
        log_file_name_path.write_text('\n'.join(text_lines), encoding=None, errors=None, newline=None)
        print('Check log for more details.')
        os.startfile(log_file_name_path) # Open log file for viewing
        
        # Delete older log files if limit hit
        if log_file_limit != NO_LIMIT:
            log_files = []
            for root, dirs, files in os.walk(log_dir_path):
                for log_file in files:
                    if log_file.find(log_file_name_suffix) > -1:
                        log_files.append(log_file)
                break
            
            log_files_meta_sorted = getFileMetaData(log_files, {DATE_MODIFIED : ASCENDING}, root)
            
            log_file_amount = len(log_files_meta_sorted)
            if log_file_amount >= log_file_limit:
                i = log_file_amount - log_file_limit
                delete_logs = log_files_meta_sorted[:i]
                
                if log_file_limit == 0: delay.sleep(1) # Allow 1 second to finish file writing and opening before deleting it.
                
                for log in delete_logs:
                    log[FILE_META_PATH].unlink(missing_ok=True)
                    if debug: print('Old Log File Deleted: [ %s ]' % log[FILE_META_PATH])
    
    return file_updated


### Change specific user inputs (answer to a question) into a "True or False" Boolean.
###     (user_input) The String with variations of "yes or no" text in them.
###     --> Returns a [Boolean] True or False
def yesTrue(user_input):
    user_input = user_input.casefold()
    if 'yes'.find(user_input) > -1:
        response = True
    else:
        response = False
    return response


### Change specific user inputs (answer to a question) into an integer constant.
###     (user_input) The user input from a question asked.
###     (category) The category of the question ask.
###     --> Returns a [Integer]
def strToIntConstant(user_input, category):
    user_input = str(user_input).casefold()
    number = NONE
    '''if category == 'edit_type':
        if user_input == 'a' or user_input == 'add':
            number = ADD
        elif user_input == 'r' or user_input == 'replace':
            number = REPLACE
    elif category == 'placement':
        if user_input == 's' or user_input == 'start':
            number = START
        elif user_input == 'e' or user_input == 'end':
            number = END
        elif user_input == 'b' or user_input == 'both':
            number = BOTH
    elif category == 'search_from':
        if user_input == 'l' or user_input == 'left':
            number = LEFT
        elif user_input == 'r' or user_input == 'right':
            number = RIGHT'''
    if category == 'file_saving':
        if user_input == '2' or 'cancel'.find(user_input) > -1:
            number = CANCEL
        elif user_input == '10' or 'tryagain'.find(user_input) > -1:
            number = TRY_AGAIN
        elif user_input == '11' or 'skip'.find(user_input) > -1:
            number = SKIP
    return number


### Get proper user preset selection.
###     (string_num) A user typed String to change into an Integer or keep blank ('').
###     --> Returns a [Integer]
def getUserPresetSelection(string_num):
    string_num = string_num.casefold()
    if string_num == '':
        number = ''
    elif 'showall'.find(string_num) > -1:
        number = ALL
    elif string_num.isnumeric():
        number = int(string_num)
    else:
        number = NONE
    return number


### Convert all the integers used in Dictionary presets into readable text.
###     (key) Option key
###     (value) Option value
###     (parent_key) The Parent Option's key 
###     --> Returns a [String] 
def intToStrText(key, value, parent_key = None):
    if type(value) != list and type(value) != tuple:
        value = [value]
    text = str(value)
    if type(key) == int:
        text = str(key)
        
        if parent_key == None:
            if key == EDIT_TYPE:
                text = 'Edit Type              '
            elif key == MATCH_TEXT:
                text = 'Text To Match          '
            elif key == IGNORE_TEXT:
                text = 'Text To Ignore         '
            elif key == MATCH_FILE_CONTENTS:
                text = 'Match Contents of File '
            elif key == MATCH_FILE_META:
                text = 'Match File Meta Data   '
            elif key == INSERT_TEXT:
                text = 'Text To Insert         '
            elif key == SOFT_RENAME_LIMIT:
                text = 'File Rename Soft Limit '
            elif key == HARD_RENAME_LIMIT:
                text = 'File Rename Hard Limit '
            elif key == LINKED_FILES:
                text = 'Files With Links       '
            elif key == INCLUDE_SUB_DIRS:
                text = 'Include Sub Directories'
            elif key == PRESORT_FILES:
                text = 'Pre-Sort Files         '
            elif key == TRACKED_DATA:
                text = 'Data That Is Tracked   '
        
        elif parent_key == MATCH_TEXT or parent_key == IGNORE_TEXT or parent_key == MATCH_FILE_CONTENTS or parent_key == MATCH_FILE_META or parent_key == INSERT_TEXT:
            if key == TEXT:
                text = 'TEXT : ' + str(value)
            if key == META:
                text = 'META : '# + str(value)
                if type(value) != list:
                    value = [value]
                for object in value:
                    if type(object) == dict:
                        for name, val in object.items():
                            
                            if name == FILE_META_SIZE or name == FILE_META_ACCESS or name == FILE_META_MODIFY or name == FILE_META_CREATE:
                                if name == FILE_META_SIZE:
                                    text += '{ Get Size Of Files '
                                elif name == FILE_META_ACCESS:
                                    text += '{ Get Dates Of Files Last Accessed '
                                elif name == FILE_META_MODIFY:
                                    text += '{ Get Dates Of Files Last Modified '
                                elif name == FILE_META_CREATE:
                                    text += '{ Get Dates Of Files Created '
                                
                                if name == FILE_META_SIZE:
                                    if val == EXACT_MATCH:
                                        text += 'Exactly '
                                    if val == LESS_THAN:
                                        text += 'Less Than '
                                    elif val == MORE_THAN:
                                        text += 'More Than '
                                else:
                                    if val == EXACT_MATCH:
                                        text += 'Exactly On '
                                    if val == OLDER_THAN:
                                        text += 'Older Than '
                                    elif val == WITHIN_THE_PAST:
                                        text += 'Within The Past '
                            
                            if name == GB:
                                text += str(val) + ' Gigabytes, '
                            elif name == MB:
                                text += str(val) + ' Megabytes, '
                            elif name == KB:
                                text += str(val) + ' Kilobytes, '
                            elif name == BYTES:
                                text += str(val) + ' Bytes '
                            
                            if name == YEAR:
                                text += 'Year: ' + str(val) + ', '
                            if name == MONTH:
                                text += 'Month: ' + str(val) + ', '
                            if name == DAY:
                                text += 'Day: ' + str(val) + ', '
                            if name == HOUR:
                                text += 'Hour: ' + str(val) + ', '
                            if name == MINUTE:
                                text += 'Minute: ' + str(val) + ', '
                            if name == SECOND:
                                text += 'Second: ' + str(val) + ', '
                            if name == MILLISECOND:
                                text += 'Millasecond: ' + str(val) + ' '
                            if name == MICROSECOND:
                                text += 'Microsecond: ' + str(val) + ' '
                        
                        text = text.rstrip(', ')
                        text += ' }'
            
            if key == OPTIONS:
                text = '\n                              OPTIONS : '
                if MATCH_CASE in value:
                    text += 'Search Case Sensitive, '
                if NO_MATCH_CASE in value:
                    text += 'Search Not Case Sensitive, '
                if SEARCH_FROM_RIGHT in value:
                    text += 'Start Search From Right Side, '
                if COUNT in value:
                    text += 'Add An Incrementing Number To Text, '
                if COUNT_TO in value:
                    text += 'Limit Specific File Renames Made, '
                if EXTENSION in value and parent_key == MATCH_TEXT:
                    text += 'Only Search The Extension, '
                if EXTENSION in value and parent_key == IGNORE_TEXT:
                    text += 'Ignore This Extension, '
                if EXTENSION in value and parent_key == INSERT_TEXT:
                    text += 'Allow Extension To Be Modified, '
                if RANDOM_NUMBERS in value:
                    text += 'Add Random Numbers, '
                if RANDOM_LETTERS in value:
                    text += 'Add Random Letters, '
                if RANDOM_SPECIALS in value:
                    text += 'Add Random Special Characters, '
                if RANDOM_OTHER in value:
                    text += 'Add Random Other Characters, '
                if REGEX in value:
                    text += 'Regular Expressions, '
                if SAME_MATCH_INDEX in value:
                    text += 'Use Match Index While Selecting From Insert Lists, '
                if NO_REPEAT_TEXT_LIST in value:
                    #text += 'Once End of Text List Reached Repeat List, '
                    text += 'Do Not Repeat Text List Once End Reached, '
                for item in value:
                    if type(item) == tuple:
                        if MATCH_LIMIT in item:
                            text += 'Limit Matches to ' + str(item[1]) + ', '
                        if MINIMUM_DIGITS in item:
                            text += 'Minimum ' + str(item[1]) + ' Digits, '
                        if RANDOM_SEED in item:
                            text += 'Random Seed used ' + str(item[1]) + ', '
                text = text.rstrip(', ')
            
            if key == PLACEMENT:
                text = '\n                              PLACEMENT : '
                if START in value:
                    text += 'Start'
                elif END in value:
                    text += 'End'
                elif BOTH_ENDS in value:
                    text += 'Both Ends'
                if OF_FILE_NAME in value:
                    text += ' of File Name'
                elif OF_MATCH in value:
                    text += ' of Match'
        
        elif parent_key == PRESORT_FILES:
            if key == ALPHABETICALLY:
                text = 'Alphabetically '
            elif key == FILE_SIZE:
                text = 'By File Size '
            elif key == DATE_ACCESSED:
                text = 'By Date Last Accessed '
            elif key == DATE_MODIFIED:
                text = 'By Date Last Modified '
            elif key == DATE_CREATED:
                text = 'By Date Created '
            elif key == DATE_META_MODIFIED:
                text = 'By Date Meta Data Last Modified '
            if value == ASCENDING:
                text += 'In Ascending Order'
            elif value == DESCENDING:
                text += 'In Descending Order'
        
        elif parent_key == TRACKED_DATA:
            if key == FILES_REVIEWED:
                text = 'Files Reviewed So Far : ' + str(value)
            if key == FILES_RENAMED:
                text = '\n                              Files Renamed So Far : ' + str(value)
            if key == DIRECTORY_FILES_RENAMED:
                text = '\n                              Directory Files Renamed So Far : ' + str(value)
            if key == INDIVIDUAL_FILES_RENAMED:
                text = '\n                              Individual Files Renamed So Far : ' + str(value)
            if key == INDIVIDUAL_FILE_GROUP:
                text = '\n                              Is Individual File Group Active : ' + str(value)
            if key == FILE_NAME_COUNT:
                text = '\n                              Current File Count Number : ' + str(value)
            if key == FILE_NAME_COUNT_LIMIT:
                text = '\n                              File Count Number Max : ' + str(value)
            if key == CURRENT_LIST_INDEX:
                text = '\n                              Current List Index : ' + str(value)
            if key == CURRENT_FILE_RENAME:
                text = '\n                              Current File Name : ' + str(value)
            if key == CURRENT_FILE_META:
                text = '\n                              Current File Meta Data : ' + str(value)
            if key == USED_RANDOM_CHARS:
                text = '\n                              Used Random Characters : ' + str(value)
            if key == SKIPPED_FILES:
                text = '\n                              Files To Skip : ' + str(value)
            if key == SKIP_WARNINGS:
                text = '\n                              User Warning Skips : ' + str(value)
            if key == LOG_DATA:
                text = '\n                              Log Data : '
                text += '' if show_log_data else '[Not Shown]'
                if type(value[0]) == dict and show_log_data:
                    for key, items in value[0].items():
                        if key == ORG_FILE_PATHS:
                            text += 'ORGINAL FILE PATHS : ' + str(items) + ', '
                        elif key == NEW_FILE_PATHS:
                            text += 'NEW (RENAMED) FILE PATHS : ' + str(items) + ', '
                        elif key == LINKED_FILES_UPDATED:
                            text += 'LINKED FILES UPDATED : ' + str(items) + ', '
                        elif key == START_TIME:
                            text += 'START TIME: ' + str(items) + ', '
                        elif key == END_TIME:
                            text += 'END TIME : ' + str(items) + ', '
                    text = text.rstrip(', ')
    
    if key == None:
        if type(value) == str:
            text = f'"{str(value)}"'
        elif parent_key == EDIT_TYPE:
            if ADD in value:
                text = 'Add'
            elif REPLACE in value:
                text = 'Replace'
            elif RENAME in value:
                text = 'Rename'
        else:
            text = str(value)
    
    return text


### Reset a number back to 0 if it hits the max. If over max, minus the max until under max.
###     (number) The number.
###     (max) Max limit to the number.
###     --> Returns a [Integer] 
def resetIfMaxed(number, max):
    if max == 1:
        number = 0
    elif number >= max:
        number = number - max
        number = resetIfMaxed(number, max)
    return number


### Drop one of more files and directories here to be renamed via presets or after answering a series of questions regarding how to properly rename said files.
###     (files) A List of files, which can include directories pointing to many more files.
###     --> Returns a [Integer] Number of files renamed.
def drop(files):
    
    global selected_preset
    start_reverting_renames = False
    files_renamed = 0
    
    # If script is ran on it's own then ask for a file to rename.
    if not files:
        files = input('No files or directories found, drop one or more here to proceed: ')
    
    if type(files) != list:
        files = [files]
    
    if len(files) == 1:
        
        files[0] = files[0].replace('"','') # Remove Quotes
        
        if files[0].find(':\\', 3) > -1:
            
            # Multiple files dropped into prompt, split them up between drive letters.
            split_files = []
            start = 0
            end = None
            while start > -1:
                start = files[0].find(':\\', start, end) + 1
                end = files[0].find(':\\', start, end) - 1
                if end > -1:
                    split_files.append( files[0][ start-2 : end ] )
                    end = None
                else:
                    split_files.append( files[0][ start-2 : ] )
                    start = -1
            
            files = split_files
    
    # Check if files or directories exist and remove any that don't exist.
    i = len(files)-1
    while i > -1:
        if not os.path.exists(files[i]):
            print('\nThis file or directory does not exists: [ %s ]' % files[i])
            if i > 0:
                input('\nPress [ Enter ] to continue on with additional dropped files or directories...')
            files.pop(i)
        i -= 1
    
    if debug: print(files)
    
    if files:
        
        print('\nNumber of Files or Directories Dropped: [ %s ]' % len(files))
        
        # Check if first file drop is a log file and ask if it is ok to start reverting file renames.
        if files[0].find(log_dir_name) > -1 and files[0].find(log_file_name_suffix) > -1:
            start_reverting_renames = input('\nA log file was detected, do you wish to revert the file renames made in this log file? [ Yes / No ] ')
            start_reverting_renames = yesTrue(start_reverting_renames)
        
        # Either reverting renames made in log files OR do normal file renaming to dropped files.
        if start_reverting_renames:
            
            # Make sure log files are sorted in order of when the renames were made.
            files_meta = getFileMetaData(files, {DATE_MODIFIED : DESCENDING})
            
            for log_file in files_meta[0]:
                revert_files_meta, edit_details = getRenameRevertFilesAndEditDetails(log_file)
                
                if revert_files_meta:
                    
                    # Start Reverting File Renames...
                    edit_details_copy = startingFileRenameProcedure(revert_files_meta, edit_details)
                    files_renamed += getTrackedData(edit_details_copy, FILES_RENAMED, [FULL_AMOUNT])
                    
                    if debug: displayPreset(edit_details_copy)
                    updateLogFile(edit_details_copy, True)
                    if len(files_meta[0]) > 1:
                        delay.sleep(1) # Log files are named using time so wait a second to make sure next log file name is +1 second.
                
                else:
                    print('\nThe files in this log file no longer exist: [ %s ]' % log_file[FILE_META_PATH].name)
                    print('You may have already reverted, renamed or deleted these files. ')
        
        else:
            
            # Get User Preset Selection
            preset_loop = loop
            while preset_loop:
                displayPreset(preset_options, selected_preset)
                preset_selection = input('Continue with this Preset [ Enter ] or choose another? [ # ] or [ (S)how(A)ll ]: ')
                preset_selection = getUserPresetSelection(preset_selection)
                
                if preset_selection == ALL:
                    displayPreset(preset_options)
                    preset_selection = input('Select a Preset [ # ]: ')
                    preset_selection = getUserPresetSelection(preset_selection)
                
                elif preset_selection == '':
                    preset_selection = selected_preset
                    preset_loop = False
                
                if preset_selection < len(preset_options) and preset_selection > NONE:
                    selected_preset = preset_selection
                else:
                    print('That Preset Doesn\'t Exist.')
            
            print('\nPreset [ #%s ] Selected' % selected_preset)
            edit_details = preset_options[selected_preset]
            
            # Presort Files
            files_meta = getFileMetaData(files, edit_details.get(PRESORT_FILES, None))
            
            include_sub_dirs = edit_details.get(INCLUDE_SUB_DIRS, False)
            
            # Start Renaming Files...
            edit_details_copy = startingFileRenameProcedure(files_meta, edit_details, include_sub_dirs)
            files_renamed = getTrackedData(edit_details_copy, FILES_RENAMED, [FULL_AMOUNT])
            
            # Show and record details of file renames.
            if debug: displayPreset(edit_details_copy)
            updateLogFile(edit_details_copy)
    
    else:
        print('\nNo Existing Files or Directories Found.')
    
    return files_renamed


### Script Starts Here
if __name__ == '__main__':
    print(sys.version)
    print('\n==============================')
    print('Batch File Renamer by JDHatten')
    print('==============================\n')
    assert sys.version_info >= MIN_VERSION, f"This Script Requires Python v{MIN_VERSION_STR} or Newer"
    
    # Testing: Simulating File Drops
    #ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces')
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces\\file - file - file.txt')
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces\\sub1')
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces\\sub1\\sub2')
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces\\sub2')
    #sys.argv.append(os.path.join(ROOT_DIR,'Logs of File Renames'))
    
    files_renamed = drop(sys.argv[1:])
    print('\nTotal number of files renamed: [ %s ]' % (files_renamed))
    
    if loop:
        new_file = 'startloop'
        prev_files_renamed = 0
        while new_file != '':
            new_file = input('\nDrop more files or directories here to go again or just press enter to quit: ')
            if new_file != '':
                files_renamed += drop(new_file)
            if files_renamed > prev_files_renamed:
                print('\nTotal number of files renamed: [ %s ]' % (files_renamed))
                prev_files_renamed = files_renamed
    
