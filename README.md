# Batch File Renamer by JDHatten

If you ever had a need to reorganize a large amount of files by renaming them this is the script to accomplish that task quickly.

This script will rename one or more files either by adding new text or replacing text in the file names.  Adding text can be placed at the start, end, or both sides of either matched text or the entire file name itself.  Replacing text will replace the first or all instances of matched text in a file name including the extension.  Renaming will just rename the entire file, but an iterating number or some other modify option should be used.

**Extra Features**:
- Update any text based files that that have links to the renamed files to prevent broken links in whatever apps that use the those files.
- Revert any file name changes by dropping the generated log file back into the script.
- Sort groups of files before renaming using file meta data.
- Insert file meta data into file names.

<br>

## How To Use:
- To Rename Files: Simply drag and drop one or more files or directories onto the script. Create your own custom presets for more complex renaming tasks.<br>
- To Revert File Renames: Drag and drop one or more of the generated log files back into the script.<br>
- To Update Links Only: Drag and drop a file fitting the criteria below.<br>

> File Name (Exactly): `'x:\same\path\as\this\script\find-replace-links.txt'`<br>
> File Contents (Example):<br>
>> `find = ['x:\path\to\old\file\link.jpg', ...]`<br>
>> `replace = ['x:\path\to\new\file\link-01.jpg', ...]`<br>
>> `links = ['x:\path\to\file\with\links.xml', ...]`<br>
Note: Use either single or double quotes (stick with one set of quotes) and there is no need to escape characters (double slashes not necessary)

<br>

## Requirements:
> Matching and inserting meta data from files requires the ffmpeg-python and filetype packages. Also in order to read and write a larger variety of linked files, chardet is required to detect file encodings. These are optional features.
- https://github.com/kkroening/ffmpeg-python
- https://github.com/h2non/filetype.py
- https://github.com/chardet/chardet
- *Install Via Pip*:
```
pip install ffmpeg-python
```
```
pip install filetype
```
```
pip install chardet
```

<br>

## Presets:

`EDIT_TYPE : ADD, REPLACE or RENAME` [*Required*]

> `ADD` simply adds new text to a file name.<br>
> `REPLACE` finds and replace text in a file name.<br>
> `RENAME` renames the entire file name.

<br>

`MATCH_FILE_NAME : "Text"`<br>
*-or-*<br>
`MATCH_FILE_NAME : { TEXT : "Text", OPTIONS : ["Search Option 1",2,3,...] }`<br>

> `TEXT` is the text to search for and match before editing a file name. If a match is not made then that file name will not be changed.<br>

> `OPTIONS` are used to further customize search criteria. All current search options are listed below:<br>
>> `MATCH_CASE` means searches are case-sensitive. [*Default*]<br>
>> `NO_MATCH_CASE` is used for non-case-sensitive searches.<br>
>> `FULL_MATCH` is used when a complete or perfect full match is needed of a file name.<br>
>> `SEARCH_FROM_RIGHT` simply starts searching from right to left opposed from the default left to right.<br>
>> `MATCH_LIMIT` is used to find and replace a limited number of text matches per file name. The default is ( **MATCH_LIMIT**, **NO_LIMIT** ).<br>
>> `SAME_MATCH_INDEX` is used in combination with the **INSERT_FILE_NAME** List, i.e. ["Text", "Text",...]. When a match is made from the **MATCH_FILE_NAME** List, the same index from the **INSERT_FILE_NAME** List will be chosen. Useful when making a long lists of specific files to find and rename.<br>
>> `MATCH_ALL_INDEXES` is used to match all text in a list, else any match will do. Note: SAME_MATCH_INDEX takes precedent.<br>
>> `REGEX` will allow the use of regular expression to search text. Use raw (r) strings, example: r'[R]\s*[E]'<br>
>> `REGEX_GROUP` is an option to be used together with REGEX to make sure the matched (groups) are sourced from "this" matched list. [*Default*] Example Regex: r'(group1)(group2)'  -->  r'\1\2'. Note: Group text will be taken from the last match made. Use MATCH_LIMIT and/or SEARCH_FROM_RIGHT to select which match to use.<br>
>> `EXTENSION` if used in search options will only match the file extension and only an exact match.  For example, ‘.doc’ will match ‘.doc’ but will not match ‘.docx’.  Only use if you need this exact match use-case.

<br>

`IGNORE_FILE_NAME : "Text"`<br>
*-or-*<br>
`IGNORE_FILE_NAME : { TEXT : "Text", OPTIONS : ["Search Option 1",2,3,...] }`<br>

> `TEXT` to search for and if found in a file name skip that file renaming, effectively renaming every other file not matched.<br>

> `OPTIONS` are used to further customize search criteria. All current search options are listed below:<br>
>> `MATCH_CASE` means searches are case-sensitive. [*Default*]<br>
>> `NO_MATCH_CASE` is used for non-case-sensitive searches.<br>
>> `FULL_MATCH` is used when a complete or perfect full match is needed of a file name.<br>
>> `MATCH_ALL_IGNORE_INDEXES` is used to match all text in ignore list in order to skip a rename.<br>
>> `REGEX` will allow the use of regular expression to search text. Use raw (r) strings, example: r'[R]\s*[E]'<br>
>> `EXTENSION` if used in search options will only match the file extension and only an exact match.  For example, ‘.doc’ will match ‘.doc’ but will not match ‘.docx’.  Only use if you need this exact match use-case.

<br>

`MATCH_FILE_CONTENTS : "Text"`<br>
*-or-*<br>
`MATCH_FILE_CONTENTS : { TEXT : "Text", OPTIONS : ["Search Option 1",2,3,...] }`<br>

> `TEXT` is the text in a file's contents to search for and match before editing a file name. If a match is not made then that file name will not be changed. Note: Only text files can be opened and searched. Other files will be ignored.<br>

> `OPTIONS` are used to further customize search criteria. All current search options are listed below:<br>
>> `MATCH_CASE` means searches are case-sensitive. [*Default*]<br>
>> `NO_MATCH_CASE` is used for non-case-sensitive searches.<br>
>> `SEARCH_FROM_RIGHT` simply starts searching from right to left opposed from the default left to right.<br>
>> `MATCH_LIMIT` is used to find and replace a limited number of text matches per file name. The default is ( **MATCH_LIMIT**, **NO_LIMIT** ).<br>
>> `SAME_MATCH_INDEX` is used in combination with the **INSERT_FILE_NAME** List, i.e. ["Text", "Text",...]. When a match is made from the **MATCH_FILE_CONTENTS** List, the same index from the **INSERT_FILE_NAME** List will be chosen. Useful when making a long lists of specific files to find and rename.<br>
>> `MATCH_ALL_INDEXES` is used to match all text in a list, else any match will do. Note: SAME_MATCH_INDEX takes precedent.<br>
>> `REGEX` will allow the use of regular expression to search text. Use raw (r) strings, example: r'[R]\s*[E]'<br>
>> `REGEX_GROUP` is an option to be used together with REGEX to make sure the matched groups are sourced from "this" matched list. Example Regex: r'(group1)(group2)'  -->  r'\1\2'. Note: Group text will be taken from the last match made. Use MATCH_LIMIT and/or SEARCH_FROM_RIGHT to select which match to use.<br>

<br>

`MATCH_FILE_META : A FILE_META_TYPE or 'Text' to match a FILE_META_MIME`<br>
*-or-*<br>
`MATCH_FILE_META : { META : [ { 'Specific Meta' : 'How To Match', 'What To Match' : 'Data', ... }, {}, ... ], OPTIONS : ["Search Option 1",2,3,...] }`<br>

> `META` is the file meta data to search for and match before editing a file name. If a match is not made then that file name will not be changed.<br>
>> `TYPE_APPLICATION`, `TYPE_AUDIO`, `TYPE_FONT`, `TYPE_IMAGE`, `TYPE_MESSAGE`, `TYPE_MODEL`, `TYPE_MULTIPART`, `TYPE_TEXT`, `TYPE_VIDEO TYPE_ARCHIVE`, `TYPE_DOCUMENT`<br>
>> `FILE_META_SIZE`, `FILE_META_ACCESSED`, `FILE_META_MODIFIED`, `FILE_META_CREATED`(*Windows Only*), `FILE_META_METADATA`(*UNIX*), `FILE_META_TYPE`, `FILE_META_MIME`, `FILE_META_FORMAT`, `FILE_META_FORMAT_LONG`, `FILE_META_HEIGHT`, `FILE_META_WIDTH`, `FILE_META_LENGTH`, `FILE_META_BIT_DEPTH`, `FILE_META_VIDEO_BITRATE`, `FILE_META_VIDEO_FRAME_RATE`, `FILE_META_AUDIO_BITRATE`, `FILE_META_AUDIO_SAMPLE_RATE`, `FILE_META_AUDIO_CHANNELS`, `FILE_META_AUDIO_CHANNEL_LAYOUT`, `FILE_META_AUDIO_TITLE`, `FILE_META_AUDIO_ALBUM`, `FILE_META_AUDIO_ARTIST`, `FILE_META_AUDIO_YEAR`, `FILE_META_AUDIO_GENRE`, `FILE_META_AUDIO_PUBLISHER`, `FILE_META_AUDIO_TRACK`<br>
>> `EXACT_MATCH`, `LOOSE_MATCH`, `SKIP_EXACT_MATCH`, `SKIP_LOOSE_MATCH` `LESS_THAN`, `MORE_THAN`, `BEFORE`, `AFTER`, `WITHIN_THE_PAST`, `OLDER_THAN`<br>
>> `YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE` `SECOND`, `MILLISECOND`, `MICROSECOND`, `TIMESTAMP`, `BYTES`, `KB`, `MB`, `GB`, `IN_BYTES_ONLY`<br>

> `OPTIONS` are used to further customize search criteria. All current search options are listed below:<br>
>> `MATCH_CASE` means searches are case-sensitive. [*Default*]<br>
>> `NO_MATCH_CASE` is used for non-case-sensitive searches.<br>
>> `SAME_MATCH_INDEX` is used in combination with the **INSERT_FILE_NAME** List, i.e. ["Text", "Text",...]. When a match is made from the **MATCH_FILE_META** List, the same index from the **INSERT_FILE_NAME** List will be chosen.

<br>

`INSERT_TEXT : "Text"` [*Required*]<br>
*-or-*<br>
`INSERT_FILE_NAME : { TEXT : "Text", OPTIONS : ["Modify Options 1",2,3,...], PLACEMENT : (PLACE, OF_) }`<br>

> `TEXT` is the text to insert into file names.<br>

> `OPTIONS` are used to further modify text. All current modify options are listed below:<br>
>> `COUNT` is a way to dynamically add an iterating number to a file name. **TEXT : ( "Starting Text", ( Starting Number, Ending Number ), "Ending Text" )**. Note: The ending number is optional and count resets after each directory change.<br>
>> `COUNT_TO` is the max amount of renames to make before stopping and moving onto the next **TEXT** in a List or the next directory. Is similar to COUNT's ending number without adding an iterating number to a file name. **TEXT : ( ‘Text’, Number )**<br>
>> `MINIMUM_DIGITS` is the minimum number or digits used for any dynamic text. For example, **OPTIONS : ( MINIMUM_DIGITS, 3 )** will turn ‘7’ into ‘007’.<br>
>> `RANDOM_NUMBERS` will generate random numbers that are added to file names. Note: All random generators can be used together.<br>
>> `RANDOM_LETTERS` will generate random letters that are added to file names.<br>
>> `RANDOM_SPECIALS` will generate random special characters that are added to file names.<br>
>> `RANDOM_OTHER` will generate random other (uncommon, unique, or foreign) characters that are added to file names.<br>
>> `RANDOM_SEED` is the starting seed number to use in random generators. Default: (RANDOM_SEED, None)<br>
>> `REPEAT_TEXT_LIST` will repeat a text list once the end of a text list is reached. The length of a text list is treated as a soft rename limit unless this option is used. **TEXT** must be dynamic if used, [**COUNT**, **RANDOM**, etc.].<br>
>> `EXTENSION` if used in modify options and **EDIT_TYPE : ADD or REPLACE** only the extension will be replaced or added on to the **END**. If used with **EDIT_TYPE : RENAME** the entire file name may be rewritten including the extension, but only if a "." is in **TEXT**. Note: You don't need to use **EXTENSION** in all cases where you wish to match or modify the extension.<br>
>> `INSERT_META_DATA` will retrieve specific meta data from a file and add it to the file name.  ('Text', *File Meta Data*, 'Text', *File Meta Data*, 'Text', ...)<br>
>> `NO_ADD_DUPES` will avoid adding duplicate text in the same **PLACEMENT** (only when using ADD).<br>
>> `REGEX` will allow the use of regular expression to insert matched groups into text. See REGEX_GROUP above.<br>
>> `CUSTOM` is when you need to write/code your own unique custom file renaming procedure. Search script for: **def getCustomText**<br>

> `PLACEMENT` when using **EDIT_TYPE : ADD** this signifies where to place text. For example, **( START, OF_FILE_NAME )**. All current placement options are listed below:<br>
>> `START` to place at the start of...<br>
>> `LEFT` to place at the left of...<br>
>> `END` to place at the end of... [*Default*]<br>
>> `RIGHT` to place at the right of...<br>
>> `BOTH` to place at both sides of...<br>
>> `BOTH_ENDS` to place at both ends of...<br>
>> `OF_FILE_NAME` to be placed at file name minus extension. [*Default*]<br>
>> `OF_MATCH` to be placed at one or more matches found.

<br>

`SOFT_RENAME_LIMIT : 0 to NO_LIMIT`<br>

> Max number of file renames to make per directory or group of individual files dropped. Default: NO_LIMIT

<br>

`HARD_RENAME_LIMIT : 0 to NO_LIMIT`<br>

> Hard limit on how many files to rename each time script is ran, no mater how many directories or group of individual files dropped. Default: NO_LIMIT

<br>

`LINKED_FILES : ["://File//Path",...]`<br>

> Files that need to be updated of any file name changes to prevent broken links in apps. *Make sure to use double slashes "//".*

<br>

`IDENTICAL_FILE_NAMES : "Paths"`<br>
*-or-*<br>
`IDENTICAL_FILE_NAMES : { LINKS : "Paths", OPTIONS : ["Search Option 1",2,3,...] }`<br>

> `LINKS` are the paths to directories to find identical file names (to those already renamed) and rename them as well.<br>

> `OPTIONS` are used to further customize search criteria. All current search options are listed below:<br>
>> `MATCH_CASE` means searches are case-sensitive. [*Default*]<br>
>> `NO_MATCH_CASE` is used for non-case-sensitive searches.<br>
>> `SEARCH_SUB_DIRS` is used to search sub directories within the provided directory paths.<br>
>> `EXTENSION` will include file name + extension when comparing file names, else only the file name will be matched.

<br>

`INCLUDE_SUB_DIRS : True or False`<br>

> If a directory is used or dropped choose whether or not to search through sub-directories. Default: False

<br>

`PRESORT_FILES : { "File Meta Data" : ASCENDING or DESCENDING }`<br>

> Sort before renaming files using the file's meta data. Default: None<br>All current sort options are listed below:<br>

>> `ASCENDING` sort in order of 0-9, A-Z [*Default*]<br>
>> `DESCENDING` sort in order of 9-0, Z-A<br>
>> `ALPHABETICALLY` or `FILE_NAME` sort file names in alphabetical order. [*Default*]<br>
>> `FILE_META_SIZE`, `FILE_META_ACCESSED`, `FILE_META_MODIFIED`, `FILE_META_CREATED`(*Windows Only*), `FILE_META_METADATA`(*UNIX*), `FILE_META_TYPE`, `FILE_META_MIME`, `FILE_META_FORMAT`, `FILE_META_FORMAT_LONG`, `FILE_META_HEIGHT`, `FILE_META_WIDTH`, `FILE_META_LENGTH`, `FILE_META_BIT_DEPTH`, `FILE_META_VIDEO_BITRATE`, `FILE_META_VIDEO_FRAME_RATE`, `FILE_META_AUDIO_BITRATE`, `FILE_META_AUDIO_SAMPLE_RATE`, `FILE_META_AUDIO_CHANNELS`, `FILE_META_AUDIO_CHANNEL_LAYOUT`, `FILE_META_AUDIO_TITLE`, `FILE_META_AUDIO_ALBUM`, `FILE_META_AUDIO_ARTIST`, `FILE_META_AUDIO_YEAR`, `FILE_META_AUDIO_GENRE`, `FILE_META_AUDIO_PUBLISHER`, `FILE_META_AUDIO_TRACK`

<br>

**Dynamic Text Format**<br>
> *Tuple*: ("Starting Text", Integer/Tuple, "Ending Text")<br>
> *List*:  ["Text1", "Text2", ...]<br>
> Tuples can go inside of Lists. [ "Text", ("Text-[", (1,10), "]") ]

<br>

### Example Presets:
```
preset13 = {
  EDIT_TYPE        : REPLACE,
  MATCH_FILE_NAME  : { TEXT    : " (U)",
                       OPTIONS : [ (MATCH_LIMIT, 1), SEARCH_FROM_RIGHT ] },
  INSERT_FILE_NAME : { TEXT    : "" },
  LINKED_FILES     : [ "X:\\Path\\To\\File_With_Links.xml" ],
  INCLUDE_SUB_DIRS : True
}
```
This preset searches for file names with a " (U)" and match the first one found starting from the right.  Then replace that single match with an empty string, which effectively removes the " (U)" from the file name.  Afterwards if a file was successfully renamed then attempt to find any links in the provided XML file and update them.  Lastly, if a directory is being searched also search any sub-directories.

**Example File Renames:**
- "some file (U).bin" will change to "some file.bin"<br>
- "file (U) (U).doc" will change to "file (U).doc "<br>

<br>

```
preset19 = {
  EDIT_TYPE        : ADD,
  MATCH_FILE_NAME  : { TEXT      : [ ".jpg", ".png" ],
                       OPTIONS   : [ NO_MATCH_CASE, EXTENSION, SAME_MATCH_INDEX ] },
  INSERT_FILE_NAME : { TEXT      : [ ("-", (1,200), ""), ("-", (1001,2200), "") ],
                       OPTIONS   : [ COUNT, (MINIMUM_DIGITS, 4) ],
                       PLACEMENT : ( END, OF_FILE_NAME ) }
}
```

This preset searches for image files with the extension ".jpg" or ".png" ignoring case.  Depending on whether a match is ".jpg" or ".png" add an incrementing number starting a 0001 or 1000 respectively to the end of the file name.

**Example File Renames:**
- "image_file.jpg" will change to "image_file-0001.jpg"<br>
- "image_file.png" will change to "image_file-1001.png"<br>

<br>

```
preset23 = {
  EDIT_TYPE        : RENAME,
  IGNORE_FILE_NAME : { TEXT     : [ 'skip' ],
                       OPTIONS  : [ NO_MATCH_CASE ] },
  INSERT_FILE_NAME : { TEXT     : [ ('RandomS-(', 4, ')'), ('RandomL-[', (7), ']') ],
                       OPTIONS  : [ RANDOM_NUMBERS, RANDOM_LETTERS, (RANDOM_SEED, 167), REPEAT_TEXT_LIST ] }
}
```

This preset searches for all files except those that have the string "skip" in their file name. Then rename those files alternating between RandomS-(####) and RandomL-[#######] because of the REPEAT_TEXT_LIST option. The #’s could be any number or letter. The random seed chosen means the random #’s will always start and continue with the same pattern every time a new rename task is ran including directory and file group changes.

**Example File Renames:**
- "a_file.pdf" will change to "RandomS-(1py7).pdf"<br>
- "skip_file.doc" will not be renamed.<br>
- "some_file.txt" will change to "RandomL-[jjc124z].txt"<br>
