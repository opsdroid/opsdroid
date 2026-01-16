from opsdroid.skill import Skill
from opsdroid.matchers import match_event
from opsdroid.events import OpsdroidStarted
import random
import string

class PasswordGeneratorSkill(Skill):
    @match_event(OpsdroidStarted)
    async def run_on_start(self, event):
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(chars) for i in range(12))
        
        print("\n" + "="*40)
        print(f"  SUCCESS! OPSDROID IS WORKING!")
        print(f"  YOUR PASSWORD: {password}")
        print("="*40 + "\n")
