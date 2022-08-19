#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Batch File Renamer by JDHatten
    This script will rename one or more files either by adding new text or replacing text in the file names.
    Adding text can be placed at the start, end, or both sides of either matched text or the entire file name itself.
    Replacing text will replace the first or all instances of matched text in a file name including the extension.
    Renameing will just rename the entire file, but an iterating number or some other modify option must be used.
    Bonus: This script can also update any text based files that that have links to the renamed files to prevent
    broken links in whatever apps that use the renamed files.

Usage:
    Simply drag and drop one or more files or directories onto the script.  Use custom presets for more complex 
    renaming methods.  Script can be opened directly but only one file or directory may be dropped/added/typed-in at once.

TODO:
    [] Rename directories too
    [] Create a log of files renamed, time of completion, etc.
    [DONE] Loop script after finishing and ask to drop another file before just closing.
    [DONE] When replacing only one or more but not all matched strings start searching from the right/end of string.
    [DONE] Preset options
    [DONE] Display preset options and allow user to chose from cmd promt
    [DONE] Better handling of overwriting files
    [DONE] Sort files in a particular way before renameing
    [DONE] Update one or more texted based files after a file has been renamed
    [] Use more than one search/modify option at a time.
    [] Special search and edits. Examples: 
        [X] Find file names with a string then add another string at end of the file name.
        [X] Find file names with a string then rename entire file name and stop/return/end.
        [X] Find file names with a string then add another string specifically next to matched string.
        [X] Add an iterated number to file names.
        [X] Find specific file names extentions and only change (or add to) the extention
        [] Generate random numbers or text that is added to file names.
        [X] A List of Strings to search for or add to file names.
        [] Make use of regular expressions.  This could get complex.
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

# EDIT_TYPE
ADD = 0
REPLACE = 1
RENAME = 2

# PLACEMENT
START = 3
LEFT = 3
END = 4
RIGHT = 4
BOTH = 5
BOTH_ENDS = 5
OF_FILE_NAME = 6
OF_MATCH = 7
EXTENTION = 8

# EDIT_DETAILS
EDIT_TYPE = 0
ADD_TEXT = 1
PLACEMENT = 2
MATCH_TEXT = 3
REPLACE_TEXT = 4
RECURSIVE = 5
SEARCH_FROM = 6 ## TODO: move to MATCH_TEXT OPTIONS
LINKED_FILES = 7
SUB_DIRS = 8
PRESORT_FILES = 9
SEARCHABLE_TEXT = 8
SEARCH_OPTION = 9
MODIFY_OPTION = 10
RENAMED_COUNT = 11
RENAMED_COUNT_MAX = 12

FILE_PATH = 0
FILE_NAME = 1
FILE_SIZE = 2

FILES_RENAMED = 0
FILE_NAME_COUNT = 1
FILE_NAME_COUNT_MAX = 2
SKIPPED_FILES = 3

ALL = 999
NONE = -1
NO = -1
CANCEL = 0
OK = 1
YES = 1
TRY_AGAIN = 2
SKIP = 3
CONTINUE = 3
SAME_NAME = 4
SAME = 4
NO_CHANGE = 4

TEXT = 0
OPTIONS = 1

STARTING_TEXT = 0
DYNAMIC_TEXT = 1
ENDING_TEXT = 2

STARTING_COUNT = 0
ENDING_COUNT = 1

### Modify/Search/Sort Options
MATCH_CASE = 0       # Defualt
NO_MATCH_CASE = 1    # Not case sensitive search
COUNT = 2            # Iterate a number that is added to a file name. (Starting Number, Ending Number) Ending number is optional. (NOTE: Resets after each directory change.)
COUNT_TO = 3         # Max amount of renames to make before stopping.  Similer to COUNT without adding an iterating number to file name.
RANDOM = 4           ## TODO: Generate random numbers or text that is added to file names.
TEXT_LIST = 5        ## TODO: A List of Strings to search for or add to file names.
REGEX = 6            ## TODO:
SAME_MATCH_INDEX = 7 # When a match is made from the "MATCH_TEXT List" use the same index when choosing text from the "REPLACE_TEXT List".
REPEAT_TEXT_LIST = 8 ## TODO: Once the end of a text list is reached, repeat it.  Text must be dynamic, i.e. COUNT, RANDOM, etc.

ASCENDING = 10
DESCENDING = 11
ALPHABETICALLY = 12
FILE_SIZE = 13
DATE_ACCESSED = 14
DATE_MODIFIED = 15
DATE_CREATED = 16       # Windows
DATE_META_MODIFIED = 16 # UNIX

#EXTENTION = 6   ## TODO: Moved to PLACEMENT, might revisit if "multiple options" coded in


### After initial drop and file renaming, ask for additional files or just quit the script.
loop = True

### Present Options - Used to skip questions and immediately start renaming all dropped files.
### Much more complex renaming possibilities are avaliable when using presets.
### Make sure to select the correct preset (select_preset)
use_preset = True
select_preset = 15

preset0 = {     # Defualts
  EDIT_TYPE     : ADD,      # ADD or REPLACE or RENAME (entire file name, minus extention)
  ADD_TEXT      : '',       # 'Text' to Add -OR- Dict{ TEXT : 'Text', OPTIONS : Modify Options }
  PLACEMENT     : END,      # START or END or BOTH (ends) or EXTENTION (add after or replace extention) -OR- Dict{ PLACE : OF_ }
  MATCH_TEXT    : '',       # 'Text' to Find  -OR- Dict{ TEXT : 'Text', OPTIONS : Modify Options }
  REPLACE_TEXT  : '',       # 'Text' to Replace with -OR- Dict{ TEXT : 'Text', OPTIONS : Modify Options }
  RECURSIVE     : ALL,      # 1-999/ALL (how many match and replace edits to make per file name)
  SEARCH_FROM   : LEFT,     # Start searching from LEFT or RIGHT (important if using a recursive limit, i.e. not ALL)
  LINKED_FILES  : [],       # File Paths of files that need to be updated of any file name changes to prevent broken links in apps. (Use double slashes "//")
  SUB_DIRS      : False,    # Search Sub-Directories (True or False)
  PRESORT_FILES : None      # Sort before renaming files.  Dict{ Sort Option : ASCENDING or DESCENDING }
}                           # Note: Dynamic Text Format = Tuple('Starting Text', Integer/Tuple/List, 'Ending Text') -OR- just a List['Text',...]
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
  ADD_TEXT      : ' (U)',
  PLACEMENT     : END,
  SUB_DIRS      : True
}
preset4 = {
  EDIT_TYPE     : RENAME,
  MATCH_TEXT    : { TEXT : '', OPTIONS : NO_MATCH_CASE },
  REPLACE_TEXT  : { TEXT : ('TextTextText-[', (1,7), ']'), OPTIONS : COUNT },
  SUB_DIRS      : True
}
preset5 = {
  EDIT_TYPE     : ADD,
  MATCH_TEXT    : { TEXT : 'Text', OPTIONS : MATCH_CASE },
  ADD_TEXT      : { TEXT : ('--(', 1, ')'), OPTIONS : COUNT },
  PLACEMENT     : END,
  SUB_DIRS      : True
}
preset6 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : { TEXT : 'Tex', OPTIONS : MATCH_CASE },
  REPLACE_TEXT  : { TEXT : ('(', 0, ')'), OPTIONS : COUNT },
  RECURSIVE     : 4,
  SEARCH_FROM   : RIGHT,
  SUB_DIRS      : False
}
preset7 = {
  EDIT_TYPE     : REPLACE,
  PLACEMENT     : EXTENTION,
  MATCH_TEXT    : { TEXT : 'txt', OPTIONS : NO_MATCH_CASE },
  REPLACE_TEXT  : { TEXT : 'doc' },
}
preset8 = {
  EDIT_TYPE     : ADD,
  PLACEMENT     : EXTENTION,
  MATCH_TEXT    : 'txt',
  ADD_TEXT      : 'bck',
}
preset9 = {
  EDIT_TYPE     : ADD,
  PLACEMENT     : { BOTH_ENDS : OF_MATCH },
  MATCH_TEXT    : { TEXT : 'text', OPTIONS : NO_MATCH_CASE },
  ADD_TEXT      : 'XXX',
  RECURSIVE     : 2,
  SEARCH_FROM   : RIGHT,
}
preset10 = {
  EDIT_TYPE     : ADD,
  PLACEMENT     : { END : OF_MATCH },
  MATCH_TEXT    : { TEXT : 'text', OPTIONS : NO_MATCH_CASE },
  ADD_TEXT      : { TEXT : ('-XXX', 3), OPTIONS : COUNT_TO },
  RECURSIVE     : 1,
  SEARCH_FROM   : RIGHT,
}
preset11 = {
  EDIT_TYPE     : RENAME,
  MATCH_TEXT    : { TEXT : '', OPTIONS : NO_MATCH_CASE },
  REPLACE_TEXT  : { TEXT : ('TextTextText-[', (1,7), ']'), OPTIONS : COUNT },
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
  PRESORT_FILES : { DATE_MODIFIED : DESCENDING }
}
preset12 = {
  EDIT_TYPE     : ADD,
  ADD_TEXT      : ' (U)',
  PLACEMENT     : END,
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
  SUB_DIRS      : True
}
preset13 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : ' (U)',
  REPLACE_TEXT  : '',
  RECURSIVE     : 1,
  SEARCH_FROM   : RIGHT,
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
  SUB_DIRS      : True
}
preset14 = {
  EDIT_TYPE     : RENAME,
  MATCH_TEXT    : { TEXT : ['[1]','[2]','[3]','[4]','[5]'], OPTIONS : NO_MATCH_CASE },
  REPLACE_TEXT  : { TEXT : ['NewName-01','ThisName-02','AName-03','NotAName-04','NameName-05'], OPTIONS : SAME_MATCH_INDEX },
  RECURSIVE     : ALL,
  SEARCH_FROM   : LEFT,
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
}
preset15 = {
  EDIT_TYPE     : RENAME,
  MATCH_TEXT    : { TEXT : ['text','name'], OPTIONS : NO_MATCH_CASE },
  REPLACE_TEXT  : { TEXT : [('NewName-', 1, ''),('DiffName-', 1, '')], OPTIONS : REPEAT_TEXT_LIST }, ## TODO
  RECURSIVE     : ALL,
  SEARCH_FROM   : LEFT,
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
}
preset_options = [preset0,preset1,preset2,preset3,preset4,preset5,preset6,preset7,preset8,preset9,preset10,preset11,preset12,preset13,preset14,preset15]
preset = preset_options[select_preset]


### Display one or all file rename preset options.
###     (preset) A Dictonary with a file rename preset.
###     (number) Preset selection.
###     --> Returns a [0] 
def displayPreset(presets, number = -1):
    if number == -1:
        for ps in presets:
            number += 1
            print('\nPreset %s' % str(number))
            for option, mod in ps.items():
                opt_str = intToStrText(option, 'Preset Options')
                mod_str = ''
                if type(mod) == dict:
                    for key, value in mod.items():
                        mod_str += intToStrText(key, value, option) + '  '
                else:
                    mod_str = intToStrText(None, mod, option)
                print('    %s : %s' % (opt_str, mod_str))
    else:
        print('\nPreset %s' % str(number))
        for option, mod in presets[number].items():
            opt_str = intToStrText(option, 'Preset Options')
            mod_str = ''
            if type(mod) == dict:
                for key, value in mod.items():
                    mod_str += intToStrText(key, value, option) + '  '
            else:
                mod_str = intToStrText(None, mod, option)
            print('    %s : %s' % (opt_str, mod_str))
    return 0


### Iterate over all files in a directory for the purpose of renaming each file that matches the edit conditions.
###     (some_dir) The full path to a directory. Str("path\to\file")
###     (edit_details) All the details on how to proceed with the file name edits. 
###                    Dictionary[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, SUB_DIRS]
###     (include_sub_dirs) Search sub-directories for more files.  Booleon(True) or Boolean(False)
###     --> Returns a [Integer] Number of files renamed.
def renameAllFilesInDirectory(some_dir, edit_details, include_sub_dirs = False):
    assert Path.is_dir(some_dir) # Error if not directory or doen't exist
    
    files_renamed = 0
    files_renamed_data = (0,0,-1, [])
    
    for root, dirs, files in os.walk(some_dir):
        
        print('\n-Root: %s\n' % (root))
        
        #for dir in dirs:
            #print('--Directory: [ %s ]' % (dir))
        
        # Sort Files
        files_meta = sortFiles(files, edit_details.get(PRESORT_FILES,None), root)
        
        for file in files_meta:
            #print('--File: [ %s ]' % (file[FILE_NAME]))
            file_path = Path(file[FILE_PATH])
            
            files_renamed_data = startingFileRenameProcedure(file_path, edit_details, files_renamed_data)
            #print(files_renamed_data)
            
            if files_renamed_data[FILE_NAME_COUNT_MAX] != -1 and files_renamed_data[FILE_NAME_COUNT] > files_renamed_data[FILE_NAME_COUNT_MAX]:
                break # Max file count hit, stop and move on to next directory.
        
        files_renamed = files_renamed_data[FILES_RENAMED]
        files_renamed_data = (files_renamed_data[FILES_RENAMED], 0, -1, []) # Reset all but files renamed
        
        if not include_sub_dirs:
            break
    
    return files_renamed


### Sort file in various ways before renaming.
###     (files) A List of file names.
###     (sort_option) A Dictionary with a file sorting option.
###     (root) Root path of files if (files) is just names
###     --> Returns a [List] 
def sortFiles(files, sort_option, root = ''):
    files_meta = []
    for file in files:
        if root == '':
            file_path = Path(file)
        else:
            file_path = Path(PurePath().joinpath(root, file))
        file_meta = os.stat(file_path)
        files_meta.append((file_path, file_path.name, file_meta.st_size, file_meta.st_atime, file_meta.st_mtime, file_meta.st_ctime))
    
    if type(sort_option) == dict:
        descending = False if list(sort_option.values())[0] == ASCENDING else True
        if ALPHABETICALLY in sort_option:
            files_meta.sort(reverse=descending, key=sortFilesAlphabetically)
        elif FILE_SIZE in sort_option:
            files_meta.sort(reverse=descending, key=sortFilesByFileSize)
        elif DATE_ACCESSED in sort_option:
            files_meta.sort(reverse=descending, key=sortFilesByAccessDate)
        elif DATE_MODIFIED in sort_option:
            files_meta.sort(reverse=descending, key=sortFilesByModifyDate)
        elif DATE_CREATED in sort_option: # or DATE_META_MODIFIED in sort_option:
            files_meta.sort(reverse=descending, key=sortFilesByCreationDate)
    
    return files_meta


### Sort file functions.
###     (file) A Tuple with the [0]full file path, [1]file name,      [2]file size, 
###                             [3]access date,    [4]modify date, or [5]creation date (UNIX: meta data modified data).
###     --> Returns a [String] or [Integer]
def sortFilesAlphabetically(file):
    return file[1]
def sortFilesByFileSize(file):
    return file[2]
def sortFilesByAccessDate(file):
    return file[3]
def sortFilesByModifyDate(file):
    return file[4]
def sortFilesByCreationDate(file):
    return file[5]


### Adds specific text to a filename.
###     (some_file) The full path to a file.
###     (edit_details) All the details on how to proceed with the file name edits. 
###                    Dictionary[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, LINKED_FILES,...]
###     (files_renamed_data) Number of files renamed so far and the current count (added to file name if COUNT used)
###                          that should be looped back into function, and increased if file is renamed.
###     --> Returns a [Tuple] files_renamed_data
def startingFileRenameProcedure(some_file, edit_details, files_renamed_data = (0,0,-1,[])):
    file_path = Path(some_file)
    assert Path.is_file(file_path) # Error if not a file or doen't exist
    file_renamed = False
    skip_file = False
    
    # Keep Track Of...
    renamed_number = files_renamed_data[FILES_RENAMED]
    renamed_count = files_renamed_data[FILE_NAME_COUNT]
    renamed_count_max = files_renamed_data[FILE_NAME_COUNT_MAX]
    files_to_skip = files_renamed_data[SKIPPED_FILES]
    
    # Prepare all the Edit Data
    prepared_edit_data = prepareAllEditData(edit_details, file_path.name, renamed_count, renamed_count_max)
    edit_type = prepared_edit_data[EDIT_TYPE]
    match_text = prepared_edit_data[MATCH_TEXT]
    add_text = prepared_edit_data[ADD_TEXT]
    placement = prepared_edit_data[PLACEMENT]
    replace_text = prepared_edit_data[REPLACE_TEXT]
    recursive = prepared_edit_data[RECURSIVE]
    search_from = prepared_edit_data[SEARCH_FROM]
    linked_files = prepared_edit_data[LINKED_FILES]
    searchable_file_name = prepared_edit_data[SEARCHABLE_TEXT]
    search_option = prepared_edit_data[SEARCH_OPTION]
    modify_option = prepared_edit_data[MODIFY_OPTION]
    renamed_count = prepared_edit_data[RENAMED_COUNT]
    renamed_count_max = prepared_edit_data[RENAMED_COUNT_MAX]
    #print(prepared_edit_data)
    if edit_type == ADD:
        insert_text = add_text
    elif edit_type == REPLACE or edit_type == RENAME:
        insert_text = replace_text
    
    # Skip any files that already had a name matching previous rename attempts (and not overwritten).
    # Note: This keeps the starting and ending COUNT exactly as typed with no skipping numbers.
    # (3,9) will always be (3,9) and not (5,9) due to files with that same name/count already existing.
    for file in files_to_skip:
        if file == file_path:
            skip_file = True
            break
    
    # Create The New File Name
    if not skip_file:
        new_file_name = insertTextIntoFileName(file_path, edit_type, match_text, insert_text, placement, modify_option, recursive, search_from, searchable_file_name, renamed_number, renamed_count)
        file_renamed = False if new_file_name == file_path.name else True
    
    # Rename The File Now
    if file_renamed:
        new_file_path = Path(file_path.parent, new_file_name)
        files_renamed_data = renameFile(file_path, new_file_path, edit_details, (renamed_number, renamed_count, renamed_count_max, files_to_skip))
        renamed_number = files_renamed_data[FILES_RENAMED]
        renamed_count = files_renamed_data[FILE_NAME_COUNT]
        
        for file in linked_files:
            links_updated = updateLinksInFile(file, str(file_path), str(new_file_path))
            if links_updated:
                print('----Link File Updated: [ %s ]' % (file))
            #else:
                #print('----Link File Not Updated: [ %s ]' % (file))
    
    else:
        print('--File Not Renamed: %s' % (file_path))
    
    return (renamed_number, renamed_count, renamed_count_max, files_to_skip)


### Prepare edit_details data adding in any custom search and modify options.
### Options: MATCH_CASE, NO_MATCH_CASE, COUNT, RANDOM, TEXT_LIST, REGEX, EXTENTION
###     (edit_details) Unmodified details on how to proceed with the file name edits. 
###                    Dictionary[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, SUB_DIRS]
###     (file_name) Unmodified file name
###     (renamed_count) Iterate count here if needed
###     --> Returns a [Tuple] (EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, SEARCHABLE_TEXT, SEARCH_OPTION, MODIFY_OPTION, RENAMED_COUNT)
def prepareAllEditData(edit_details, file_name, renamed_count = 0, renamed_count_max = -1):
    
    edit_type = edit_details.get(EDIT_TYPE,ADD)
    match_data = edit_details.get(MATCH_TEXT,'')
    if edit_type == ADD:
        modify_data = edit_details.get(ADD_TEXT,'')
    else:
        modify_data = edit_details.get(REPLACE_TEXT,'')
    placement = edit_details.get(PLACEMENT, END)
    recursive = edit_details.get(RECURSIVE, ALL)
    search_from = edit_details.get(SEARCH_FROM, LEFT)
    linked_files = edit_details.get(LINKED_FILES, [])
    
    search_option = None
    modify_option = None
    
    ## TODO: Skip edit data that has already been prepared and no changes needed.
    if type(match_data) == dict and len(match_data) >= 1:
        
        match_text = match_data.get(TEXT, '')
        search_option = match_data.get(OPTIONS, None)
        
        if search_option == NO_MATCH_CASE: # Right now this is only setup for "one" search option at a time.
            if type(match_text) == list:
                i = 0
                while i < len(match_text):
                    text = match_text.pop(i)
                    match_text.insert(i, text.casefold())
                    i += 1
            else:
                match_text = match_text.casefold()
            
            searchable_text = file_name.casefold()
        
        elif search_option == REGEX: ## TODO
            print('TODO REGEX')
        
        else: # Defualt MATCH_CASE
            searchable_text = file_name
    
    else:
        match_text = match_data
        searchable_text = file_name
    
    '''
    elif type(match_data) == tuple and len(match_data) >= 2:
        match_text = match_data[1]
        
        if match_data[0] == NO_MATCH_CASE:
            search_option = NO_MATCH_CASE
            match_text = match_text.casefold()
            searchable_text = file_name.casefold()
        
        elif match_data[0] == REGEX: ## TODO
            search_option = REGEX
            print('TODO REGEX')
        
        elif modify_data[0] == EXTENTION and len(modify_data) >= 2:
            search_option = EXTENTION
            match_text = match_text.casefold()
            if match_text.find('.') != 0:
                match_text = '.'+match_text
            searchable_text = file_name.casefold()
        
        else: # Defualt MATCH_CASE
            searchable_text = file_name
    
    elif type(match_data) == tuple:
        match_text = match_data[0]
        searchable_text = file_name
    else:
        match_text = match_data
        searchable_text = file_name
    '''
    
    if type(modify_data) == dict and len(modify_data) >= 1:
        
        insert_text = modify_data.get(TEXT, '')
        modify_option = modify_data.get(OPTIONS, None)
        
        if type(insert_text) == list:
            print('TEXT_LIST')
            
            ## TODO: Repeat?
            if renamed_count_max == -1: #and not repeat:
                ##TODO prepare text list if items are tuples
                renamed_count_max = len(insert_text)
            
            #if renamed_count == renamed_count_max:
                #if repeat == true
                    #reset
                    #insert_text = modify_data.get(TEXT, '')
            
            ## TODO: Handle dynamic text
            '''if type(insert_text_list[match_index]) == tuple:
                dynamic_text = insert_text_list.pop(match_index)
                dynamic_text_data = prepareDynamicText(dynamic_text, renamed_count)
                insert_text_list.insert(match_index, dynamic_text_data[0])'''
        
        
        
        
        elif type(insert_text) == tuple:
            
            if modify_option == COUNT:
                
                # Get Starting/Ending Count
                if type(insert_text[DYNAMIC_TEXT]) == tuple:
                    if insert_text[DYNAMIC_TEXT][STARTING_COUNT] > renamed_count:
                        renamed_count = insert_text[DYNAMIC_TEXT][STARTING_COUNT]
                        if len(insert_text[DYNAMIC_TEXT]) == 2:
                            renamed_count_max = insert_text[DYNAMIC_TEXT][ENDING_COUNT]
                else:
                    if insert_text[DYNAMIC_TEXT] > renamed_count:
                        renamed_count = insert_text[DYNAMIC_TEXT]
                        renamed_count_max = -1
                
                insert_text = insert_text[STARTING_TEXT] + str(renamed_count) + insert_text[ENDING_TEXT] if len(insert_text) > 2 else ''
            
            elif modify_option == COUNT_TO:
                
                renamed_count_max = insert_text[DYNAMIC_TEXT] - 1
                insert_text = insert_text[STARTING_TEXT]
            
            elif modify_option == RANDOM: ## TODO
                print('TODO RANDOM')
            
            elif modify_option == TEXT_LIST: ## TODO
                print('TODO TEXT_LIST')
            
            elif modify_option == REGEX: ## TODO
                print('TODO REGEX')
            
        else:
            insert_text = modify_data
    
    '''elif type(modify_data) == tuple and len(modify_data) >= 2:
        
        if modify_data[0] == COUNT and len(modify_data) >= 3:
            
            # Get Starting Count
            if type(modify_data[2]) == tuple:
                if modify_data[2][0] > renamed_count:
                    renamed_count = modify_data[2][0]
                    if len(modify_data[2]) >= 2:
                        renamed_count_max = modify_data[2][1]
            else:
                if modify_data[2] > renamed_count:
                    renamed_count = modify_data[2]
                    renamed_count_max = -1
            
            insert_text = modify_data[1] + str(renamed_count) + modify_data[3] if len(modify_data) > 3 else ''
        
        if modify_data[0] == COUNT_TO and len(modify_data) >= 3:
            renamed_count_max = modify_data[1] - 1
            insert_text = modify_data[2]
        
        elif match_data[0] == RANDOM: ## TODO
            print('TODO RANDOM')
        
        elif match_data[0] == TEXT_LIST: ## TODO
            print('TODO TEXT_LIST')
        
        elif match_data[0] == REGEX: ## TODO
            print('TODO REGEX')
        
        elif modify_data[0] == EXTENTION and len(modify_data) >= 2:
            modify_option = EXTENTION
            insert_text = modify_data[1]
            if insert_text.find('.') != 0 and len(insert_text) > 0:
                insert_text = '.'+insert_text
            recursive = 1
            search_from = RIGHT
        
    elif type(modify_data) == tuple:
         insert_text = modify_data[0]
    else:
         insert_text = modify_data'''
    
    if placement == EXTENTION or type(placement) == tuple and placement[0] == EXTENTION: #list(placement.values())[0] == EXTENTION:
        ##TODO: if list, need to loop through it
        if len(match_text) > 0 and match_text.find('.') != 0:
            match_text = '.'+match_text
        
        ext_index = searchable_text.rfind('.')
        searchable_text = searchable_text[ext_index:]
        
        if len(insert_text) > 0 and insert_text.find('.') != 0:
            insert_text = '.'+insert_text
    
    return (edit_type, insert_text, placement, match_text, insert_text, recursive, search_from, linked_files, searchable_text, search_option, modify_option, renamed_count, renamed_count_max)


### 
###     (insert_text) The dynamic text.
###     (renamed_count) 
###     (renamed_count_max) 
###     --> Returns a [Tuple] 
def prepareDynamicText(insert_text, renamed_count, renamed_count_max = -1):
    # Get Starting/Ending Count
    if type(insert_text[DYNAMIC_TEXT]) == tuple:
        if insert_text[DYNAMIC_TEXT][STARTING_COUNT] > renamed_count:
            renamed_count = insert_text[DYNAMIC_TEXT][STARTING_COUNT]
            if len(insert_text[DYNAMIC_TEXT]) == 2:
                renamed_count_max = insert_text[DYNAMIC_TEXT][ENDING_COUNT]
    else:
        if insert_text[DYNAMIC_TEXT] > renamed_count:
            renamed_count = insert_text[DYNAMIC_TEXT]
            renamed_count_max = -1
    
    insert_text = insert_text[STARTING_TEXT] + str(renamed_count) + insert_text[ENDING_TEXT] if len(insert_text) > 2 else ''
    return (insert_text, renamed_count, renamed_count_max)


### "Find and Add" text within a file name.
###     (file_path) The full path to a file.
###     (match_text_list) The text to find in the String. Will be changed into a list if not already.
###     (insert_text_list) The text to add within the String. Will be changed into a list if no already.
###     (placement) Where to place the inserted text
###     (modify_option) 
###     (recursive) Search for all (all = 999) or a specific number of matched text.
###     (search_from) Begain searching from LEFT to right or from RIGHT to left of String.
###     (searchable_file_name) A String that has been modified (lower cased) as to make it searchable.
###     (renamed_number) 
###     (renamed_count) 
###     --> Returns a [String] 
def insertTextIntoFileName(file_path, edit_type, match_text_list, insert_text_list, placement, modify_option, recursive = ALL, search_from = LEFT, searchable_file_name = '', renamed_number = 0, renamed_count = 0):
    
    searchable_file_name = file_path.name if searchable_file_name == '' else searchable_file_name
    
    if type(match_text_list) != list:
        match_text_list = [match_text_list]
    if type(insert_text_list) != list:
        insert_text_list = [insert_text_list]
    
    i = -1
    for match_text in match_text_list:
        
        i += 1
        if modify_option == SAME_MATCH_INDEX:
            if len(insert_text_list) != len(match_text_list):
                print('/nYour using the SAME_MATCH_INDEX option, but your MATCH_TEXT list is larger or smaller than your REPLACE_TEXT / ADD_TEXT list.')
                input('Did you mean to do this? Press "Enter" if so to continue...')
            match_index = i
        elif len(insert_text_list) > 1:
            if modify_option == REPEAT_TEXT_LIST:
                renamed_number = resetIfMaxed(renamed_number, len(insert_text_list))
            match_index = renamed_number
        else:
            match_index = 0
        
        ## TODO: Handle dynamic text
        if type(insert_text_list[match_index]) == tuple:
            dynamic_text = insert_text_list.pop(match_index)
            dynamic_text_data = prepareDynamicText(dynamic_text, renamed_count)
            insert_text_list.insert(match_index, dynamic_text_data[0])
        
        
        
        if searchable_file_name.find(match_text) == -1:
            new_file_name = file_path.name
        else:
            match_size = len(match_text)
            new_file_name = file_path.name
            file_renamed = True
            
            index_matches = []
            index_match = 0
            start = 0
            end = -1
            if match_size > 0:
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
            #print(index_matches)
            
            if edit_type == ADD:
                
                if type(placement) == dict:
                    
                    if OF_MATCH in placement.values():
                        
                        for index in index_matches:
                            if START in placement: # or LEFT
                                new_file_name = new_file_name[:index] + insert_text_list[match_index] + new_file_name[index:]
                            elif END in placement: # or RIGHT
                                new_file_name = new_file_name[:index + match_size] + insert_text_list[match_index] + new_file_name[index + match_size:]
                            elif BOTH in placement:
                                new_file_name = new_file_name[:index] + insert_text_list[match_index] + new_file_name[index:index + match_size] + insert_text_list[match_index] + new_file_name[index + match_size:]
                            elif EXTENTION in placement:
                                new_file_name = f"{file_path.name}{insert_text_list[match_index]}"
                            else:
                                file_renamed = False
                    
                    elif OF_FILE_NAME in placement.values():
                        new_file_name = addToFileName(file_path, insert_text_list[match_index], list(placement)[0])
                
                    '''elif type(placement) == tuple:
                    new_file_name = addToFileName(file_path, insert_text_list[match_index], placement[0])'''
                
                else:
                    new_file_name = addToFileName(file_path, insert_text_list[match_index], placement)
            
            elif edit_type == REPLACE:
                
                if type(placement) == dict and list(placement.values())[0] == EXTENTION:
                    if searchable_file_name == match_text:
                        new_file_name = f"{file_path.stem}{insert_text_list[match_index]}"
                elif placement == EXTENTION:
                    if searchable_file_name == match_text:
                        new_file_name = f"{file_path.stem}{insert_text_list[match_index]}"
                else:
                    for index in index_matches:
                        new_file_name = new_file_name[:index] + insert_text_list[match_index] + new_file_name[index + match_size:]
            
            elif edit_type == RENAME:
                
                if match_size == 0 or searchable_file_name.find(match_text) > -1:
                    new_file_name = insert_text_list[match_index] + file_path.suffix  ## TODO: could/should I change extention along with the file name?
            
            #if file_renamed: ## TODO: record all edits or just if the filename was renamed?
            #    edit_count += 1
            
            break # Match was found so break loop
    
    return new_file_name


### Add text to file name using a simple placement.
###     (file_path) The full path to a file.
###     (add_text) The text to add to the file name.
###     (placement) Where to place the added text
###     --> Returns a [String] 
def addToFileName(file_path, add_text, placement):
    if placement == START: # or LEFT
        new_file_name = f"{add_text}{file_path.stem}{file_path.suffix}"
    elif placement == END: # or RIGHT
        new_file_name = f"{file_path.stem}{add_text}{file_path.suffix}"
    elif placement == BOTH:
        new_file_name = f"{add_text}{file_path.stem}{add_text}{file_path.suffix}"
    elif placement == EXTENTION:
        new_file_name = f"{file_path.name}{add_text}"
    else:
        new_file_name = file_path.name
    return new_file_name


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


### Rename a file...
###     (file_path) The full path to file.
###     (new_file_path) The full path to file.
###     (edit_details) All the details on how to proceed with the file name edits. 
###                    Dictionary[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM, SUB_DIRS]
###     (files_renamed_data) Number of files renamed so far and the current count (added to file name if COUNT used)
###                          that should be looped back into function, and increased if file is renamed.
###     --> Returns a [Tuple] files_renamed_data
def renameFile(file_path, new_file_path, edit_details, files_renamed_data):
    renamed_number = files_renamed_data[FILES_RENAMED]
    renamed_count = files_renamed_data[FILE_NAME_COUNT]
    renamed_count_max = files_renamed_data[FILE_NAME_COUNT_MAX]
    files_to_skip = files_renamed_data[SKIPPED_FILES]
    
    does_file_exist = checkIfFileExist(new_file_path, file_path)
    
    if does_file_exist == CANCEL: # Will throw error, but will stop any further renaming.
        print('Canceling any further renaming and closing...')
        new_file_path = file_path.rename(new_file_path) # Error
    
    elif does_file_exist == NO: # Actually renaming file
        new_file_path = file_path.rename(new_file_path)
        file_renamed = True
        renamed_number += 1
    
    elif does_file_exist == CONTINUE: # Skip this count (+1) and try again (recursively).
        file_renamed = False
        files_to_skip.append(new_file_path) # And keep skipping this file if it comes up again.
        files_renamed_data = startingFileRenameProcedure(file_path, edit_details, (renamed_number, renamed_count + 1, renamed_count_max, files_to_skip))
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
    
    return (renamed_number, renamed_count, renamed_count_max, files_to_skip)


### Update any files that have links to the renamed files to prevent broken links in whatever app that use the renamed files.
###     (linked_file) The full path to a file with links.
###     (old_file_path) A String of the full path to a file before renaming.
###     (new_file_path) A String of the full path to a file after renaming.
###     --> Returns a [Boolean] 
def updateLinksInFile(linked_file, old_file_path, new_file_path):
    linked_file = Path(linked_file)
    
    read_data = linked_file.read_text()
    
    # Replace all style of slashes in links
    old_file_path_esc = old_file_path.replace('\\', '\\\\')
    new_file_path_esc = new_file_path.replace('\\', '\\\\')
    old_file_path_rev = old_file_path.replace('\\', '/')
    new_file_path_rev = new_file_path.replace('\\', '/')
    
    write_data = read_data.replace(old_file_path_esc, new_file_path_esc)
    write_data = write_data.replace(old_file_path_rev, new_file_path_rev)
    write_data = write_data.replace(old_file_path, new_file_path)
    
    if read_data == write_data:
        data_changed = False
    else:
        data_changed = True
        linked_file.write_text(write_data)
    
    return data_changed


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
    if string_num == 'a' or string_num == 'all' or string_num == 'showall' or string_num == 'sa':
        number = ALL
    elif string_num.find('show') > -1:
        number = string_num.partition('show')[2]
        number = strNumberToInt(str(int(number)+1000))
    elif string_num.isnumeric():
        number = int(string_num)
    else:
        number = NONE
    return number


### Convert all the integers used in presets into readable text.
###     (number) Depending on the option, change this number (if Integer) into text.
###     (option) The current option.
###     (lvl) The index level of the number if it's in a Tuple.
###     --> Returns a [String] 
def intToStrText(key, value, parent_key = None):
    text = str(value)
    if type(key) == int:
        text = str(key)
        
        if parent_key == None:
            if key == EDIT_TYPE:
                text = 'Edit Type              '
            elif key == ADD_TEXT:
                text = 'Add Text               '
            elif key == PLACEMENT:
                text = 'Placement              '
            elif key == MATCH_TEXT:
                text = 'Match Text             '
            elif key == REPLACE_TEXT:
                text = 'Replace Text           '
            elif key == RECURSIVE:
                text = 'Edits Per Rename       '
            elif key == SEARCH_FROM:
                text = 'Start Search From The  '
            elif key == LINKED_FILES:
                text = 'Files With Links       '
            elif key == SUB_DIRS:
                text = 'Include Sub Directories'
            elif key == PRESORT_FILES:
                text = 'Pre-Sort Files         '
        
        if parent_key == PLACEMENT:
            if key == START:
                text = 'Start'
            elif key == END:
                text = 'End'
            elif key == BOTH_ENDS:
                text = 'Both Ends'
            if value == EXTENTION:
                text += ' of Extention'
            elif value == OF_FILE_NAME:
                text += ' of File Name'
            elif value == OF_MATCH:
                text += ' of Match'
        
        elif parent_key == ADD_TEXT or parent_key == MATCH_TEXT or parent_key == REPLACE_TEXT:
            if key == TEXT:
                text = 'TEXT : ' + str(value)
            if key == OPTIONS:
                text = '\n                              OPTIONS : '
                if value == MATCH_CASE:
                    text += 'Search Case Sensitive'
                elif value == NO_MATCH_CASE:
                    text += "Search Not Case Sensitive"
                elif value == COUNT:
                    text += 'Add An Incrementing Number To Text'
                elif value == COUNT_TO:
                    text += 'Max Files To Rename'
                elif value == RANDOM:
                    text += 'Add Random Numbers/Text'
                elif value == TEXT_LIST:
                    text += 'List Of Text Strings'
                elif value == REGEX:
                    text += 'Regular Expressions'
                elif value == SAME_MATCH_INDEX:
                    text += 'Use Match Index While Selecting From Add/Replace Text List'
                elif value == REPEAT_TEXT_LIST:
                    text += 'Once End of Text List Reached, Repeat List'
        
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
    
    if key == None:
        if type(value) == str:
            text = f'"{str(value)}"'
        elif parent_key == EDIT_TYPE:
            if value == ADD:
                text = 'Add'
            elif value == REPLACE:
                text = 'Replace'
            elif value == RENAME:
                text = 'Rename'
        elif parent_key == RECURSIVE and value == ALL:
            text = 'Edit All'
        elif parent_key == SEARCH_FROM:
            if value == LEFT:
                text = 'Left'
            elif value == RIGHT:
                text = 'Right'
        else:
            text = str(value)
    
    return text


### Reset a number back to 0 if it hits the max.
###     (number) The number.
###     (max) Max limit to the number.
###     --> Returns a [Integer] 
def resetIfMaxed(number, max):
    if number >= max:
        number = number - max
        number = resetIfMaxed(number, max)
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
    files_renamed_data = (0,0,-1,[])
    
    try:
        # Check if at least one file or directory was dropped
        dropped_file = files[0]
        print('Number of Files or Directories Dropped: [ %s ]' % len(files))
        
        global use_preset
        if use_preset:
            edit_details = preset
            print('\nUsing...')
            displayPreset(preset_options, select_preset)
            print('\n')
            #input('\nContinue...')
        
        else:
            print('Do you wish to select a preset or do more simple file renaming by answering a few questions?')
            use_preset = input('Use Presets [ Y / N ]: ')
            use_preset = yesTrue(use_preset)
            
            if use_preset:
                
                preset_selection = NONE
                while preset_selection == NONE:
                    print('\nSelect a Preset Option [ # ] ')
                    preset_selection = input('Or Type [ Show# ] or [ ShowAll ] To Display Presets: ')
                    preset_selection = strNumberToInt(preset_selection)
                    
                    if preset_selection == ALL:
                        displayPreset(preset_options)
                        preset_selection = NONE
                    
                    elif preset_selection > 999:
                        preset_selection -= 1000
                        if preset_selection < len(preset_options):
                            displayPreset(preset_options, preset_selection)
                        preset_selection = NONE
                    
                    elif preset_selection < len(preset_options) and preset_selection > NONE:
                        edit_details = preset_options[preset_selection]
                        print('Preset [ #%s ] Selected' % preset_selection)
                    
                    else:
                        preset_selection = NONE
            
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
        
        # Presort Files
        files_meta = sortFiles(files, edit_details.get(PRESORT_FILES,None))
        
        # Iterate over all dropped files including all files in dropped directories
        include_sub_dirs = -1
        for file in files_meta:
            file_path = file[FILE_PATH]
            
            #if os.path.isdir(file_path):
            if Path.is_dir(file_path):
                
                if include_sub_dirs == -1 and not use_preset: # Only answer once
                    include_sub_dirs = input('Search through sub-directories too? [ Y / N ]: ')
                    include_sub_dirs = yesTrue(include_sub_dirs)
                else:
                    include_sub_dirs = preset.get(SUB_DIRS, False)
                
                files_renamed += renameAllFilesInDirectory(file_path, edit_details, include_sub_dirs)
            
            #elif os.path.isfile(file_path):
            elif Path.is_file(file_path):
                #print('\n')
                files_renamed_data = startingFileRenameProcedure(file_path, edit_details, files_renamed_data)
            
            else:
                print( os.path.isfile(file_path) )
                print("\nThis is not a normal file of directory (socket, FIFO, device file, etc.) and so this script won't be renameing it." )
                
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
    
