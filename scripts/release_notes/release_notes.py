import subprocess


def git_update_tags():
    """Update git tags from upstream master."""
    print("Updating tags.")
    print("=" * 20)
    process = subprocess.Popen(
        ["git", "pull", "upstream", "master", "--tags"],
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for output in process.communicate():
        if output != "":
            for line in output.splitlines():
                print(line.strip().decode("ascii"))
    process.wait()
    print()


def get_last_tag():
    """Get latest tag form git history."""
    print("Getting latest tag.")
    print("=" * 20)
    process = subprocess.Popen(
        ["git", "describe", "--tags", "--abbrev=0"],
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for output in process.communicate():
        if output != "":
            for line in output.splitlines():
                tag = line.strip().decode("ascii")
    process.wait()
    print("Latest version is {}.\n".format(tag))
    return tag


def git_log(tag):
    """Get the git log since the last tag."""
    print("Generating changelog since {}.".format(tag))
    print("=" * 20)
    process = ["git", "log", "{}..HEAD".format(tag), "--oneline"]
    process = subprocess.Popen(
        process, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    changelog = []
    for output in process.communicate():
        if output != "":
            for line in output.splitlines():
                changelog.append(line.strip().decode("ascii"))
    process.wait()
    return changelog


def output(changelog):
    """Format the changelog and print it."""
    changelog = [" ".join(line.split(" ")[1:]).strip() for line in changelog]
    for line in changelog:
        print(line)


def main():
    # Update git tags
    git_update_tags()
    tag = get_last_tag()

    # Run git log
    changelog = git_log(tag)

    # Format output
    output(changelog)


if __name__ == "__main__":
    main()
