from github import Github, Repository
import base64
import yaml
import re

def normalize(string):
    lines = string.strip().split('\n')
    if 'skills' in lines[0]:
        return '\n'.join([re.sub('^(#)?  ', '\g<1>', line) for line in lines[1:]])
    return string.strip()

g = Github()
repos = []
repos = [repo for repo in g.get_user("opsdroid").get_repos() if repo.name.startswith('skill-')]

skills = []
for repo in repos:
    readme_base64 = repo.get_readme().content
    readme = base64.b64decode(readme_base64).decode("utf-8")
    config = re.search('#[#\s]+Configuration((.|\n)*)```(yaml)?\n((.|\n)*)\n```', readme, re.MULTILINE)
    if config:
        skills.append((
            repo.name[6:].replace('-', ' ').capitalize(),
            repo.html_url,
            normalize(config.group(4))
        ))
    else:
        skills.append((
            repo.name[6:].replace('-', ' ').capitalize(),
            repo.html_url,
            '- name: ' + repo.name[6:]
        ))

commented_skills = []
uncommented_skills = []
before = ''
after = ''
with open("./opsdroid/configuration/example_configuration.yaml") as f:
    parse = False
    parsed = False
    for line in f:
        if parse:
            if line.startswith('#'):
                name = re.search('.*- name:(.*)(#|$)', line)
                if name:
                    commented_skills.append(name.group(1).strip())
            elif line.startswith(' '):
                name = re.search('.*- name:(.*)(#|$)', line)
                if name:
                    uncommented_skills.append(name.group(1).strip())
            elif line == '\n':
                continue
            else:
                parse = False
                parsed = True
                after += line
        elif not parsed:
            before += line 
        else:
            after += line

        if line.startswith('skills'):
            parse = True

skill_set = ''
commented_skill_set = ''

for skill in skills:
    name = re.search('((.|\n)*)- name:(.*)(#|$)', skill[2], re.MULTILINE)
    if name:
        if name.group(3).strip() in uncommented_skills:
            skill_set += '\n\n  ## {} ({})'.format(skill[0], skill[1])
            for line in skill[2].split('\n'):
                skill_set += '\n  ' + line
        else:
            commented_skill_set += '\n#\n#  ## {} ({})'.format(skill[0], skill[1])
            for line in skill[2].split('\n'):
                commented_skill_set += '\n#  ' + line


text = before + skill_set + '\n\n  # Configurations for other skills uncomment desired skill to activate it.' + commented_skill_set + after
with open("./opsdroid/configuration/example_configuration.yaml", 'w') as f:
    f.write(text)