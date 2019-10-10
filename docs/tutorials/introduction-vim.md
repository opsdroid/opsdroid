# Introduction to Vi/Vim
Vi/Vim is a command line text editor that comes with every platform other than windows (unless you install it). It can be hard to figure out how to do things in this editor because the editor is command-centric, this tutorial is meant to give you the basic knowledge of vi/vim and how to do things with it.


## Vi/Vim Modes
Vi/Vim comes with three different modes:
- Normal Mode (Default mode)
- Insert Mode (Press _i_ key)
- Visual Mode (Press _v_ key)

These modes are quite easy to understand and you can see which mode you are in on the bottom left corner of the terminal window. 

The normal mode is the default mode and the one activated as soon as you open Vi/Vim, you can move around, read the text, copy, insert lines, etc. The only thing you can't do in this mode is editing the text.

#### Editing text
If you want to edit the text you can just press the _i_ key on your keyboard you can notice that the bottom left corner of the window now shows the text: --INSERT--. 

You will now be able to use your terminal as a text editor, you can add, edit and delete text like you would do in any other text editor. 

Once you are happy with the changes that you have just made, press the _esc_ key on your keyboard and you will be back to the Normal mode.

### Visual Mode

There is nothing much to say about this mode. It allows you to select big chunks of text in order for you to copy or cut. When this mode is active you can read the text: --VISUAL-- in the bottom left corner of the window.

Another thing you can do in the visual mode is to highlight text and then make small changes to the highlighted text such as changing to uppercase or indenting lines.

For example, let's highlight a block of text starting with v and then moving the cursor.
We now delete it with the d command.
The v command selects text by character. The CTRL-V command selects text as a block. The V command selects line.

## Vi/Vim Commands
Vi/Vim is meant to help you do things fairly quickly without the need for a mouse. Everything can be done with a keyboard, so learning some of the Vi/Vim commands will be helpful.

Things that you will learn:
- how to save a file
- how to quit Vi/Vim
- how to move around
- how to see line numbers

_Note: Vi/Vim has a lot of different commands and combinations, this is just an introduction and you should read other sources if you want to learn how to use Vi/Vim properly._

#### Saving and quitting Vi/Vim
Now that you know how to edit text in Vi/Vim, the most important thing you will learn will be how to save your changes and quit. If you press the _:_ key of your keyboard, you will be able to enter commands to Vi/Vim.

To save a file all you need to do is type `:w` and then press enter.

To quit a file and go back to the command line you need to type `:q`. 

Note that if you made changes to the file and didn't save them, Vi/Vim won't automatically exit, instead, it will tell you to run the command `:q!` which basically translates to force quit.

These two commands can be combined into one `:wq`. This will write the changes to the file and then quit Vi/Vim.

#### Line numbers

Showing line numbers can be very useful when editing a file. Vi/Vim allows you to jump straight into a line if you know its number, so your editing can be done quicker if you know exactly where and what to edit.

To show line numbers you need to run the command `:set number`, once you press enter, you can see that Vi/Vim will show the number of each line.

If you want to jump straight to a line you can type the command `:<line number>` and the cursor will jump to the beginning of that line.

#### Moving around

To move around all you need is pressing a few keys to do different things. Moving around doesn't require you to enter the command mode by pressing the `:` key.

- `h` or `arrow left` - move the cursor one character to the left
- `l` or `arrow right` - move the cursor one character to the right
- `j` or `arrow down` - move the cursor one line down
- `k` or `arrow up` - move the cursor one line up
- `0` - move the cursor to the beginning of the line
- `$` - move the cursor to the end of the line
- `w` - move the cursor one word forward
- `b` - move the cursor one word back
- `gg` - move to the beginning of the file (line 1)
- `G` - move to the end of the line (last line)

These two commands can be used while moving/editing the file:

- `o` - adds an empty line below the cursor, moves the cursor to that line, enters edit mode
- `O` - adds an empty line above the cursor, moves the cursor to that line, enters edit mode


## Conclusion

This concludes the introduction to Vi/Vim, hopefully, you found it useful. There is a lot of things that you still need to learn but this should give you the basics to work around in this text editor.

If you would like to know more about Vi/Vim, you can run the Vim tutor by running this command on your terminal:

`$ Vimtutor`

This will open a text file with step-by-step instructions that cover all the basic commands in Vi/Vim.

You can also read this post - [Vi/Vim 101: A Beginner's Guide to Vi/Vim](https://www.linux.com/learn/Vi/Vim-101-beginners-guide-Vi/Vim) on Linux website.
