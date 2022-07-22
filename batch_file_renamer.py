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
    [] Special search and edits. Examples: 
        Find file names with a string then add another string at end of the file name.
        Find file names with a string then rename entire file name and stop/return/end.
        Find file names with a string then add another string specifically next to matched string.
        Make use of regular expressions.  This could get complex.
        Add an iterated number to the end of the file names.
        
'''

from pathlib import Path, PurePath
import os
#import re
import sys

#CUR_VERSION_STR = ".".join(map(str, sys.version_info[:3]))
MIN_VERSION = (3,8,0)
MIN_VERSION_STR = '.'.join([str(n) for n in MIN_VERSION])
START = 0
END = 1
BOTH = 2
LEFT = 0
RIGHT = 1
ADD = 0
REPLACE = 1
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
ALL = 999
NONE = -1


### After initial drop and file renaming, ask for additional files or just quit the script.
loop = True


### Present Options - Used to skip questions and immediately start renaming all drop files.
use_preset = False

preset0 = {
  EDIT_TYPE     : ADD,      # ADD or REPLACE
  ADD_TEXT      : '-F',     # 'Text' to Add
  PLACEMENT     : END,      # START, END, or BOTH
  MATCH_TEXT    : '',       # 'Text' to Find
  REPLACE_TEXT  : '',       # 'Text' to Replace with
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
preset_options = [preset0,preset1,preset2,preset3][1] # Pick which preset to use [#].


### Iterate over all files in a directory for the purpose of renaming each file that matches the edit conditions.
###     (some_dir) The full path to a directory. Str("path\to\file")
###     (edit_details) All the dtials on how to proceed with the edits. List[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM]
###     (include_sub_dirs) Search sub-directories for more files.  bool(True) or bool(False)
###     --> Returns a [Integer] Number of files renamed.
def renameAllFilesInDirectory(some_dir, edit_details, include_sub_dirs = False):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir) # Error if not directory or doen't exist
    
    files_renamed = 0
    for root, dirs, files in os.walk(some_dir):
    
        print('\n-Root: %s' % (root))
        
        #for dir in dirs:
            #print('--Directory: [ %s ]' % (dir))
            
        for file in files:
            #print('--File: [ %s ]' % (file))
            file_path = Path(PurePath().joinpath(root,file))
            is_file_renamed = False
            
            if edit_details[EDIT_TYPE] == ADD:
                is_file_renamed = addStringToFileName(file_path, edit_details[ADD_TEXT], edit_details[PLACEMENT])
            
            elif edit_details[EDIT_TYPE] == REPLACE:
                is_file_renamed = replaceStringInFileName(file_path, edit_details[MATCH_TEXT], edit_details[REPLACE_TEXT], edit_details[RECURSIVE], edit_details[SEARCH_FROM])
            
            if is_file_renamed:
                    files_renamed+=1
            
        if not include_sub_dirs:
            break
    
    return files_renamed


### Adds a string value to a filename
###     (some_file) The full path to file.
###     (string) The new string value to add to the filename.
###     (placement) Where the new string value will be placed, "START", "END", "BOTH".
###     --> Returns a [Bool] True or False
def addStringToFileName(some_file, string, placement = END):
    file_path = Path(some_file)
    assert Path.is_file(file_path) # Error if not a file or doen't exist
    
    renamed = True
    if placement == START:
        new_file_name = f"{string}{file_path.stem}{file_path.suffix}"
    elif placement == END:
        new_file_name = f"{file_path.stem}{string}{file_path.suffix}"
    elif placement == BOTH:
        new_file_name = f"{string}{file_path.stem}{string}{file_path.suffix}"
    else:
        renamed = False
        #raise ValueError('"%s" Is not a proper placement of string.' % placement)
    
    if renamed:
        new_file_path = file_path.rename(Path(file_path.parent, new_file_name))
        print('--File Renamed From: %s\\ [ %s ] to [ %s ]' % (new_file_path.parent, file_path.name, new_file_path.name))
    
    return renamed


### Find and Replace a string in a filename.
###     (some_file) The full path to file.
###     (match) The string value to find in the filename.
###     (replace) The string value to replace the matched string value with.
###     (recursive) Search for all (999 = all) or a specific number of matched values to replace.
###     (search_from) Begain searching from LEFT to right or from RIGHT to left of string.
###     --> Returns a [Bool] True or False
def replaceStringInFileName(some_file, match, replace, recursive, search_from):
    file_path = Path(some_file)
    assert Path.is_file(file_path) # Error if not a file or doen't exist
    
    new_file_name = findReplace(file_path.name, match, replace, recursive, search_from)
    
    if new_file_name[EDITS_MADE] > 0:
        new_file_path = file_path.rename(Path(file_path.parent, new_file_name[FILE_NAME]))
        renamed = True
        print('--File Renamed From: %s\\ [ %s ] to [ %s ]' % (new_file_path.parent, file_path.name, new_file_path.name))
    else:
        renamed = False
        print('--File Not Renamed: %s' % (file_path))

    return renamed


### "Find and Replace" a string with another string within a larger string.
###     (string) The main string to search through.
###     (match) The string value to find in the main string.
###     (replace) The string value to replace the matched string value with.
###     (recursive) Search for all (all = 999) or a specific number of matched values to replace.
###     (search_from) Begain searching from LEFT to right or from RIGHT to left of string.
###     (output_prints) Turn print outputs on or off.
###     (edit_count) *Do not use*
###     --> Returns a [Tuple] (String, Integer)
def findReplace(string, match, replace, recursive = ALL, search_from = LEFT, output_prints = True, edit_count=0):
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
    

### Change any "Yes or No" string into a "True or False" Bool
###     (string) The string with variations of "yes or no" in them.
###     --> Returns a [Bool] True or False
def yesTrue(string):
    string = string.lower()
    if string == 'y' or string == 'yes' or string == 'yea' or string == 'ye':
        bool = True
    else:
        bool = False
    return bool


### Change certain user inputs (or answer to question) into an integer constant.
###     (string) The user input from a question asked.
###     (category) The category of the question ask.
###     --> Returns a [Integer]
def strToIntConstant(string, category):
    string = string.lower()
    number = NONE
    if category == 'edit_type':
        if string == 'a' or string == 'add':
            number = ADD
        elif string == 'r' or string == 'replace':
            number = REPLACE
    if category == 'placement':
        if string == 's' or string == 'start':
            number = START
        elif string == 'e' or string == 'end':
            number = END
        elif string == 'b' or string == 'both':
            number = BOTH
    if category == 'search_from':
        if string == 'l' or string == 'left':
            number = LEFT
        elif string == 'r' or string == 'right':
            number = RIGHT
    return number


### Change strings into an integers.
###     (string) The string to change into an integer.
###     --> Returns a [Integer]
def strNumberToInt(string):
    string = string.lower()
    if string == 'a' or string == 'all':
        number = ALL
    elif string.isnumeric():
        number = int(string)
    else:
        number = NONE
    return number


### Drop one of more files and directories here to be renamed after answering a series of questions regarding how to properly rename said files.
###     (files) A [List] of files, which can include directories pointing to many more files.
###     --> Returns a [Integer] Number of files renamed.
def drop(files):
    
    # If script is ran on it's own then ask for a file to rename.
    if len(files) == 0:
        droppedFile = input('No files or directories found, drop one here now to proceed: ')
        droppedFile = findReplace(droppedFile,'"','',ALL,LEFT,False)[0] # Remove the auto quotes
        
        if os.path.exists(droppedFile):
            files.append(droppedFile)
        else:
            print('\nNo Files or Directories Dropped')
            return 0
    elif not os.path.exists(files[0]):
        print('\nNo Files or Directories Dropped')
        return 0
    
    files_renamed = 0
    
    try:
        # Check if at least one file or directory was dropped
        droppedFile = files[0]
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
                
                files_renamed = renameAllFilesInDirectory(file_path, edit_details, include_sub_dirs)
            
            elif os.path.isfile(file_path):
                print('\n')
                is_file_renamed = False
                print(edit_details[EDIT_TYPE])
                if edit_details[EDIT_TYPE] == ADD:
                    is_file_renamed = addStringToFileName(file_path, edit_details[ADD_TEXT], edit_details[PLACEMENT])
                
                elif edit_details[EDIT_TYPE] == REPLACE:
                    is_file_renamed = replaceStringInFileName(file_path, edit_details[MATCH_TEXT], edit_details[REPLACE_TEXT], edit_details[RECURSIVE], edit_details[SEARCH_FROM])
                    
                if is_file_renamed:
                    files_renamed+=1
            
            else:
                print( os.path.isfile(file_path) )
                print("\nThis is not a normal file of directory (socket, FIFO, device file, etc.) and so this script won't be renameing it." )
                
    except IndexError:
        print('\nNo Files or Directories Dropped')
    
    return files_renamed

### 
###     () 
###     --> Returns a [] 
'''def ():
    return 0'''
    
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
   
    files_renamed = drop(sys.argv[1:])
    print('\nNumber of files renamed: [ %s ]' % (files_renamed))
    
    if loop:
        newFile = 'startloop'
        prev_files_renamed = 0
        while newFile != '':
            newFile = input('\nDrop another file or directory here to go again or press enter to quit: ')
            #newFile = newFile.replace('"','')
            newFile = findReplace(newFile,'"','',ALL,LEFT,False)[0] # Remove the auto quotes around file paths with spaces.
            files_renamed += drop([newFile])
            if files_renamed > prev_files_renamed:
                print('\nNumber of all files renamed so far: [ %s ]' % (files_renamed))
                prev_files_renamed = files_renamed
    
