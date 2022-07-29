#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Batch File Renamer by JDHatten
    This script will rename one or more files either by adding new text or replacing text in the file names.
    Adding text can be placed at the start, end, or both sides of a file name the minus extension.
    Replacing text will replace the first or all instances of matched text in a file name including the extension.

Usage:
    Simply drag and drop one or more files or directories onto the script.
    Script can be opened directly but only one file or directory may be dropped/added at once.

TODO:
    [] Rename directories too
    [] Create a log of files renamed, time of completion, etc.
    [DONE] Loop script after finishing and ask to drop another file before just closing.
    [DONE] When replacing only one or more but not all matched strings start searching from the right/end of string.
    [DONE] Preset options
    [] Better handling of overwriting files
    [] Special search and edits. Examples: 
        Find file names with a string then add another string at end of the file name.
        Find file names with a string then rename entire file name and stop/return/end.
        Find file names with a string then add another string specifically next to matched string.
        Make use of regular expressions.  This could get complex.
        [] Add an iterated number to the end of the file names.
        Find specific file names and only change the extention
        
'''

from pathlib import Path, PurePath
import os
#import re
import sys
if sys.platform == "linux" or sys.platform == "linux2":
    print('Linux')
elif sys.platform == "darwin":
    print('OS X')
elif sys.platform == "win32":
    print('Windows')
    from ctypes import windll


#CUR_VERSION_STR = ".".join(map(str, sys.version_info[:3]))
MIN_VERSION = (3,8,0)
MIN_VERSION_STR = '.'.join([str(n) for n in MIN_VERSION])

ADD = 0
REPLACE = 1
RENAME = 2
START = 3
END = 4
BOTH = 5
LEFT = 6
RIGHT = 7

EDIT_TYPE = 0
ADD_TEXT = 1
PLACEMENT = 2
MATCH_TEXT = 3
REPLACE_TEXT = 4
RECURSIVE = 5
SEARCH_FROM = 6
SUB_DIRS = 7

FILE_NAME = 0
EDITS_MADE = 1

FILES_RENAMED = 0
FILE_NAME_COUNT = 1

ALL = 999
NONE = -1
NO = -1
CANCEL = 0
TRY_AGAIN = 1
SKIP = 2
CONTINUE = 2
SAME_NAME = 3

### Modify/Search Options
MATCH_CASE = 0 # Defualt
NO_MATCH_CASE = 1
COUNT = 2 # Iterate a number that is added to a file name. (NOTE: Resets after each drop or directory change.)
RANDOM = 3 ## TODO: Generate random numbers or text that is added to file names.
TEXT_LIST = 4 ## TODO: A List of Strings to search for or add to file names.
REGEX = 5 ## TODO


### After initial drop and file renaming, ask for additional files or just quit the script.
loop = True

### Present Options - Used to skip questions and immediately start renaming all drop files.
### Make sure to select the correct preset in preset_options[#]
use_preset = True

preset0 = {
  EDIT_TYPE     : ADD,      # ADD or REPLACE or RENAME
  ADD_TEXT      : '-F',     # 'Text' to Add -OR- Tuple(Modify Options, 'Text', Integer/Tuple/List, additional 'Text')
  PLACEMENT     : END,      # START, END, or BOTH
  MATCH_TEXT    : '',       # 'Text' to Find  -OR- Tuple(Search Options, text)
  REPLACE_TEXT  : '',       # 'Text' to Replace with -OR- Tuple(Modify Options, 'Text', Integer/Tuple/List, additional 'Text')
  RECURSIVE     : ALL,      # 1-999/ALL
  SEARCH_FROM   : LEFT,     # LEFT or RIGHT
  SUB_DIRS      : True      # True or False
}
preset1 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : '(Text)',
  REPLACE_TEXT  : '[Text]',
  RECURSIVE     : 1,
  SEARCH_FROM   : RIGHT,
  SUB_DIRS      : True
}
preset2 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : '123',
  REPLACE_TEXT  : 'abc',
  RECURSIVE     : ALL,
  SEARCH_FROM   : LEFT,
  SUB_DIRS      : False
}
preset3 = {
  EDIT_TYPE     : ADD,
  ADD_TEXT      : '_(F)',
  PLACEMENT     : END,
  SUB_DIRS      : True
}
preset4 = {
  EDIT_TYPE     : RENAME, ## TODO: only changes name, extention stays the same.  option to change extention too?
  MATCH_TEXT    : (NO_MATCH_CASE, ''),
  REPLACE_TEXT  : (COUNT, 'TextTextText-[', 10, ']', 12), ## TODO: Ending Count (s,e)?
  SUB_DIRS      : True
}
preset5 = {
  EDIT_TYPE     : ADD,
  ADD_TEXT      : (COUNT, '-(', 0, ')'), ## TODO
  PLACEMENT     : END,
  SUB_DIRS      : True
}
preset6 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : (MATCH_CASE, 'tex'),
  REPLACE_TEXT  : (COUNT, '(', 0, ')'),
  RECURSIVE     : 4,
  SEARCH_FROM   : RIGHT,
  SUB_DIRS      : False
}
preset_options = [preset0,preset1,preset2,preset3,preset4,preset5,preset6][6] # Pick which preset to use [#].


### Iterate over all files in a directory for the purpose of renaming each file that matches the edit conditions.
###     (some_dir) The full path to a directory. Str("path\to\file")
###     (edit_details) All the dtials on how to proceed with the file name edits. 
###                    List[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, SUB_DIRS]
###     (include_sub_dirs) Search sub-directories for more files.  bool(True) or bool(False)
###     --> Returns a [Integer] Number of files renamed.
def renameAllFilesInDirectory(some_dir, edit_details, include_sub_dirs = False):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir) # Error if not directory or doen't exist
    
    files_renamed = 0
    files_renamed_data = (0,0)
    
    for root, dirs, files in os.walk(some_dir):
        
        print('\n-Root: %s\n' % (root))
        
        #for dir in dirs:
            #print('--Directory: [ %s ]' % (dir))
            
        for file in files:
            #print('--File: [ %s ]' % (file))
            file_path = Path(PurePath().joinpath(root,file))
            is_file_renamed = False
            
            if edit_details[EDIT_TYPE] == ADD:
                is_file_renamed = addTextToFileName(file_path, edit_details[ADD_TEXT], edit_details[PLACEMENT])
            
            elif edit_details[EDIT_TYPE] == REPLACE:
                files_renamed_data = replaceTextInFileName(file_path, edit_details, files_renamed_data)
            
            elif edit_details[EDIT_TYPE] == RENAME:
                files_renamed_data = replaceEntireFileName(file_path, edit_details, files_renamed_data)
                #print(files_renamed_data)
            
            if is_file_renamed:
                files_renamed += 1
        
        if edit_details[EDIT_TYPE] == RENAME or edit_details[EDIT_TYPE] == REPLACE:
            files_renamed = files_renamed_data[FILES_RENAMED]
            files_renamed_data = (files_renamed_data[FILES_RENAMED], 0) # Only reset count
        
        if not include_sub_dirs:
            break
    
    return files_renamed


### Adds specific text to a filename.
###     (some_file) The full path to a file.
###     (text) The text to add to the filename.
###     (placement) Where the text will be placed, "START", "END", "BOTH".
###     --> Returns a [Boolean] True or False
def addTextToFileName(some_file, text, placement = END):
    file_path = Path(some_file)
    assert Path.is_file(file_path) # Error if not a file or doen't exist
    
    renamed = True
    if placement == START:
        new_file_name = f"{text}{file_path.stem}{file_path.suffix}"
    elif placement == END:
        new_file_name = f"{file_path.stem}{text}{file_path.suffix}"
    elif placement == BOTH:
        new_file_name = f"{text}{file_path.stem}{text}{file_path.suffix}"
    else:
        renamed = False
        #raise ValueError('"%s" Is not a proper placement of text.' % placement)
    
    if renamed:
        new_file_path = file_path.rename(Path(file_path.parent, new_file_name))
        print('--File Renamed From: %s\\ [ %s ] to [ %s ]' % (new_file_path.parent, file_path.name, new_file_path.name))
    
    return renamed


### Find and Replace text in a filename.
###     (some_file) The full path to file.
###     (edit_details) All the dtials on how to proceed with the file name edits. 
###                    List[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, SUB_DIRS]
###     (files_renamed_data) Number of files renamed so far and the current count (added to file name if COUNT used)
###                          that should be looped back into function, and increased if file is renamed.
###     --> Returns a [Tuple] files_renamed_data
def replaceTextInFileName(some_file, edit_details, files_renamed_data = (0,0)):
    file_path = Path(some_file)
    assert Path.is_file(file_path) # Error if not a file or doen't exist
    match = edit_details[MATCH_TEXT]
    replace = edit_details[REPLACE_TEXT]
    recursive = edit_details[RECURSIVE]
    search_from = edit_details[SEARCH_FROM]
    renamed_number = files_renamed_data[FILES_RENAMED]
    renamed_count = files_renamed_data[FILE_NAME_COUNT]
    
    match_replace_data = prepareMatchAndReplaceData(match, replace, file_path.name, renamed_count)
    match_text = match_replace_data[0]
    replace_text = match_replace_data[1]
    searchable_file_name = match_replace_data[2]
    renamed_count = match_replace_data[3]
    #print(match_replace_data)
    
    file_data = findReplace(file_path.name, match_text, replace_text, recursive, search_from, searchable_file_name)
    
    if file_data[EDITS_MADE] > 0:
        new_file_path = Path(file_path.parent, file_data[FILE_NAME])
        
        # Renaming File Now
        files_renamed_data = renameFile(file_path, new_file_path, edit_details, (renamed_number, renamed_count))
        renamed_number = files_renamed_data[FILES_RENAMED]
        renamed_count = files_renamed_data[FILE_NAME_COUNT]
    
    else:
        print('--File Not Renamed: %s' % (file_path))
    
    return (renamed_number, renamed_count)


### Change filename entirely and possibly add a unique identifier.
###     (some_file) The full path to a file.
###     (edit_details) All the dtials on how to proceed with the file name edits. 
###                    List[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, SUB_DIRS]
###     (files_renamed_data) Number of files renamed so far and the current count (added to file name if COUNT used) 
###                          that should be looped back into function, and increased if file is renamed.
###     --> Returns a [Tuple] files_renamed_data
def replaceEntireFileName(some_file, edit_details, files_renamed_data = (0,0)):
    file_path = Path(some_file)
    assert Path.is_file(file_path) # Error if not a file or doen't exist
    match = edit_details[MATCH_TEXT]
    replace = edit_details[REPLACE_TEXT]
    file_renamed = False
    renamed_number = files_renamed_data[FILES_RENAMED]
    renamed_count = files_renamed_data[FILE_NAME_COUNT]
    does_file_exist = TRY_AGAIN
    
    match_replace_data = prepareMatchAndReplaceData(match, replace, file_path.name, renamed_count)
    match_text = match_replace_data[0]
    new_file_name = match_replace_data[1]
    searchable_file_name = match_replace_data[2]
    renamed_count = match_replace_data[3]
    #print(match_replace_data)
    
    if match_text == '' or searchable_file_name.find(match_text) > -1:
        new_file_path = Path(file_path.parent, new_file_name+file_path.suffix)
        file_renamed = True
    '''else:
        ## TODO: Handle a single file name change? nah
        if match_text == '' or searchable_file_name.find(match_text) > -1:
            new_file_path = Path(file_path.parent, replace)'''
    
    # Renaming File Now
    if file_renamed:
        files_renamed_data = renameFile(file_path, new_file_path, edit_details, (renamed_number, renamed_count))
        renamed_number = files_renamed_data[FILES_RENAMED]
        renamed_count = files_renamed_data[FILE_NAME_COUNT]
    else:
        print('--File Not Renamed: %s' % (file_path))
    
    return (renamed_number, renamed_count)


### Prepare match and replace data using any special modify/search options.
###     (match_data) Unmodified match data
###     (replace_data) Unmodified replace data
###     (file_name) Unmodified file name
###     (renamed_count) Iterate count here
###     --> Returns a [Tuple] (match_text, replace_text, searchable_file_name, renamed_count)
def prepareMatchAndReplaceData(match_data, replace_data, file_name, renamed_count = 0):
    
    if type(match_data) == tuple and len(match_data) == 2:
        match_text = match_data[1]
        if match_data[0] == NO_MATCH_CASE:
            match_text = match_text.casefold()
            searchable_file_name = file_name.casefold()
        
        #elif match_data[0] == REGEX: ## TODO
        
        else: # Defualt MATCH_CASE
            searchable_file_name = file_name
    
    elif type(match_data) == tuple:
        match_text = match_data[0]
        searchable_file_name = file_name
    else:
        match_text = match_data
        searchable_file_name = file_name
    
    if type(replace_data) == tuple and len(replace_data) >= 3:
        if replace_data[0] == COUNT:
            
            # Get Starting Count
            if replace_data[2] > renamed_count:
                renamed_count = replace_data[2]
            
            replace_text = replace_data[1] + str(renamed_count) + replace_data[3] if len(replace_data) > 3 else ''
    
    elif type(replace_data) == tuple:
         replace_text = replace_data[0]
    else:
         replace_text = replace_data
    
    return (match_text, replace_text, searchable_file_name, renamed_count)


### TODO: Test This Out
###     (file_path) The full path to file.
###     (new_file_path) The full path to file.
###     (edit_details) All the dtials on how to proceed with the file name edits. 
###                    List[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, SUB_DIRS]
###     (files_renamed_data) Number of files renamed so far and the current count (added to file name if COUNT used)
###                          that should be looped back into function, and increased if file is renamed.
###     --> Returns a [Tuple] files_renamed_data
def renameFile(file_path, new_file_path, edit_details, files_renamed_data):
    renamed_number = files_renamed_data[FILES_RENAMED]
    renamed_count = files_renamed_data[FILE_NAME_COUNT]
    
    does_file_exist = checkIfFileExist(new_file_path, file_path)
    
    if does_file_exist == CANCEL: # Will throw error, but will stop any further renaming.
        print('Canceling any further renaming and closing...')
        new_file_path = file_path.rename(new_file_path) # Error
    
    elif does_file_exist == NO: # Actually renaming file
        new_file_path = file_path.rename(new_file_path)
        file_renamed = True
        renamed_number += 1
    
    elif does_file_exist == CONTINUE: # Skip this count (+1) and try again (recursively)
        file_renamed = False
        
        if edit_details[EDIT_TYPE] == ADD:
            print('TODO ADD')
        elif edit_details[EDIT_TYPE] == REPLACE:
            files_renamed_data = replaceTextInFileName(file_path, edit_details, (renamed_number, renamed_count + 1))
        elif edit_details[EDIT_TYPE] == RENAME:
            files_renamed_data = replaceEntireFileName(file_path, edit_details, (renamed_number, renamed_count + 1))
        
        renamed_number = files_renamed_data[FILES_RENAMED]
        renamed_count = files_renamed_data[FILE_NAME_COUNT]
        
        does_file_exist = NO
        
    elif does_file_exist == SAME_NAME: # Basically skip, but don't add to renamed files. Count will still increase.
        file_renamed = True
    
    if file_renamed:
        if does_file_exist == CONTINUE:
            print('--File Name Already Exists: %s\\ [ %s ]' % (new_file_path.parent, new_file_path.name))
        if does_file_exist == SAME_NAME:
            print('--File Already Renamed: %s\\ [ %s ]' % (new_file_path.parent, new_file_path.name))
            print('--You may have ran this script twice in a row.')
        else:
            print('--File Renamed From: %s\\ [ %s ] to [ %s ]' % (new_file_path.parent, file_path.name, new_file_path.name))
        renamed_count += 1
    
    elif does_file_exist != NO:
        print('--File Not Renamed: %s' % (file_path))
    
    return (renamed_number, renamed_count)


### Check if a file alredy exists and if it does, ask user how to proceed.
###     (file_path) The full path to a file.
###     (org_file_path) The full path the file before it's rename to check if it's the same name.
###     --> Returns a [Integer] Constant
def checkIfFileExist(file_path, org_file_path = None):
    does_file_exist = TRY_AGAIN
    
    if file_path == org_file_path:
        does_file_exist = SAME_NAME
    
    while does_file_exist == TRY_AGAIN:
        if Path.exists(file_path):
            
            if sys.platform == "win32":
                print('--File Name Already Exists: %s' % (file_path))
                file_already_exist_text = ('File Already Exists: "%s" \n\nSkip this file and continue?' % (file_path))
                file_already_exist_user_input = windll.user32.MessageBoxW(0, file_already_exist_text, "File Renaming Failed!", 0x00001016)
            else:
                print('--File Name Already Exists: %s' % (file_path))
                file_already_exist_user_input = input('Skip this file and continue? [ (C)ancel / (T)ry Again / (S)kip ]')
            
            does_file_exist = strToIntConstant(file_already_exist_user_input, 'file_saving')
        else:
            does_file_exist = NO
    
    return does_file_exist


### "Find and Replace" text within a file name.
###     (file_name) The file name or String to search through.
###     (match_text) The text to find in the String.
###     (replace_text) The text to replace the matched text with.
###     (recursive) Search for all (all = 999) or a specific number of matched text.
###     (search_from) Begain searching from LEFT to right or from RIGHT to left of String.
###     (output_prints) Turn print outputs on or off.
###     (edit_count) *Do not use*
###     --> Returns a [Tuple] (String, Integer)
def findReplace(file_name, match_text, replace_text, recursive = ALL, search_from = LEFT, searchable_file_name = '', output_prints = False, edit_count=0):
    
    searchable_file_name = file_name if searchable_file_name == '' else searchable_file_name
    
    if searchable_file_name.find(match_text) == -1:
        new_file_name = file_name
    else:
        index_matches = []
        index_match = 0
        start = 0
        end = -1
        while index_match > -1:
            index_match = searchable_file_name.rfind(match_text, start, end) # Reverse Find
            end = index_match
            index_matches.append(index_match)
        index_matches.pop(-1)
        
        ingnore = len(index_matches) - recursive 
        ingnore = 0 if ingnore < 0 else ingnore
        while ingnore > 0:
            if search_from == LEFT:
                index_matches.pop(0)
            elif search_from == RIGHT:
                index_matches.pop(-1)
            ingnore -= 1
        
        match_size = len(match_text)
        new_file_name = file_name
        for index in index_matches:
            new_file_name = new_file_name[:index] + replace_text + new_file_name[index + match_size:]
            edit_count += 1
            
        if output_prints: print('Edits Made: [ %s ]' % (edit_count))
    
    return (new_file_name, edit_count)


### "Find and Replace" text within a String.
###     (string) The String to search through.
###     (match) The text to find in the String.
###     (replace) The text to replace the matched text with.
###     (recursive) Search for all (all = 999) or a specific number of matched text.
###     (search_from) Begain searching from LEFT to right or from RIGHT to left of String.
###     (output_prints) Turn print outputs on or off.
###     (edit_count) *Do not use*
###     --> Returns a [Tuple] (String, Integer)
def findReplaceOld(string, match, replace, recursive = ALL, search_from = LEFT, output_prints = True, edit_count=0):
    if string.find(match) == -1:
        new_string = string
    else:
        
        if search_from == LEFT:
            string_split = string.partition(match)
            string_split_replaced = (string_split[0], replace)
        elif search_from == RIGHT:
            string_split = string.rpartition(match)
            string_split_replaced = (replace, string_split[2])
        
        new_string = ''.join(string_split_replaced)
        edit_count += 1
        
        if recursive != 1:
        
            if search_from == LEFT:
                if recursive > edit_count:
                    
                    new_string_tuple = findReplace(string_split[2], match, replace, recursive, search_from, output_prints, edit_count)
                    
                    if new_string_tuple[EDITS_MADE] > edit_count: # Was new edit made?
                        new_string += new_string_tuple[FILE_NAME]
                        edit_count = new_string_tuple[EDITS_MADE]
                        if output_prints: print('Edits Made: [ %s ]' % (edit_count))
                    else:
                        new_string += string_split[2]
                else:
                    new_string += string_split[2]
            
            elif search_from == RIGHT:
                if recursive > edit_count:
                
                    new_string_tuple = findReplace(string_split[0], match, replace, recursive, search_from, output_prints, edit_count)
                
                    if new_string_tuple[EDITS_MADE] > edit_count: # Was new edit made?
                        new_string = new_string_tuple[FILE_NAME] + new_string
                        edit_count = new_string_tuple[EDITS_MADE]
                        if output_prints: print('Edits Made: [ %s ]' % (edit_count))
                    else:
                        new_string = string_split[0] + new_string
                else:
                    new_string = string_split[0] + new_string
        
        else:
            if search_from == LEFT:
                new_string += string_split[2]
            elif search_from == RIGHT:
                new_string = string_split[0] + new_string
    
    return (new_string, edit_count)
    

### Change specific user inputs (answer to a question) into a "True or False" Boolean.
###     (user_input) The String with variations of "yes or no" text in them.
###     --> Returns a [Boolean] True or False
def yesTrue(user_input):
    user_input = user_input.casefold()
    if user_input == 'y' or user_input == 'yes' or user_input == 'yea' or user_input == 'ye':
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
    if category == 'edit_type':
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
            number = RIGHT
    elif category == 'file_saving':
        if user_input == '2' or user_input == 'c' or user_input == 'cancel':
            number = CANCEL
        if user_input == '10' or user_input == 't' or user_input == 'try' or user_input == 'try again':
            number = TRY_AGAIN
        elif user_input == '11' or user_input == 's' or user_input == 'skip':
            number = SKIP
    return number


### Change a String into an Integer.
###     (string) The String to change into an Integer.
###     --> Returns a [Integer]
def strNumberToInt(string_num):
    string_num = string_num.casefold()
    if string_num == 'a' or string_num == 'all':
        number = ALL
    elif string_num.isnumeric():
        number = int(string_num)
    else:
        number = NONE
    return number


### Drop one of more files and directories here to be renamed after answering a series of questions regarding how to properly rename said files.
###     (files) A [List] of files, which can include directories pointing to many more files.
###     --> Returns a [Integer] Number of files renamed.
def drop(files):
    
    # If script is ran on it's own then ask for a file to rename.
    if len(files) == 0:
        dropped_file = input('No files or directories found, drop one here now to proceed: ')
        dropped_file = dropped_file.replace('"','') # Remove the auto quotes.
        
        if os.path.exists(dropped_file):
            files.append(dropped_file)
        else:
            print('\nNo Files or Directories Dropped')
            return 0
    elif not os.path.exists(files[0]):
        print('\nNo Files or Directories Dropped')
        return 0
    
    files_renamed = 0
    files_renamed_data = (0,0)
    
    try:
        # Check if at least one file or directory was dropped
        dropped_file = files[0]
        print('Number of Files or Directories Dropped: [ %s ]' % len(files))
        
        if use_preset:
            edit_details = preset_options
            
        else:
            edit_details = [EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM]
            
            edit_type = NONE
            while edit_type == NONE:
                edit_type = input('Do you wish to add text or replace text in filename(s)? [ (A)DD / (R)EPLACE ]: ')
                edit_type = strToIntConstant(edit_type, 'edit_type')
            
            edit_details[EDIT_TYPE] = edit_type
            
            if edit_type == ADD:
                add_text = input('Text To Add: ')
                
                placement = NONE
                while placement == NONE:
                    placement = input('Where To Place Text [ (S)TART / (E)ND / (B)OTH ]: ')
                    placement = strToIntConstant(placement, 'placement')
                
                edit_details[ADD_TEXT] = add_text
                edit_details[PLACEMENT] = placement
            
            elif edit_type == REPLACE:
                match_text = input('Search File Name(s) For: ')
                replace_text = input('And Replace With: ')
                
                recursive = NONE
                while recursive == NONE:
                    recursive = input('How many matches per file name are to be replaced? [ (A)LL / 1 / # ]: ') # All = 999
                    recursive = strNumberToInt(recursive)
                
                if recursive != ALL:
                    search_from = NONE
                    while search_from == NONE:
                        search_from = input('Begin searching from "Left to Right" or from "Right to Left"? [ (L)EFT / (R)IGHT ]: ')
                        search_from = strToIntConstant(search_from, 'search_from')
                else:
                    search_from = LEFT
                
                edit_details[MATCH_TEXT] = match_text
                edit_details[REPLACE_TEXT] = replace_text
                edit_details[RECURSIVE] = recursive
                edit_details[SEARCH_FROM] = search_from
        
        # Iterate over all dropped files including all files in dropped directories
        include_sub_dirs = -1
        for file_path in files:
            
            if os.path.isdir(file_path):
                
                if include_sub_dirs == -1 and not use_preset: # Only answer once
                    include_sub_dirs = input('Search through sub-directories too? [ Y / N ]: ')
                    include_sub_dirs = yesTrue(include_sub_dirs)
                else:
                    include_sub_dirs = preset_options[SUB_DIRS]
                
                files_renamed += renameAllFilesInDirectory(file_path, edit_details, include_sub_dirs)
            
            elif os.path.isfile(file_path):
                print('\n')
                is_file_renamed = False
                
                if edit_details[EDIT_TYPE] == ADD:
                    is_file_renamed = addTextToFileName(file_path, edit_details[ADD_TEXT], edit_details[PLACEMENT])
                
                elif edit_details[EDIT_TYPE] == REPLACE:
                    files_renamed_data = replaceTextInFileName(file_path, edit_details, files_renamed_data)
                
                elif edit_details[EDIT_TYPE] == RENAME:
                    files_renamed_data = replaceEntireFileName(file_path, edit_details, files_renamed_data)
                
                if is_file_renamed:
                    files_renamed += 1
            
            else:
                print( os.path.isfile(file_path) )
                print("\nThis is not a normal file of directory (socket, FIFO, device file, etc.) and so this script won't be renameing it." )
                
        if edit_details[EDIT_TYPE] == RENAME or edit_details[EDIT_TYPE] == REPLACE:
            files_renamed += files_renamed_data[FILES_RENAMED]
        
    except IndexError:
        print('\nNo Files or Directories Dropped')
    
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
    #sys.argv.append(os.path.join(ROOT_DIR,'folder with spaces'))
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces')
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces\\file - file - file.txt')
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces\\sub2')
   
    files_renamed = drop(sys.argv[1:])
    print('\nNumber of files renamed: [ %s ]' % (files_renamed))
    
    if loop:
        newFile = 'startloop'
        prev_files_renamed = 0
        while newFile != '':
            newFile = input('\nDrop another file or directory here to go again or press enter to quit: ')
            newFile = newFile.replace('"','') # Remove the auto quotes around file paths with spaces.
            files_renamed += drop([newFile])
            if files_renamed > prev_files_renamed:
                print('\nNumber of all files renamed so far: [ %s ]' % (files_renamed))
                prev_files_renamed = files_renamed
    
