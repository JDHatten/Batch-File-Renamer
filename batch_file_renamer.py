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
    [DONE] Use more than one search/modify option at a time.
    [] Special search and edits. Examples: 
        [X] Find file names with a string then add another string at end of the file name.
        [X] Find file names with a string then rename entire file name and stop/return/end.
        [X] Find file names with a string then add another string specifically next to matched string.
        [X] Add an iterated number to file names.
        [X] Find specific file name extensions and only change (or add to) the extension
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
#EXTENSION = 8 ## moved to OPTIONS

# EDIT_DETAILS
EDIT_TYPE = 0
MATCH_TEXT = 1
INSERT_TEXT = 2
RENAME_LIMIT = 3 ## TODO should this be a hard limit or limit per drop/sub-dir?
LINKED_FILES = 7
SUB_DIRS = 8
PRESORT_FILES = 9
TRACKED_DATA = 99

FILE_PATH = 0
FILE_NAME = 1
FILE_SIZE = 2

# TRACKED_DATA
FILES_RENAMED = 0
FILE_NAME_COUNT = 1
FILE_NAME_COUNT_LIMIT = 2
CURRENT_LIST_INDEX = 3
CURRENT_FILE_NAME = 4
SKIPPED_FILES = 5

AMOUNT = 0
INDEX_POINTER = 0
LIMIT = 1
UPDATE_COUNT = 1
UPDATE_LIMIT = 1

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

TEXT = 0
OPTIONS = 1
PLACEMENT = 2

STARTING_TEXT = 0
DYNAMIC_TEXT = 1
ENDING_TEXT = 2

STARTING_COUNT = 0
ENDING_COUNT = 1

### Search/Modify/Sort Options
MATCH_CASE = 0          # Defualt
NO_MATCH_CASE = 1       # Not a case sensitive search.
SEARCH_FROM_RIGHT = 2   # Start searching from right to left.  Defualt: SEARCH_FROM_LEFT
MATCH_LIMIT = 3         # Matches to make (or text inserts) per file name.  Defualt: (MATCH_LIMIT, NO_LIMIT)
SAME_MATCH_INDEX = 4    # When a match is made from the "MATCH_TEXT List" use the same index when choosing text from the "INSERT_TEXT List".
                        # Useful when makeing a long lists of specfic files to find and rename.

EXTENSION = 10          # ADD (to end of the entire file name) REPLACE (just the extension) or RENAME (the entire file name if a '.' is in text).
                        # If used in MATCH_TEXT Options, (unless RENAME) only the extension will be searched and not the rest of the file name.
                        # If used in INSERT_TEXT Options, only the extension will be replaced or added to, unless RENAME where the entire file name may be rewriten.
REGEX = 11              ## TODO: Regular Expressions

COUNT = 20              # Iterate a number that is added to a file name. (Starting Number, Ending Number) Ending number is optional.
                        # NOTE: Resets after each directory change.
COUNT_TO = 21           # Max amount of renames to make before stopping.  Similer to COUNT's ending number without adding an iterating number to a file name.
MINIMUM_DIGITS = 23     ## TODO: Minimum digits for any dynamic text used, i.e. 3 = 003, RANDOM Digits?
RANDOM = 24             ## TODO: Generate random numbers or text that is added to file names.
REPEAT_TEXT_LIST = 25   # Once the end of a text list is reached, repeat it.  Text must be dynamic, i.e. COUNT, RANDOM, etc.

ASCENDING = 30          # 0-9, A-Z
DESCENDING = 31         # 9-0, Z-A
ALPHABETICALLY = 32     # Alphabetically Ordered
FILE_SIZE = 33          # File size in bytes
DATE_ACCESSED = 34      # Date file last opened.
DATE_MODIFIED = 35      # Date file last changed.
DATE_CREATED = 36       # Date file created. (Windows Only)
DATE_META_MODIFIED = 36 # Date file's meta data last updated. (UNIX)


### After initial drop and file renaming, ask for additional files or just quit the script.
loop = True

### Present Options - Used to skip questions and immediately start renaming all dropped files.
### Much more complex renaming possibilities are avaliable when using presets.
### Make sure to select the correct preset (select_preset)
use_preset = True
select_preset = 7

preset0 = {     # Defualts
  EDIT_TYPE     : ADD,      # ADD or REPLACE or RENAME (entire file name, minus extension) [Required]
  MATCH_TEXT    : '',       # 'Text' to Find  -OR- Dict{ TEXT : 'Text', OPTIONS : Search Options }
  INSERT_TEXT   : '',       # 'Text' to Replace with -OR- Dict{ TEXT : 'Text', OPTIONS : Modify Options, PLACEMENT : (PLACE, OF_) } [TEXT Required]
  LINKED_FILES  : [],       # File Paths of files that need to be updated of any file name changes to prevent broken links in apps. (Use double slashes "//")
  SUB_DIRS      : False,    # Search Sub-Directories (True or False)
  PRESORT_FILES : None      # Sort before renaming files.  Dict{ Sort Option : ASCENDING or DESCENDING }
}                           # Note: Dynamic Text Format = Tuple('Starting Text', Integer/Tuple/List, 'Ending Text') -OR- just a List['Text',...]
preset1 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : { TEXT : '(Text)', OPTIONS : [ (MATCH_LIMIT, 1), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT   : { TEXT : '[Text]' },
  SUB_DIRS      : True
}
preset2 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : '123',
  INSERT_TEXT   : 'abc',
  SUB_DIRS      : False
}
preset3 = {
  EDIT_TYPE     : ADD,
  INSERT_TEXT   : { TEXT        : ' (U)',
                    PLACEMENT   : END },
  SUB_DIRS      : True
}
preset4 = {
  EDIT_TYPE     : RENAME,
  MATCH_TEXT    : { TEXT : '', OPTIONS : NO_MATCH_CASE },
  INSERT_TEXT   : { TEXT : ('TextTextText-[', (1,7), ']'), OPTIONS : COUNT },
  SUB_DIRS      : True
}
preset5 = {
  EDIT_TYPE     : ADD,
  MATCH_TEXT    : { TEXT : 'Text', OPTIONS : MATCH_CASE },
  INSERT_TEXT   : { TEXT : ('--(', 1, ')'), OPTIONS : COUNT, PLACEMENT : END },
  SUB_DIRS      : True
}
preset6 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : { TEXT : 'Tex', OPTIONS : [ MATCH_CASE, (MATCH_LIMIT, 4), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT   : { TEXT : ('(', 0, ')'), OPTIONS : COUNT },
  SUB_DIRS      : False
}
preset7 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : { TEXT : '.txt2', OPTIONS : [ NO_MATCH_CASE, EXTENSION ] },
  INSERT_TEXT   : { TEXT : 'txt', OPTIONS : EXTENSION },
}
preset8 = {
  EDIT_TYPE     : ADD,
  MATCH_TEXT    : { TEXT : 'txt', OPTIONS : [ EXTENSION ] },
  INSERT_TEXT   : { TEXT : 'bck', OPTIONS : EXTENSION },
}
preset9 = {
  EDIT_TYPE     : ADD,
  MATCH_TEXT    : { TEXT        : 'text',
                    OPTIONS     : [ MATCH_CASE, (MATCH_LIMIT, 2), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT   : { TEXT        : 'XXX',
                    PLACEMENT   : ( BOTH_ENDS, OF_MATCH ) },
}
preset10 = {
  EDIT_TYPE     : ADD,
  MATCH_TEXT    : { TEXT : 'name', OPTIONS : [ NO_MATCH_CASE, (MATCH_LIMIT, 1), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT   : { TEXT : ('-XXX', 3), OPTIONS : COUNT_TO, PLACEMENT : (END, OF_MATCH) },
}
preset11 = {
  EDIT_TYPE     : RENAME,
  MATCH_TEXT    : { TEXT : '', OPTIONS : NO_MATCH_CASE },
  INSERT_TEXT   : { TEXT : ('TextTextText-[', (1,7), ']'), OPTIONS : COUNT },
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
  PRESORT_FILES : { DATE_MODIFIED : DESCENDING }
}
preset12 = {
  EDIT_TYPE     : ADD,
  INSERT_TEXT   : { TEXT : ' (U)', PLACEMENT : END },
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
  SUB_DIRS      : True
}
preset13 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : { TEXT : ' (U)', OPTIONS : [ MATCH_CASE, (MATCH_LIMIT, 1), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT   : { TEXT : '' },
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
  SUB_DIRS      : True
}
preset14 = {
  EDIT_TYPE     : RENAME,
  MATCH_TEXT    : { TEXT        : ['[1]','[2]','[3]','[4]','[5]'],
                    OPTIONS     : [NO_MATCH_CASE, SAME_MATCH_INDEX] },
  INSERT_TEXT   : { TEXT        : ['NewName-01','ThisName-02','AName-03','NotAName-04','NameName-05'],
                    OPTIONS     : None },
  LINKED_FILES  : ['V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt'],
}
preset15 = {
  EDIT_TYPE     : ADD,
  MATCH_TEXT    : { TEXT        : [ 'text', 'name' ],
                    OPTIONS     : [ NO_MATCH_CASE, (MATCH_LIMIT, 3), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT   : { TEXT        : [ ('-(', (1,2), ')-'), ('--[', (1,2), ']--') ],
                    OPTIONS     : [ COUNT, REPEAT_TEXT_LIST ],
                    PLACEMENT   : ( END, OF_MATCH ) },
  RENAME_LIMIT  : NO_LIMIT,
  LINKED_FILES  : [ 'V:\\Apps\\Scripts\\folder with spaces\\file_with_links.txt' ],
}
preset16 = {
  EDIT_TYPE     : REPLACE,
  MATCH_TEXT    : { TEXT        : [ '.rarzzz', '.zipzzz' ],
                    OPTIONS     : [ NO_MATCH_CASE, EXTENSION ] },
  INSERT_TEXT   : { TEXT        : [ ('.r', (0), ''), ('.z', (0), '') ],
                    OPTIONS     : [ COUNT, EXTENSION, REPEAT_TEXT_LIST, (MINIMUM_DIGITS, 2) ] }, ## TODO
  RENAME_LIMIT  : NO_LIMIT,
}
preset_options = [preset0,preset1,preset2,preset3,preset4,preset5,preset6,preset7,preset8,preset9,preset10,preset11,preset12,preset13,preset14,preset15,preset16]
preset = preset_options[select_preset]


### Display one or all file rename preset options.
###     (preset) A List of file rename presets. Or a single preset Dictionary.
###     (number) Only show specific preset in List.
###     --> Returns a [None] 
def displayPreset(presets, number = -1):
    if type(presets) == list and number == -1:
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
        if type(presets) == dict:
            print('\nCurrent Preset In Use')
        else:
            presets = presets[number]
            print('\nPreset %s' % str(number))
        for option, mod in presets.items():
            opt_str = intToStrText(option, 'Preset Options')
            mod_str = ''
            if type(mod) == dict:
                for key, value in mod.items():
                    mod_str += intToStrText(key, value, option) + '  '
            else:
                mod_str = intToStrText(None, mod, option)
            print('    %s : %s' % (opt_str, mod_str))
    
    return None


### Iterate over all files in a directory for the purpose of renaming each file that matches the edit conditions.
###     (some_dir) The full path to a directory. Str("path\to\file")
###     (edit_details) All the details on how to proceed with the file name edits. 
###                    Dictionary[EDIT_TYPE, INSERT_TEXT, PLACEMENT, MATCH_TEXT, INSERT_TEXT, RECURSIVE, SEARCH_FROM, SUB_DIRS]
###     (include_sub_dirs) Search sub-directories for more files.  Boolean(True) or Boolean(False)
###     --> Returns a [Integer] Number of files renamed.
def renameAllFilesInDirectory(some_dir, edit_details, include_sub_dirs = False):
    assert Path.is_dir(some_dir) # Error if not directory or doen't exist
    
    files_renamed = 0
    
    for root, dirs, files in os.walk(some_dir):
        
        print('\n-Root: %s\n' % (root))
        
        #for dir in dirs:
            #print('--Directory: [ %s ]' % (dir))
        
        # Sort Files
        files_meta = sortFiles(files, edit_details.get(PRESORT_FILES,None), root)
        
        # Prepare Edit Details and add Tracker 
        edit_details_copy = copyEditDetails(edit_details, files_renamed)
        #displayPreset(edit_details_copy)
        
        for file in files_meta:
            #print('--File: [ %s ]' % (file[FILE_NAME]))
            file_path = Path(file[FILE_PATH])
            
            edit_details_copy = startingFileRenameProcedure(file_path, edit_details_copy)
            displayPreset(edit_details_copy)
            tracked_data = edit_details_copy[TRACKED_DATA]
            
            if tracked_data[FILES_RENAMED][LIMIT] != NO_LIMIT and tracked_data[FILES_RENAMED][AMOUNT] > tracked_data[FILES_RENAMED][LIMIT]:
                #print('[FILES_RENAMED][LIMIT] hit')
                break # File rename limit hit, stop and move on to next directory.
            if allCountLimitsHitCheck(tracked_data):
                #print('allCountLimitsHitCheck: True')
                break # File count limit hit, stop and move on to next directory.
        
        files_renamed += edit_details_copy[TRACKED_DATA][FILES_RENAMED][AMOUNT]
        
        if not include_sub_dirs:
            break
    
    # Add the entire amount of renames made in this last update; for this directory drop, which may include sub-directories.
    edit_details_copy = updateTrackedData(edit_details_copy, { FILES_RENAMED : files_renamed }, False)
    
    return edit_details_copy

### Copy and add a data tracker to edit_details
###     (edit_details) All the details on how to proceed with the file name edits.
###     --> Returns a [Dictionary] 
def copyEditDetails(edit_details, files_renamed = 0):
    edit_details_copy = edit_details.copy()
    
    rename_limit = edit_details_copy.get(RENAME_LIMIT, NO_LIMIT)
    modify_options = getOptions(edit_details_copy[INSERT_TEXT])
    
    fnc = []
    fncl = []
    
    if type(edit_details_copy[INSERT_TEXT]) == dict:
        
        ##TODO: if RANDOM, REGEX, etc., get correct starting data
        
        if type(edit_details_copy[INSERT_TEXT][TEXT]) == tuple:
            if type(edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT]) == tuple:
                # Assumed COUNT
                fnc.append( edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT][STARTING_COUNT] )
                fncl.append( edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT][ENDING_COUNT] )
            else:
                if COUNT in modify_options:
                    fnc.append( edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT] )
                    fncl.append( NO_LIMIT )
                elif COUNT_TO in modify_options:
                    fnc.append( 1 )
                    fncl.append( edit_details_copy[INSERT_TEXT][TEXT][DYNAMIC_TEXT] )
        
        elif type(edit_details_copy[INSERT_TEXT][TEXT]) == list:
            rename_limit = NO_LIMIT if REPEAT_TEXT_LIST in modify_options else len(edit_details_copy[INSERT_TEXT][TEXT])
            
            for text in edit_details_copy[INSERT_TEXT][TEXT]:
                if type(text) == tuple:
                    if type(text[DYNAMIC_TEXT]) == tuple:
                        # Assumed COUNT
                        fnc.append( text[DYNAMIC_TEXT][STARTING_COUNT] )
                        fncl.append( text[DYNAMIC_TEXT][ENDING_COUNT] )
                    else:
                        if COUNT in modify_options:
                            fnc.append( text[DYNAMIC_TEXT] )
                            fncl.append( NO_LIMIT )
                        elif COUNT_TO in modify_options:
                            fnc.append( 1 )
                            fncl.append( text[DYNAMIC_TEXT] )
    
    if not fnc:
        fnc.append(0)
    if not fncl:
        fncl.append(NO_LIMIT)
    
    edit_details_copy.update( { TRACKED_DATA : { FILES_RENAMED : [files_renamed, rename_limit],
                                                 FILE_NAME_COUNT : fnc,
                                                 FILE_NAME_COUNT_LIMIT : fncl,
                                                 CURRENT_LIST_INDEX : NONE,
                                                 CURRENT_FILE_NAME : '',
                                                 SKIPPED_FILES : [] } } )
    
    return edit_details_copy


### 
###     (edit_details) 
###     (update_data) 
###     --> Returns a [Dictionary] 
def updateTrackedData(edit_details, update_data, append_values = True):
    if FILES_RENAMED in update_data:
        if append_values:
            edit_details[TRACKED_DATA][FILES_RENAMED][AMOUNT] = edit_details[TRACKED_DATA][FILES_RENAMED][AMOUNT] + update_data[FILES_RENAMED]
        else:
            edit_details[TRACKED_DATA][FILES_RENAMED][AMOUNT] = update_data[FILES_RENAMED]
    
    if FILE_NAME_COUNT in update_data:
        index = update_data[FILE_NAME_COUNT][INDEX_POINTER]
        update_count = update_data[FILE_NAME_COUNT][UPDATE_COUNT]
        edit_details[TRACKED_DATA][FILE_NAME_COUNT][index] = edit_details[TRACKED_DATA][FILE_NAME_COUNT][index] + update_count
    
    if FILE_NAME_COUNT_LIMIT in update_data:
        index = update_data[FILE_NAME_COUNT_LIMIT][INDEX_POINTER]
        update_count_limit = update_data[FILE_NAME_COUNT_LIMIT][UPDATE_LIMIT]
        edit_details[TRACKED_DATA][FILE_NAME_COUNT_LIMIT][index] = edit_details[TRACKED_DATA][FILE_NAME_COUNT_LIMIT][index] + update_count_limit
    
    if CURRENT_LIST_INDEX in update_data:
        edit_details[TRACKED_DATA][CURRENT_LIST_INDEX] = update_data[CURRENT_LIST_INDEX]
    
    if CURRENT_FILE_NAME in update_data:
        edit_details[TRACKED_DATA][CURRENT_FILE_NAME] = update_data[CURRENT_FILE_NAME]
    
    if SKIPPED_FILES in update_data:
        edit_details[TRACKED_DATA][SKIPPED_FILES].append( update_data[SKIPPED_FILES] )
        edit_details[TRACKED_DATA][FILE_NAME_COUNT] = edit_details[TRACKED_DATA][FILE_NAME_COUNT] + update_data[FILE_NAME_COUNT]
    
    return edit_details


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


### Starting file name procedures using the edit details.
###     (some_file) The full path to a file.
###     (edit_details) All the details on how to proceed with the file name edits.
###     --> Returns a [Dictionary] 
def startingFileRenameProcedure(some_file, edit_details):
    file_path = Path(some_file)
    assert Path.is_file(file_path) # Error if not a file or doen't exist
    file_renamed = False
    skip_file = False
    
    # Skip any files that already had a name matching previous rename attempts (and not overwritten).
    # Note: This keeps the starting and ending COUNT exactly as typed with no skipping numbers.
    # (3,9) will always be (3,9) and not (5,9) due to files with that same name/count already existing.
    for file in edit_details[TRACKED_DATA][SKIPPED_FILES]:
        if file == file_path:
            skip_file = True
            break
    
    # Create The New File Name
    if not skip_file:
        edit_details = insertTextIntoFileName(file_path, edit_details)
        new_file_name = edit_details[TRACKED_DATA][CURRENT_FILE_NAME]
        file_renamed = False if new_file_name == file_path.name else True
    
    # Rename The File Now
    if file_renamed:
        new_file_path = Path(file_path.parent, new_file_name)
        edit_details = renameFile(file_path, new_file_path, edit_details)
        
        linked_files = edit_details.get(LINKED_FILES, [])
        
        for file in linked_files:
            links_updated = updateLinksInFile(file, str(file_path), str(new_file_path))
            if links_updated:
                print('----Link File Updated: [ %s ]' % (file))
            #else:
                #print('----Link File Not Updated: [ %s ]' % (file))
    
    else:
        print('--File Not Renamed: %s' % (file_path))
    
    return edit_details


### Get the text from a Tuples() that requires an OPTION on how to handle it.
###     (dynamic_text_data) The dynamic text Tuple.
###     (the_dynamic_text) The dynamic text/number to insert into the regular text.
###     --> Returns a [String] 
def getDynamicText(dynamic_text_data, the_dynamic_text):
    starting_text = dynamic_text_data[STARTING_TEXT]
    middle_text = str(the_dynamic_text)
    ending_text = dynamic_text_data[ENDING_TEXT] if len(dynamic_text_data) > 2 else ''
    dynamic_text = starting_text + middle_text + ending_text
    return dynamic_text


### Get all text needed to make a proper search.
###     (search_data) All the search or match data.
###     (file_path) The file path with a file name that will be searched through.
###     (rename_edit) Full file rename edit flag.
###     --> Returns a [Tuple] (match_text, searchable_file_name)
def getSearchData(search_data, file_path, rename_edit = False):
    if type(search_data) == dict and len(search_data) >= 1:
        
        match_text = search_data.get(TEXT, '')
        search_options = search_data.get(OPTIONS, [])
        
        searchable_file_name = file_path.name
        
        if type(search_options) != list:
            search_options = [search_options]
        
        # Defualt MATCH_CASE
        if NO_MATCH_CASE in search_options:
            if type(match_text) == list:
                i = 0
                while i < len(match_text):
                    text = match_text.pop(i)
                    match_text.insert(i, text.casefold())
                    i += 1
            else:
                match_text = match_text.casefold()
            
            searchable_file_name = file_path.name.casefold()
        
        if EXTENSION in search_options and not rename_edit:
            if match_text != '' and match_text.find('.') != 0 :
                match_text = '.'+match_text # Add a '.' if missing
            
            if NO_MATCH_CASE in search_options:
                searchable_file_name = file_path.suffix
                searchable_file_name = searchable_file_name.casefold()
            else:
                searchable_file_name = file_path.suffix
        
        if REGEX in search_options: ## TODO
            print('TODO REGEX')
    
    else:
        match_text = search_data
        searchable_file_name = file_path.name
    
    return (match_text, searchable_file_name)


### Return all or a specific option's value from a data Dictionary.
###     (data) A Dictionary that has an OPTIONS key.
###     (specific_option) Return True (or a value) if specific option found
###     (default) If specific option not found return default
###     --> Returns a [List] or [Boolean] or [Integer]
def getOptions(data, specific_option = None, default = False):
    options = data.get(OPTIONS, [])
    if type(options) != list:
        options = [options]
    if specific_option != None:
        for option in options:
            if type(option) == tuple:
                if option[0] == specific_option:
                    return option[1] # A value, likely a number
            elif option == specific_option:
                return True
        return default
    return options


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
###     (insert_text_length) 
###     (same_match_index) 
###     (repeat_text_list) 
###     --> Returns a [Integer] 
def checkAllAvalibleCountLimits(tracked_data, list_index, insert_text_length = -1, same_match_index = False, repeat_text_list = False, recursive_count = 0):
    dynamic_count = tracked_data[FILE_NAME_COUNT][list_index]
    dynamic_count_limit = tracked_data[FILE_NAME_COUNT_LIMIT][list_index]
    
    if dynamic_count_limit > NO_LIMIT and dynamic_count > dynamic_count_limit:
        # Then check the next index...
        next_list_index = list_index + 1
        
        if same_match_index:
            list_index = -1 # No choosing another index to return, will either be -1 or -2 in the end
            next_list_index = 0 if next_list_index >= insert_text_length else next_list_index
            recursive_count += 1
            if recursive_count <= insert_text_length:
                list_index = checkAllAvalibleCountLimits(tracked_data, next_list_index, insert_text_length, same_match_index, repeat_text_list, recursive_count)
                if list_index > -2: # Only checking if all limits hit, if not go with first called index check, which we alreayd know is -1
                    list_index = -1
            else:
                list_index = -2
        
        elif next_list_index >= insert_text_length:
            recursive_count += 1
            if recursive_count <= insert_text_length:
                list_index = checkAllAvalibleCountLimits(tracked_data, next_list_index, insert_text_length, same_match_index, repeat_text_list, recursive_count)
            else:
                list_index = -2
        
        elif repeat_text_list:
            recursive_count += 1
            if recursive_count <= insert_text_length:
                list_index = checkAllAvalibleCountLimits(tracked_data, 0, insert_text_length, same_match_index, repeat_text_list, recursive_count)
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
    
    edit_type = edit_details[EDIT_TYPE]
    modify_data = edit_details[INSERT_TEXT]
    tracked_data = edit_details[TRACKED_DATA]
    search_options = getOptions(edit_details[MATCH_TEXT])
    same_match_index = SAME_MATCH_INDEX in search_options
    
    if type(modify_data) == dict:
        
        insert_text = modify_data.get(TEXT, '')
        modify_options = getOptions(modify_data)
        
        #renamed_limit = tracked_data[FILES_RENAMED][LIMIT]
        repeat_text_list = REPEAT_TEXT_LIST in modify_options 
        
        if type(insert_text) == list:
            
            insert_text_length = len(insert_text)
            
            if list_index > -1:
                
                if type(insert_text[list_index]) == tuple: # Dynamic Text
                    
                    if COUNT in modify_options or COUNT_TO in modify_options:
                        
                        dynamic_count = tracked_data[FILE_NAME_COUNT][list_index]
                        dynamic_count_limit = tracked_data[FILE_NAME_COUNT_LIMIT][list_index]
                        
                        list_index = checkAllAvalibleCountLimits(tracked_data, list_index, insert_text_length, same_match_index, repeat_text_list)
                        
                        if list_index > -1:
                            dynamic_count = tracked_data[FILE_NAME_COUNT][list_index]
                            #dynamic_count_limit = tracked_data[FILE_NAME_COUNT_LIMIT][list_index]
                            
                            if COUNT in modify_options:
                                insert_text = getDynamicText(insert_text[list_index], dynamic_count)
                            
                            elif COUNT_TO in modify_options:
                                insert_text = insert_text[list_index][STARTING_TEXT]
                        
                        else:
                            insert_text = False
                            #print('A max count limit hit.')
                    
                    elif RANDOM in modify_options: ## TODO
                        print('TODO RANDOM')
                    
                    elif REGEX in modify_options: ## TODO
                        print('TODO REGEX')
                
                else: # Plain Text
                    insert_text = insert_text[list_index]
        
        elif type(insert_text) == tuple: # Dynamic Text
            
            if COUNT in modify_options or COUNT_TO in modify_options:
                
                dynamic_count = tracked_data[FILE_NAME_COUNT][0]
                dynamic_count_limit = tracked_data[FILE_NAME_COUNT_LIMIT][0]
                
                has_count_limit_hit = checkAllAvalibleCountLimits(tracked_data, 0, 1)
                
                if COUNT in modify_options:
                    insert_text = getDynamicText(insert_text, dynamic_count) if has_count_limit_hit > -1 else False
                
                elif COUNT_TO in modify_options:
                    insert_text = insert_text[STARTING_TEXT] if has_count_limit_hit > -1 else False
            
            elif RANDOM in modify_options: ## TODO
                print('TODO RANDOM')
            
            elif REGEX in modify_options: ## TODO
                print('TODO REGEX')
            
            else:
                print('/nYour using dynamic text "(text,1,text)" without using an OPTION informing how to handle it.')
                insert_text = False
        
        '''else: # Plain Text
            insert_text = modify_data'''
    
    else: # Plain Text
        insert_text = modify_data
    
    if EXTENSION in modify_options and edit_type != RENAME and type(insert_text) != bool:
        if insert_text != '' and insert_text.find('.') != 0 :
            insert_text = '.'+insert_text # Add a '.' if missing
    
    #print(insert_text)
    
    return insert_text


### Prepare the text to be inserted into file making and changes or text matches before renaming.
### If the same file name is returned then the original file did not match the criteria in the edit details.
###     (file_path) The full path to a file.
###     (edit_details) All the details on how to proceed with the file name edits.
###     --> Returns a [String] 
def insertTextIntoFileName(file_path, edit_details):
    
    rename_edit = True if edit_details[EDIT_TYPE] == RENAME else False
    search_data = getSearchData(edit_details[MATCH_TEXT], file_path, rename_edit)
    match_text_list = search_data[0]
    searchable_file_name = search_data[1]
    if type(match_text_list) != list:
        match_text_list = [match_text_list]
    
    search_options = getOptions(edit_details[MATCH_TEXT])
    modify_options = getOptions(edit_details[INSERT_TEXT])
    
    match_limit = getOptions(edit_details[MATCH_TEXT], MATCH_LIMIT, ALL)
    match_limit = ALL if match_limit <= NO_LIMIT else match_limit
    same_match_index = SAME_MATCH_INDEX in search_options
    tracked_data = edit_details[TRACKED_DATA]
    
    renamed_number = tracked_data[FILES_RENAMED][AMOUNT]
    renamed_limit = tracked_data[FILES_RENAMED][LIMIT]
    
    i = -1
    for match_text in match_text_list: # Loop breaks on first match found
        i += 1
        
        if same_match_index:
            #if len(match_text_list) != len(insert_text_list):
            if len(match_text_list) != renamed_limit:
                print('/nYour using the SAME_MATCH_INDEX option, but your MATCH_TEXT list is larger or smaller than your INSERT_TEXT list.')
                input('Did you mean to do this? Press "Enter" if so to continue...')
            match_index = i
        elif renamed_limit > 1:
            if REPEAT_TEXT_LIST in modify_options:
                renamed_number = resetIfMaxed(renamed_number, renamed_limit)
            match_index = renamed_number
        else:
            match_index = 0
        
        insert_text = getInsertText(edit_details, match_index)
        
        if type(insert_text) == bool or searchable_file_name.find(match_text) == -1:
            new_file_name = file_path.name
        else:
            match_size = len(match_text)
            new_file_name = file_path.name
            file_renamed = True
            
            index_matches = []
            index_match = 0
            start = 0
            end = None
            if match_size > 0:
                while index_match > -1:
                    index_match = searchable_file_name.rfind(match_text, start, end) # Reverse Find
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
            #print(index_matches)
            
            placement = getPlacement(edit_details[INSERT_TEXT])
            
            if edit_details[EDIT_TYPE] == ADD:
                
                if EXTENSION in modify_options:
                    if EXTENSION in search_options:
                        if match_text == searchable_file_name:
                            new_file_name = new_file_name + insert_text
                    else:
                        new_file_name = new_file_name + insert_text
                
                elif placement[1] == OF_MATCH:
                    
                    for index in index_matches:
                        
                        if placement[0] == START: # or LEFT
                            new_file_name = new_file_name[:index] + insert_text + new_file_name[index:]
                        
                        elif placement[0] == END: # or RIGHT
                            new_file_name = new_file_name[:index + match_size] + insert_text + new_file_name[index + match_size:]
                        
                        elif placement[0] == BOTH:
                            new_file_name = new_file_name[:index] + insert_text + new_file_name[index:index + match_size] + insert_text + new_file_name[index + match_size:]
                        
                        #elif placement[0] == EXTENSION:
                        #    new_file_name = f"{file_path.name}{insert_text}"
                        else:
                            file_renamed = False
                
                else: # placement[1] == OF_FILE_NAME:
                    new_file_name = addToFileName(file_path, insert_text, placement[0])
            
            elif edit_details[EDIT_TYPE] == REPLACE:
                
                ## TODO test? Replace extension only if...
                if EXTENSION in modify_options:
                    if EXTENSION in search_options:
                        if match_text == searchable_file_name:
                            new_file_name = file_path.stem + insert_text
                    else:
                        new_file_name = file_path.stem + insert_text
                
                else:
                    for index in index_matches:
                        new_file_name = new_file_name[:index] + insert_text + new_file_name[index + match_size:]
            
            elif edit_details[EDIT_TYPE] == RENAME:
                
                if match_size == 0 or searchable_file_name.find(match_text) > -1: ## TODO: this shouldn't even be needed, match already confirmed
                    
                    # Rename entire file name plus extension if...
                    if EXTENSION in modify_options and insert_text.find('.') > -1: ##TODO with EXTENSION, is it searching whole name? now it is test it
                        new_file_name = insert_text
                    else:
                        new_file_name = insert_text + file_path.suffix
            
            #if file_renamed: ## TODO: record all edits or just if the filename was renamed?
            #    edit_count += 1
            
            break # Match was found so break loop
    
    edit_details = updateTrackedData(edit_details, { CURRENT_LIST_INDEX : match_index, CURRENT_FILE_NAME : new_file_name })
    
    #print(new_file_name)
    
    return edit_details


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
    #elif placement == EXTENSION:
    #    new_file_name = f"{file_path.name}{add_text}"
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
###     --> Returns a [Dictionary] 
def renameFile(file_path, new_file_path, edit_details):
    renamed_number = edit_details[TRACKED_DATA][FILES_RENAMED]
    renamed_count = edit_details[TRACKED_DATA][FILE_NAME_COUNT][AMOUNT]
    renamed_count_limit = edit_details[TRACKED_DATA][FILE_NAME_COUNT_LIMIT]
    current_list_index = edit_details[TRACKED_DATA][CURRENT_LIST_INDEX]
    #current_file_name = edit_details[TRACKED_DATA][CURRENT_FILE_NAME]
    files_to_skip = edit_details[TRACKED_DATA][SKIPPED_FILES]
    
    does_file_exist = checkIfFileExist(new_file_path, file_path)
    
    if does_file_exist == CANCEL: # Will throw error, but will stop any further renaming.
        print('Canceling any further renaming and closing...')
        new_file_path = file_path.rename(new_file_path) # Error
    
    elif does_file_exist == NO: # Actually renaming file
        new_file_path = file_path.rename(new_file_path)
        edit_details = updateTrackedData(edit_details, { FILES_RENAMED : +1 })
        file_renamed = True
        #renamed_number += 1
    
    elif does_file_exist == CONTINUE: # Skip this count (+1) and try again (recursively).
        file_renamed = False
        #renamed_count += 1
        ## FILE_NAME_COUNT may be updated twice, fix later is so
        edit_details = updateTrackedData(edit_details, { FILE_NAME_COUNT : [current_list_index, +1], SKIPPED_FILES : new_file_path })
        
        edit_details = startingFileRenameProcedure(file_path, edit_details)
        
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
        #renamed_count += 1
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
    
    read_data = linked_file.read_text()
    
    # Check for all style of slashes in links
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
                text = 'Match Text             '
            elif key == INSERT_TEXT:
                text = 'Text To Insert         '
            elif key == RENAME_LIMIT:
                text = 'File Rename Limit      '
            elif key == LINKED_FILES:
                text = 'Files With Links       '
            elif key == SUB_DIRS:
                text = 'Include Sub Directories'
            elif key == PRESORT_FILES:
                text = 'Pre-Sort Files         '
            elif key == TRACKED_DATA:
                text = 'Data That Is Tracked   '
        
            '''if parent_key == PLACEMENT:
            if key == START:
                text = 'Start'
            elif key == END:
                text = 'End'
            elif key == BOTH_ENDS:
                text = 'Both Ends'
            if value == EXTENSION:
                text += ' of Extension'
            elif value == OF_FILE_NAME:
                text += ' of File Name'
            elif value == OF_MATCH:
                text += ' of Match'''
        
        elif parent_key == MATCH_TEXT or parent_key == INSERT_TEXT:
            if key == TEXT:
                text = 'TEXT : ' + str(value)
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
                    text += 'Limit Files To Rename, '
                if EXTENSION in value:
                    text += 'Allow Extension To Be Modified, '
                if RANDOM in value:
                    text += 'Add Random Numbers/Text, '
                if REGEX in value:
                    text += 'Regular Expressions, '
                if SAME_MATCH_INDEX in value:
                    text += 'Use Match Index While Selecting From Insert Text List, '
                if REPEAT_TEXT_LIST in value:
                    text += 'Once End of Text List Reached Repeat List, '
                for item in value:
                    if type(item) == tuple:
                        if MATCH_LIMIT in item:
                            text += 'Limit Matches to ' + str(item[1]) + ', '
                        if MINIMUM_DIGITS in item:
                            text += 'Minimum Digits ' + str(item[1]) + ', '
                text = text.rstrip(', ')
            
            if key == PLACEMENT:
                text = '\n                              PLACEMENT : '
                if START in value:
                    text += 'Start'
                elif END in value:
                    text += 'End'
                elif BOTH_ENDS in value:
                    text += 'Both Ends'
                '''if EXTENSION in value:
                    text += 'Extension'''
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
            if key == FILES_RENAMED:
                text = 'Files Renamed So Far : ' + str(value)
            if key == FILE_NAME_COUNT:
                text = '\n                              Current File Count Number : ' + str(value)
            if key == FILE_NAME_COUNT_LIMIT:
                text = '\n                              File Count Number Max : ' + str(value)
            if key == CURRENT_LIST_INDEX:
                text = '\n                              Current List Index : ' + str(value)
            if key == CURRENT_FILE_NAME:
                text = '\n                              Current File Name : ' + str(value)
            if key == SKIPPED_FILES:
                text = '\n                              Files To Skip : ' + str(value)
    
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
###     (files) A List of files, which can include directories pointing to many more files.
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
            input('\nContinue...')
        
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
                ## TODO: Rewrite...
                edit_details = [EDIT_TYPE, PLACEMENT, MATCH_TEXT, INSERT_TEXT, RECURSIVE, SEARCH_FROM]
                
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
                    
                    edit_details[INSERT_TEXT] = add_text
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
                    edit_details[INSERT_TEXT] = replace_text
                    edit_details[RECURSIVE] = recursive ## TODO fix this
                    edit_details[SEARCH_FROM] = search_from
        
        # Presort Files
        files_meta = sortFiles(files, edit_details.get(PRESORT_FILES,None))
        
        # Iterate over all dropped files including all files in dropped directories
        include_sub_dirs = -1
        for file in files_meta:
            file_path = file[FILE_PATH]
            
            if Path.is_dir(file_path):
                
                if include_sub_dirs == -1 and not use_preset: # Only answer once
                    include_sub_dirs = input('Search through sub-directories too? [ Y / N ]: ')
                    include_sub_dirs = yesTrue(include_sub_dirs)
                else:
                    include_sub_dirs = preset.get(SUB_DIRS, False)
                
                edit_details_copy = renameAllFilesInDirectory(file_path, edit_details, include_sub_dirs)
                
                files_renamed += edit_details_copy[TRACKED_DATA][FILES_RENAMED][AMOUNT]
            
            elif Path.is_file(file_path):
                #print('\n')
                edit_details_copy = startingFileRenameProcedure(file_path, edit_details)
                
                files_renamed += edit_details_copy[TRACKED_DATA][FILES_RENAMED][AMOUNT]
            
            else:
                print( os.path.isfile(file_path) )
                print("\nThis is not a normal file of directory (socket, FIFO, device file, etc.) and so this script won't be renameing it." )
    
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
    #sys.argv.append('V:\\Apps\\Scripts\\folder with spaces\\sub1')
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
    
