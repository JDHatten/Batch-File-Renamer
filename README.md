# Batch File Renamer by JDHatten

If you ever had a need to reorganize a large amount of files by renaming them this is the script to accomplish that task quickly.

This script will rename one or more files either by adding new text or replacing text in the file names.  Adding text can be placed at the start, end, or both sides of either matched text or the entire file name itself.  Replacing text will replace the first or all instances of matched text in a file name including the extension.  Renaming will just rename the entire file, but an iterating number or some other modify option must be used.

**Extra Features**:
- Update any text based files that that have links to the renamed files to prevent broken links in whatever apps that use the those files.
- Revert any file name changes by dropping the generated log file back into the script.
- Sort groups of files before renaming using file meta data.

<br>

## How To Use:
> Simply drag and drop one or more files or directories onto the script.<br>
> Create *custom presets* for more complex renaming methods.<br>

<br>

## Presets:

`EDIT_TYPE : ADD, REPLACE or RENAME` [*Required*]

> `ADD` simply adds new text to a file name.<br>
> `REPLACE` finds and replace text in a file name.<br>
> `RENAME` renames the entire file name.<br>


`MATCH_TEXT : "Text"`<br>
*-or-*<br>
`MATCH_TEXT : { TEXT : "Text", OPTIONS : ["Search Option 1",2,3,...] }`<br>

> `TEXT` is the text to search for and match before editing a file name. If a match is not made then that file name will not be changed.<br>

> `OPTIONS` are used to further customize search criteria. All current search options are listed below:<br>
>> `MATCH_CASE` means searches are case-sensitive. [*Default*]<br>
>> `NO_MATCH_CASE` is used for non-case-sensitive searches.<br>
>> `SEARCH_FROM_RIGHT` simply starts searching from right to left opposed from the default left to right.<br>
>> `MATCH_LIMIT` is used to find and replace a limited number of text matches per file name. The default is ( **MATCH_LIMIT**, **NO_LIMIT** ).<br>
>> `SAME_MATCH_INDEX` is used in combination with Lists of both **MATCH_TEXT** and **INSERT_TEXT**, i.e. ["Text", "Text",...]. When a match is made from the **MATCH_TEXT** List, the same index from the **INSERT_TEXT** List will be chosen. Useful when making a long lists of specific files to find and rename.<br>
>> `EXTENSION` if used in search options will only match the file extension and only an exact match.  For example, ‘.doc’ will match ‘.doc’ but will not match ‘.docx’.  Only use if you need this exact match use-case.


`IGNORE_TEXT : "Text"`<br>
*-or-*<br>
`IGNORE_TEXT : { TEXT : "Text", OPTIONS : ["Search Option 1",2,3,...] }`<br>

> `TEXT` to search for and if found in a file name skip that file renaming, effectively renaming every other file not matched.<br>

> `OPTIONS` are used to further customize search criteria. All current search options are listed below:<br>
>> `MATCH_CASE` means searches are case-sensitive. [*Default*]<br>
>> `NO_MATCH_CASE` is used for non-case-sensitive searches.<br>
>> `EXTENSION` if used in search options will only match the file extension and only an exact match.  For example, ‘.doc’ will match ‘.doc’ but will not match ‘.docx’.  Only use if you need this exact match use-case.


`INSERT_TEXT : "Text"` [*Required*]<br>
*-or-*<br>
`INSERT_TEXT : { TEXT : "Text", OPTIONS : ["Modify Options 1",2,3,...], PLACEMENT : (PLACE, OF_) }`<br>

> `TEXT` is the text to insert into file names.<br>

> `OPTIONS` are used to further modify text. All current modify options are listed below:<br>
>> `COUNT` is a way to dynamically add an iterating number to a file name. **TEXT : ( "Starting Text", ( Starting Number, Ending Number ), "Ending Text" )**. Note: The ending number is optional and count resets after each directory change.<br>
>> `COUNT_TO` is the max amount of renames to make before stopping and moving onto the next **TEXT** in a List or the next directory. Is similar to COUNT's ending number without adding an iterating number to a file name. **TEXT : ( ‘Text’, Number )**<br>
>> `MINIMUM_DIGITS` is the minimum number or digits used for any dynamic text. For example, **OPTIONS : ( MINIMUM_DIGITS, 3 )** will turn ‘7’ into ‘007’.<br>
>> `RANDOM` will generate random numbers or text that is added to file names. This feature is not yet added.<br>
>> `REPEAT_TEXT_LIST` will repeat a text list once the end of a text list is reached. The length of a text list is treated as a soft rename limit unless this option is used. **TEXT** must be dynamic if used, [**COUNT**, **RANDOM**, etc.].<br>
>> `EXTENSION` if used in modify options and **EDIT_TYPE : ADD or REPLACE** only the extension will be replaced or added on to the **END**. If used with **EDIT_TYPE : RENAME** the entire file name may be rewritten including the extension, but only if a "." is in **TEXT**. Note: You don't need to use **EXTENSION** in all cases where you wish to match or modify the extension.


> `PLACEMENT` when using **EDIT_TYPE : ADD** this signifies where to place text. For example, **( START, OF_FILE_NAME )**. All current placement options are listed below:<br>
>> `START` to place at the start of...<br>
>> `LEFT` to place at the left of...<br>
>> `END` to place at the end of... [*Default*]<br>
>> `RIGHT` to place at the right of...<br>
>> `BOTH` to place at both sides of...<br>
>> `BOTH_ENDS` to place at both ends of...<br>
>> `OF_FILE_NAME` to be placed at file name minus extension. [*Default*]<br>
>> `OF_MATCH` to be placed at one or more matches found.<br>


`SOFT_RENAME_LIMIT : 0 to NO_LIMIT`<br>

> Max number of file renames to make per directory or group of individual files dropped. Default: NO_LIMIT<br>


`HARD_RENAME_LIMIT : 0 to NO_LIMIT`<br>

> Hard limit on how many files to rename each time script is ran, no mater how many directories or group of individual files dropped. Default: NO_LIMIT<br>


`LINKED_FILES : ["://File//Path",...]`<br>

> Files that need to be updated of any file name changes to prevent broken links in apps. *Make sure to use double slashes "//".*<br>


`INCLUDE_SUB_DIRS : True or False`<br>

> If a directory is used or dropped choose whether or not to search through sub-directories. Default: False<br>


`PRESORT_FILES : { "Sort Option" : ASCENDING or DESCENDING }`<br>

> Sort before renaming files. Default: None<br>All current sort options are listed below:<br>

>> `ASCENDING` sort in order of 0-9, A-Z [*Default*]<br>
>> `DESCENDING` sort in order of 9-0, Z-A<br>
>> `ALPHABETICALLY` sort file names in alphabetical order. [*Default*]<br>
>> `FILE_SIZE` sort by file size in bytes.<br>
>> `DATE_ACCESSED` sort by date file last opened.<br>
>> `DATE_MODIFIED` sort by date file last changed.<br>
>> `DATE_CREATED` sort by date file created. (*Windows Only*)<br>
>> `DATE_META_MODIFIED` sort by file meta data last updated. (*UNIX*)<br>


**Dynamic Text Format**<br>
> `Tuple`("Starting Text", Integer/Tuple, "Ending Text")<br>
> `List`["Text1", "Text2", ...]<br>
> Tuples can go inside of Lists. [ "Text", ("Text-[", (1,10), "]") ]

<br>

### Example Presets:
```
preset13 = {
  EDIT_TYPE        : REPLACE,
  MATCH_TEXT       : { TEXT    : " (U)",
                       OPTIONS : [ (MATCH_LIMIT, 1), SEARCH_FROM_RIGHT ] },
  INSERT_TEXT      : { TEXT    : "" },
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
  EDIT_TYPE    : ADD,
  MATCH_TEXT   : { TEXT      : [ ".jpg", ".png" ],
                   OPTIONS   : [ NO_MATCH_CASE, EXTENSION, SAME_MATCH_INDEX ] },
  INSERT_TEXT  : { TEXT      : [ ("-", (1,200), ""), ("-", (1001,2200), "") ],
                   OPTIONS   : [ COUNT, (MINIMUM_DIGITS, 4) ],
                   PLACEMENT : ( END, OF_FILE_NAME ) }
}
```

This preset searches for image files with the extension ".jpg" or ".png" ignoring case.  Depending on whether a match is ".jpg" or ".png" add an incrementing number starting a 0001 or 1000 respectively to the end of the file name.

**Example File Renames:**
- "image_file.jpg" will change to "image_file-0001.jpg"<br>
- "image_file.png" will change to "image_file-1001.png"<br>
