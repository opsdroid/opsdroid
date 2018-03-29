from github import Github
from argparse import ArgumentParser
import jinja2
import base64
import yaml
import re
import os


def normalize(string):
    """Normalize text to yaml format standards."""
    lines = string.strip().split('\n')
    if 'skills' in lines[0] or \
            'connectors' in lines[0] or \
            'databases' in lines[0] or \
            'parsers' in lines[0]:
        return '\n'.join([
            re.sub('^(#)?  ', '\g<1>', line)
            for line in lines[1:]
        ])
    return string.strip()


def render(tpl_path, context):
    """Returns the template for configuration.yaml file."""
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def get_repos():
    """Get repository details for: skills, connectors, database."""
    return [
        repo
        for repo in g.get_user("opsdroid").get_repos()
        if repo.name.startswith('skill-') or
        repo.name.startswith('connector-') or
        repo.name.startswith('database-')
    ]


def get_readme(repo):
    """Get readme.md details from repository."""
    readme_base64 = repo.get_readme().content
    return base64.b64decode(readme_base64).decode("utf-8")


def get_config_details(readme):
    """Gets all the configuration details located in the readme.md file,
    under the title "Configuration".

    Note: Regex divided by multiline in order to pass lint.
    """
    config = re.search(
        '#[#\s]+(?:Configuring|Configuration)((.|\n)*?)'
        '```(yaml)?\n((.|\n)*?)\n```',
        readme,
        re.MULTILINE
    )
    return config


def get_config_params(repo, readme):
    """Returns parameters to be used in the update."""
    if repo.name[:5] == "skill":
        raw_name = repo.name[6:]
        repo_type = "skill"
    elif repo.name[:9] == "connector":
        raw_name = repo.name[10:]
        repo_type = "connector"
    else:
        raw_name = repo.name[9:]
        repo_type = "database"

    name = raw_name.replace('-', ' ').capitalize()
    url = repo.html_url
    config = get_config_details(readme)

    if config:
        config_text = normalize(config.group(4))
    else:
        config_text = '- name: ' + raw_name

    return {
        'repo_type': repo_type,
        'raw_name': raw_name,
        'name': name,
        'url': url,
        'config': config_text
    }


def get_parsers_details():
    """Reads parser documentation and gets configuration from it."""
    base_url = 'http://opsdroid.readthedocs.io/en/stable/matchers/'
    parsers_path = '/'.join(
        os.path.realpath(__file__).split('/')[:-3]) + '/docs/matchers/'

    parsers = []

    for file in os.listdir(parsers_path):
        name = file[:-3]
        with open(parsers_path + file) as f:
            readme = f.read()
            try:
                config = get_config_details(readme).group(4)

                parsers.append({
                    'raw_name': name,
                    'name': name.capitalize(),
                    'url': base_url + name,
                    'config': normalize(config)
                })
            except AttributeError:
                # Doesn't contain config options - it's always activated
                pass

    return parsers


def validate_yaml_format(mapping, error_strict):
    """Scans the configuration format and validates yaml formatting."""
    try:
        yaml.load(mapping['config'])
    except (KeyError, TypeError):
        yaml.load(mapping)
    except yaml.scanner.ScannerError as e:
        if error_strict:
            raise e
        print(
            "[WARNING] processing {0} raised an exception\n"
            "{1}\n{0}\n{1}".format(e, '='*40)
        )


def triage_modules(g, active_modules, error_strict=False):
    """Allocate modules to their type and active/inactive status."""
    repos = get_repos()

    skills = {'commented': [], 'uncommented': []}
    connectors = {'commented': [], 'uncommented': []}
    databases = {'commented': [], 'uncommented': []}
    parsers = get_parsers_details()

    modules = {'skills': skills, 'connectors': connectors,
               'databases': databases, 'parsers': parsers}

    for repo in repos:
        readme = get_readme(repo)
        params = get_config_params(repo, readme)
        validate_yaml_format(params, error_strict)

        if params['repo_type'] == 'skill':
            if params['raw_name'] in active_modules:
                skills['uncommented'].append(params)
            skills['commented'].append(params)

        elif params['repo_type'] == 'connector':
            if params['raw_name'] in active_modules:
                connectors['uncommented'].append(params)
            connectors['commented'].append(params)
        else:
            if params['raw_name'] == active_modules:
                databases['uncommented'].append(params)
            databases['commented'].append(params)

    return modules


def update_config(g, active_modules, config_path, error_strict=False):
    """Update the example_configuration.yaml file with all the modules."""
    _modules = triage_modules(g, active_modules, error_strict)
    modules = render('scripts/update_example_config/configuration.j2',
                     _modules)
    validate_yaml_format(modules, error_strict)

    with open(config_path, 'w') as f:
        f.write(modules)


if __name__ == '__main__':
    parser = ArgumentParser(description='Config creator ')
    parser.add_argument('output', nargs='?', help='Path to config to update')
    parser.add_argument('-t', '--token', nargs='?', help='GitHub Token')
    parser.add_argument('-a', '--active-modules',
                        nargs='?', help='List of modules to be activated')

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

    print("Updating the file: 'example_configuration.yaml' "
          "this may take a while...")

    active_modules = []

    if args.active_modules:
        active_modules.append((args.active_skills.split(',')))
    else:
        active_modules = ['dance', 'hello', 'seen', 'loudnoises',
                          'websocket', 'shell']
    if not args.output:
        base_path = '/'.join(os.path.realpath(__file__).split('/')[:-3])
        config_path = base_path
        config_path += '/opsdroid/configuration/example_configuration.yaml'
    else:
        config_path = args.output

    update_config(g, active_modules, config_path, args.error_strict)
