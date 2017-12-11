from github import Github, Repository
from argparse import ArgumentParser
import jinja2
import base64
import yaml
import re
import os


def normalize(string):
    lines = string.strip().split('\n')
    if 'skills' in lines[0]:
        return '\n'.join([
            re.sub('^(#)?  ', '\g<1>', line)
            for line in lines[1:]
        ])
    return string.strip()


def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def get_repos():
    return [
        repo
        for repo in g.get_user("opsdroid").get_repos()
        if repo.name.startswith('skill-')
    ]


def get_readme(repo):
    readme_base64 = repo.get_readme().content
    return base64.b64decode(readme_base64).decode("utf-8")


def get_skill(repo, readme):
    config = re.search(
        '#[#\s]+Configuration((.|\n)*?)```(yaml)?\n((.|\n)*?)\n```',
        readme,
        re.MULTILINE
    )

    skill_raw_name = repo.name[6:]
    skill_name = skill_raw_name.replace('-', ' ').capitalize()
    skill_url = repo.html_url

    if config:
        skill_config = normalize(config.group(4))
    else:
        skill_config = '- name: ' + skill_raw_name

    return {
        'raw_name': skill_raw_name,
        'name': skill_name,
        'url': skill_url,
        'config': skill_config
    }


def check_skill(repo, skill, error_strict):
    try:
        yaml.load(skill['config'])
    except yaml.scanner.ScannerError as e:
        if error_strict:
            raise(e)
        print(
            "[WARNING] processing {0} raised an exception\n"
            "{2}\n{1}\n{2}".format(repo.name, e, '='*40)
        )


def get_skills(g, active_skills, error_strict=False):
    repos = get_repos()

    skills = {'commented_skills': [], 'uncommented_skills': []}

    for repo in repos:
        readme = get_readme(repo)
        skill = get_skill(repo, readme)
        check_skill(repo, skill, error_strict)

        if skill['raw_name'] in active_skills:
            skills['uncommented_skills'].append(skill)
        else:
            skills['commented_skills'].append(skill)

    return skills


def check_config(config, error_strict):
    try:
        yaml.load(config)
    except yaml.scanner.ScannerError as e:
        if error_strict:
            raise(e)
        print(
            "[WARNING] processing resulting config raised an exception"
            "\n{1}\n{0}\n{1}".format(e, '='*40)
        )


def update_config(g, active_skills, config_path, error_strict=False):
    skills = get_skills(g, active_skills, error_strict)
    text = render('scripts/configuration.j2', skills)
    check_config(text, error_strict)

    with open(config_path, 'w') as f:
        f.write(text)


if __name__ == '__main__':
    parser = ArgumentParser(description='Config creator ')
    parser.add_argument('output', nargs='?', help='Path to config to update')
    parser.add_argument('-t', '--token', nargs='?', help='GitHub Token')
    parser.add_argument('-a', '--active-skills',
                        nargs='?', help='List of skills to be activated')

    parser.set_defaults(error_strict=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--strict', dest='error_strict', action='store_true',
        help='Sets fail strategy to strict mode. Fails on any error.'
    )
    group.add_argument(
        '--warn', dest='error_strict', action='store_false',
        help='Sets fail strategy to warn mode (default).'
        ' Any errors are shown as warnings.'
    )

    args = parser.parse_args()

    g = Github(args.token)

    if args.active_skills:
        active_skills = args.active_skills.split(',')
    else:
        active_skills = ['dance', 'hello', 'seen', 'loudnoises']

    if not args.output:
        base_path = '/'.join(os.path.realpath(__file__).split('/')[:-2])
        config_path = base_path
        config_path += '/opsdroid/configuration/example_configuration.yaml'
    else:
        config_path = args.output

    update_config(g, active_skills, config_path, args.error_strict)
