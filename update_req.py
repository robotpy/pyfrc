import sys
import git


def main():
    repo_name = sys.argv[1]  # Ex. robotpy/robotpy-wpilib
    repo_path = "https://github.com/" + repo_name + ".git"
    package_name = sys.argv[2]  # Ex. wpilib

    print("Repository Name:", repo_name)
    print("Repository Path:", repo_path)
    print("Package Name:", package_name)

    tag = git.Repo.clone_from(repo_path, "./temp", branch="master").git.describe(
        "--tags", "--abbrev=0"
    )

    lower_bound = tag

    print("Latest Version:", lower_bound)

    version = tag.split(".")

    for i in range(len(version)):
        if i == 0:
            version[i] = str(int(version[i]) + 1)
        else:
            version[i] = "0"

    upper_bound = ".".join(version)

    print("Next Major Version:", upper_bound)

    file_data = None
    with open("requirements.txt", "r") as file:
        file_data = file.readlines()

    line_idx = None

    for i in range(len(file_data)):
        if file_data[i].find(package_name + ">=") == 0:
            line_idx = i

    if line_idx is not None:
        print("Package found in requirements.txt")

        if getCurrentVersion(file_data[line_idx]) == lower_bound:
            print(
                "Package is already at the latest version (based on git tags). It was not updated."
            )
            exit(1)

        file_data[line_idx] = "{}>={},<{}\n".format(
            package_name, lower_bound, upper_bound
        )
    else:
        print("Package not found in requirements.txt")
        exit(1)

    print("Rewriting Requirements")
    with open("requirements.txt", "w") as file:
        file.writelines(file_data)
    print("Done")

    exit(0)


def getCurrentVersion(line: str):
    stripped_line = line.strip("\r\n\t ")  # remove newlines, tabs and spaces

    v_start = stripped_line.find(">=") + 2
    v_end = stripped_line.find(",")
    if v_end == -1:
        v_end = len(stripped_line)

    v = stripped_line[v_start:v_end].strip(
        "\r\n\t "
    )  # remove newlines, tabs and spaces
    return v


if __name__ == "__main__":
    main()
