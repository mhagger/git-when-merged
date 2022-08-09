# `git when-merged`

`git when-merged` helps you figure out when and why a commit was merged into a branch.

If you use standard Git workflows, then you create a feature branch for each feature that you are working on. When the feature is complete, you merge it into your `master` branch. You might even have sub-feature branches that are merged into a feature branch before the latter is merged.

In such a workflow, the first-parent history of `master` consists mainly of merges of feature branches into the mainline. `git when-merged` can be used to ask, "When (and why) was commit C merged into the current branch?" The simplest way to use it is

```ShellSession
$ git when-merged 87c248f
refs/heads/master                      50f577451448a407ee8e78ed62aa09d209c91652
```

This command looks along the first-parent history of the current branch to find the merge commit that first brought commit `87c248f` into the branch's history. The guilty merge commit in this case is `50f5774`. Add the `-l` option to see the log for that merge, which will hopefully explain what feature was being merged and by whom:

```ShellSession
$ git when-merged -l 87c248f
refs/heads/master                      50f577451448a407ee8e78ed62aa09d209c91652
commit 50f577451448a407ee8e78ed62aa09d209c91652 (github/master, master)
Merge: f79a45d 87c248f
Author: Michael Haggerty <mhagger@alum.mit.edu>
Date:   Mon Jul 11 07:55:19 2016 +0200

    Merge pull request #9 from mhagger/recursive-option

    Add a `--recursive`/`-r` option
```

There are many more options; see below.


## Installation

**_Note: If you are using 2.6 <= Python <= 3.6, you MUST use Option 3 or 4._**

<details open>
<summary><h3>Option 1: Install as a stand-alone command line tool.</h3></summary>
<br>

> pipx is a tool to help you install and run end-user applications written in Python.

1. [Install `pipx`](https://pipxproject.github.io/pipx/installation/):

   ``` sh
   python3 -m pip install --user pipx
   ```

   - Tip: [Homebrew](https://formulae.brew.sh/formula/pipx) as well as newer versions of some Linux distributions (e.g. [Debian 10](https://packages.debian.org/buster/pipx), [Ubuntu 19.04](https://packages.ubuntu.com/disco/pipx), etc.) offer native packages for `pipx`.

   <br>

   ``` sh
   python3 -m pipx ensurepath
   ```

   - Note: You may need to restart your terminal for the `$PATH` updates to take effect.

2. Use `pipx` to install [`git-when-merged` from PyPI](https://pypi.org/project/git-when-merged/):

   ``` sh
   pipx install git-when-merged
   ```

3. Test the installation:

   ``` sh
   git-when-merged --help
   ```

- Use `pipx` to uninstall at any time:

   ``` sh
   pipx uninstall git-when-merged
   ```

See Python's [Installing stand alone command line tools](https://packaging.python.org/guides/installing-stand-alone-command-line-tools/) guide for more information.
</details>

<details>
<summary><h3>Option 2: Create an ephemeral installation.</h3></summary>
<br>

> Python "Virtual Environments" allow Python packages to be installed in an isolated location for a particular application, rather than being installed globally.

1. Use the built-in [`venv`](https://docs.python.org/3/library/venv.html) module to create a virtual environment:

   ``` sh
   python3 -m venv ./venv-gwm
   ```

2. Use `pip` to install [`git-when-merged` from PyPI](https://pypi.org/project/git-when-merged/) into the virtual environment:

   ``` sh
   venv-gwm/bin/pip install git-when-merged
   ```

3. Test the installation:

   ``` sh
   venv-gwm/bin/git-when-merged --help
   ```

   - Tip: Some users find it more convenient to "activate" the virtual environment (which prepends the virtual environment's `bin/` to `$PATH`):

      ``` sh
      source venv-gwm/bin/activate
      git-when-merged --help
      deactivate
      ```

- Remove the virtual environment to uninstall at any time:

   ``` sh
   rm --recursive venv-gwm/
   ```

See Python's [Installing Packages](https://packaging.python.org/tutorials/installing-packages/) tutorial for more information.
</details>

<details>
<summary><h3>Option 3: Clone and add to <code>$PATH</code>.</h3></summary>
<br>

1. Clone the repo somewhere on your system.

2. Ensure that `<somewhere>/bin/git-when-merged` is executable.

3. Put the contents of `<somewhere>/bin` on your `$PATH`.

That's it!
</details>

<details>
<summary><h3>Option 4 (MacOS Users): Install from Homebrew.</h3></summary>
<br>

```ShellSession
$ brew update
$ brew install git-when-merged
```
</details>

## Usage

    git when-merged [OPTIONS] COMMIT [BRANCH...]

Find the merge commit that brought `COMMIT` into the specified `BRANCH`(es). Specifically, look for the oldest commit on the first-parent history of each `BRANCH` that contains the `COMMIT` as an ancestor.

```
positional arguments:
  commit                The commit whose destiny you would like to determine.
  branch                The destination branch(es) into which <commit> might
                        have been merged. (Actually, BRANCH can be an
                        arbitrary commit, specified in any way that is
                        understood by git-rev-parse(1).) If neither <branch>
                        nor --pattern/-p nor --default/-s is specified, then
                        HEAD is used.

optional arguments:
  -h, --help            show this help message and exit
  --pattern PATTERN, -p PATTERN
                        Show when COMMIT was merged to the references matching
                        the specified regexp. If the regexp has parentheses
                        for grouping, then display in the output the part of
                        the reference name matching the first group.
  --name NAME, -n NAME  Show when COMMIT was merged to the references matching
                        the configured pattern(s) with the given name (see
                        whenmerged.<name>.pattern below under CONFIGURATION).
  --default, -s         Shorthand for "--name=default".
  --recursive, -r       Follow merges back recursively.
  --show-commit, -c     Display only the SHA-1 of the merge commit. Exit with
                        a nonzero exit code if the commit was not merged via a
                        merge commit.
  --show-branch, -b     Display the range of commits that were merged at the
                        same time as the specified commit. Exit with a nonzero
                        exit code if the commit was not merged via a merge
                        commit. This option also affects the behavior of --log
                        and --visualize.
  --abbrev N            Abbreviate commit SHA-1s to the specified number of
                        characters (or more if needed to avoid ambiguity). See
                        also whenmerged.abbrev below under CONFIGURATION.
  --no-abbrev           Do not abbreviate commit SHA-1s.
  --describe            Describe the merge commit in terms of the most recent
                        tag reachable from the commit (see git-describe(1))
  --describe-contains   Describe the merge commit in terms of a nearby tag
                        that contains it (see git-describe(1))
  --log, -l             Show the log for the merge commit. When used with
                        "--show-branch/-b", show the log for all of the
                        commits that were merged at the same time as the
                        specified commit.
  --diff, -d            Show the diff for the merge commit.
  --visualize, -v       Visualize the merge commit using gitk. When used with
                        "--show-branch/-b", only show the branch(es) that were
                        merged at the same time as the specified commit.

Examples:
  git when-merged 0a1b                   # Find the merge commit that brought
                                         # commit 0a1b into the current branch
  git when-merged 0a1b v1.10 v1.11       # Find merge into given tags/branches
  git when-merged 0a1b -p feature-[0-9]+ # Specify tags/branches by regex
  git when-merged 0a1b -n releases       # Use whenmerged.releases.pattern
  git when-merged 0a1b -s                # Use whenmerged.default.pattern

  git when-merged -r 0a1b                # If the commit was merged indirectly,
                                         # show each intermediate merge.
  git when-merged -l 0a1b                # Show the log for the merge commit
  git when-merged -lb 0a1b               # Show log for the whole merged branch
  git when-merged -v 0a1b                # Visualize the merge commit in gitk
  git when-merged -vb 0a1b               # Visualize the whole merged branch
  git when-merged -d 0a1b                # Show the diff for the merge commit
  git when-merged -c 0a1b                # Print only the merge's SHA-1

Configuration:
  whenmerged.<name>.pattern
      Regular expressions that match reference names for the pattern
      called <name>.  A regexp is sought in the full reference name,
      in the form "refs/heads/master".  This option can be multivalued, in
      which case references matching any of the patterns are considered.
      Typically the pattern will be chosen to match master and/or significant
      release branches or tags, or perhaps their remote-tracking equivalents.
      For example,

          git config whenmerged.default.pattern '^refs/heads/master$'
          git config --add whenmerged.default.pattern '^refs/heads/maint$'

      or

          git config whenmerged.releases.pattern '^refs/tags/release-'

  whenmerged.abbrev
      If this value is set to a positive integer, then Git SHA-1s are
      abbreviated to this number of characters (or longer if needed to
      avoid ambiguity).  This value can be overridden using --abbrev=N
      or --no-abbrev.
```

`git when-merged` is originally based on [the suggestion here](http://stackoverflow.com/questions/8475448/find-merge-commit-which-include-a-specific-commit).

