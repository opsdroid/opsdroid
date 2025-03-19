# Opsdroid Contact Manager Skill
The Contact Management Skill is a tool for managing **contacts** in a database. 
It allows users to add, update, retrieve, and delete contact information using natural language commands.

This example will use [SQLite3](https://www.sqlite.org/index.html) to provide you a basic example about how sqlite data base can be used.

## Building the Skill

Create a folder for your Contacts skill project. Choose a location and name it contact-manager.

```bash
mkdir /path/to/contact-manager
``` 
Inside the folder, we will create the `__init__.py` file and we will start working on our contact-manager skill.

### Configuration

Now, let's open `configuration.yaml` file that opsdroid created and add our contact-manager skill to the skills section.

```yaml
skills:
  contactmanager:
    path: /path/to/my/contact-manager
```

### Imports and Classes Needed

Now that our skill has been configured in the `configuration.yaml` file, we will continue by creating the `__init__.py` file inside of our contact-manager folder and start working on the skill!

The first thing we need to do is to import the `Skill` class and the `regex_matcher` from opsdroid. Then we will need to import `sqlite3` modules. Your `__init__.py` file should look like this:

```python
import sqlite3

from opsdroid.matchers import match_regex
from opsdroid.skill import Skill
```

### Connecting to SQLite3 
You will create a python file with your database. After compiling it ```python mydatabase.py```, the ```mydatabase.db``` will be created.

Our next step is to connect our `__init__.py` file to a SQLite database. Your `__init__.py` file should look something like this now:

```python
import sqlite3

from opsdroid.matchers import match_regex
from opsdroid.skill import Skill

conn = sqlite3.connect('/path/to/my/database')
c = conn.cursor()
```

#### Creating the Table

We now have to use the SQLite3 database file that we had connected and add a table to it by doing 

```python
import sqlite3

# Connect to SQLite database (creates the database file if it doesn't exist)
connection = sqlite3.connect('sqllite.db')

# Create a cursor object to execute SQL commands
cursor = connection.cursor()

# Create a table
cursor.execute('''CREATE TABLE IF NOT EXISTS contacts (
                    phoneNumber TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    surname TEXT NOT NULL,
                    email TEXT
                )''')


# Commit the transaction
connection.commit()


# Close cursor and connection
cursor.close()
connection.close()
```

With our table and database file we are set for the next section!

#### Adding to the contact database

Now we will be making a function which will be responsible for inserting the contact's data into the database. We will get the info from the database with `c.execute("SELECT * FROM contacts WHERE phoneNumber = ?", (phoneNumber,)")` and we will inserting it with `c.execute("INSERT INTO contacts VALUES (?)", (params,))`, params will equal contact's phone number, name, surname and email. Here is what it should look like:

```python
class Contact(Skill):

    @match_regex(r"Add contact: (\d+), (.+), (.+), (\S+@\S+)") #phoneNumber, name, surname, email
    async def addContact(self, message):
        phoneNumber = message.regex.group(1)  # Extract the phoneNumber
        name = message.regex.group(2) 
        surname = message.regex.group(3) 
        email =  message.regex.group(4) 
        c.execute("SELECT * FROM contacts WHERE phoneNumber = ?", (phoneNumber,))
        existing_contact = c.fetchone()
        if existing_contact:
            await message.respond(f"Contact already exists!")
        else:
            c.execute("INSERT INTO contacts (phoneNumber, name, surname, email) VALUES (?, ?, ?, ?)", (phoneNumber, name, surname, email))
            conn.commit()
            await message.respond(f"Contact with Phone Number {phoneNumber} added to the Contact Book!")
```
**We prevent duplicating one contact into the database by executing this:**

```python
    c.execute("SELECT * FROM contacts WHERE phoneNumber = ?", (phoneNumber,)) 
    existing_contact = c.fetchone()
```
### Getting The Data

This part involves listing the contacts that have been added to the database. We will be doing this by getting the data from the database the same as how we did for the adding to the database which is `c.execute("SELECT * FROM contacts")`. With the data we can use a for loop to go through all the things in the database. It should look something like this:

```python
    @match_regex(r"Show contacts")     
    async def showContacts(self, message):
        c.execute("SELECT * FROM contacts")
        rows = c.fetchall()
        if len(rows) == 0:
            await message.respond('No Contacts added, Please Use Command "Add contact: PhoneNumber, Name, Surname, Email"')
        else: 
            for row in rows:
                phoneNumber, name, surname, email = row
                await message.respond(f'Phone Number: {phoneNumber}, Name: {name}, Surname: {surname} and Email: {email}')
```

However we have a problem, if the user asks to `Show Contacts` without anything in the database it will return an error. We can fix this by checking if the len of rows in the database is equal to 0: `if len(rows) == 0:`.

### Update The Data
This fuction is responsible for updating the name, surname or email is given for a contact with a specific Phone Number.

```python
    @match_regex(r"Update contact for (\d+): (.+), (.+), (\S+@\S+)") # for PhoneNumber: Name, Surname, Email
    async def updateContact(self, message):
        phoneNumber = message.regex.group(1)  # Extract the phoneNumber
        name = message.regex.group(2) 
        surname = message.regex.group(3) 
        email = message.regex.group(4) 
        c.execute("UPDATE contacts SET name=?, surname=?, email=? WHERE phoneNumber = ?", (name, surname, email, phoneNumber))
        conn.commit()
        await message.respond(f'Contact {phoneNumber} updated successfully!')
```

#### Delete The Data
Deleting the data involves removing a contact's phone number along with their name, surname, and email.
```python
    @match_regex(r"Delete contact for (.+)") #PhoneNumber
    async def deleteContact(self, message):
        phoneNumber = message.regex.group(1) 
        c.execute("DELETE FROM contacts WHERE phoneNumber = ?", (phoneNumber,))
        conn.commit()
        await message.respond(f'Contact {phoneNumber} deleted successfully!')
```

**Now you can have a contact book, all in one, in Opsdroid. Congratulations! Good luck with your opsdroid journey! Here is what the final code should look like:**

```python
import sqlite3

from opsdroid.matchers import match_regex
from opsdroid.skill import Skill

conn = sqlite3.connect('sqlite.db')
c = conn.cursor()

class Contact(Skill):
    
    @match_regex(r"Add contact: (\d+), (.+), (.+), (\S+@\S+)") #phoneNumber, name, surname, email
    async def addContact(self, message):
        phoneNumber = message.regex.group(1)  # Extract the phoneNumber
        name = message.regex.group(2) 
        surname = message.regex.group(3) 
        email =  message.regex.group(4) 
        c.execute("SELECT * FROM contacts WHERE phoneNumber = ?", (phoneNumber,))
        existing_contact = c.fetchone()
        if existing_contact:
            await message.respond(f"Contact already exists!")
        else:
            c.execute("INSERT INTO contacts (phoneNumber, name, surname, email) VALUES (?, ?, ?, ?)", (phoneNumber, name, surname, email))
            conn.commit()
            await message.respond(f"Contact with Phone Number {phoneNumber} added to the Contact Book!")

    @match_regex(r"Show contacts")     
    async def showContacts(self, message):
        c.execute("SELECT * FROM contacts")
        rows = c.fetchall()
        if len(rows) == 0:
            await message.respond('No Contacts added, Please Use Command "Add contact: PhoneNumber, Name, Surname, Email"')
        else: 
            for row in rows:
                phoneNumber, name, surname, email = row
                await message.respond(f'Phone Number: {phoneNumber}, Name: {name}, Surname: {surname} and Email: {email}')

    @match_regex(r"Update contact for (\d+): (.+), (.+), (\S+@\S+)") # for PhoneNumber: Name, Surname, Email
    async def updateContact(self, message):
        phoneNumber = message.regex.group(1)  # Extract the phoneNumber
        name = message.regex.group(2) 
        surname = message.regex.group(3) 
        email = message.regex.group(4) 
        c.execute("UPDATE contacts SET name=?, surname=?, email=? WHERE phoneNumber = ?", (name, surname, email, phoneNumber))
        conn.commit()
        await message.respond(f'Contact {phoneNumber} updated successfully!')

    @match_regex(r"Delete contact for (.+)") #PhoneNumber
    async def deleteContact(self, message):
        phoneNumber = message.regex.group(1) 
        c.execute("DELETE FROM contacts WHERE phoneNumber = ?", (phoneNumber,))
        conn.commit()
        await message.respond(f'Contact {phoneNumber} deleted successfully!')

```


