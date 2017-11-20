from github import Github, Repository
from argparse import ArgumentParser
import base64
import yaml
import re
import os

def normalize(string):
    lines = string.strip().split('\n')
    if 'skills' in lines[0]:
        return '\n'.join([re.sub('^(#)?  ', '\g<1>', line) for line in lines[1:]])
    return string.strip()

def get_skills(error_strict=False):
    g = Github()
    repos = []
    repos = [repo for repo in g.get_user("opsdroid").get_repos() if repo.name.startswith('skill-')]

    skills = []
    for repo in repos:
        readme_base64 = repo.get_readme().content
        readme = base64.b64decode(readme_base64).decode("utf-8")
        config = re.search('#[#\s]+Configuration((.|\n)*)```(yaml)?\n((.|\n)*)\n```', readme, re.MULTILINE)
        if config:
            skill = (
                repo.name[6:].replace('-', ' ').capitalize(),
                repo.html_url,
                normalize(config.group(4))
            )
        else:
            skill = (
                repo.name[6:].replace('-', ' ').capitalize(),
                repo.html_url,
                '- name: ' + repo.name[6:]
            )
        try:
            yaml.load(skill[2])
        except yaml.scanner.ScannerError:
            if not error_strict:
                pass

        skills.append(skill)
    return skills

def parse_config(config_path):
    commented_skills = []
    uncommented_skills = []
    before = ''
    after = ''

    with open(config_path) as f:
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
    return(before, after, uncommented_skills, commented_skills)

def prepare_skill(skills, uncommented_skills, commented_skills):
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
    return skill_set + '\n\n  # Configurations for other skills uncomment desired skill to activate it.' + commented_skill_set


def update_config(config_path, error_strict=False):
    (before, after, uncommented_skills, commented_skills) = parse_config(config_path)
    skills = get_skills()
    skills_text = prepare_skill(skills, uncommented_skills, commented_skills)
    text = before + skills_text + after
    yaml.load(text)
    with open(config_path, 'w') as f:
        f.write(text)

if __name__ == '__main__':
    parser = ArgumentParser(description='Config creator ')
    parser.add_argument('config_path', nargs='?', help='Path to config to update')
    parser.set_defaults(set_defaults=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--strict', dest='error_strict', action='store_true', help='Sets fail strategy to strict mode. Fails on any error.')
    group.add_argument('--warn', dest='error_strict', action='store_false', help='Sets fail strategy to warn mode (default). Any errors are shown as warnings.')
    args = parser.parse_args()

    if not args.config_path:
        base_path = '/'.join(os.path.realpath(__file__).split('/')[:-2])
        config_path = base_path + '/opsdroid/configuration/example_configuration.yaml'
    else:
        config_path = args.config_path
    
    update_config(config_path, args.error_strict)