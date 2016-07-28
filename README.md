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

* Clone the repo somewhere on your system.
* Ensure that `<somewhere>/bin/git-when-merged` is executable.
* Put the contents of `<somewhere>/bin` on your `$PATH`.

That's it!

Or, using Homebrew:

```ShellSession
$ brew update
$ brew install git-when-merged
```


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
  --log, -l             Show the log for the merge commit. When used with
                        "--show-branch/-b", show the log for all of the
                        commits that were merged at the same time as the
                        specified commit.
  --diff, -d            Show the diff for the merge commit.
  --visualize, -v       Visualize the merge commit using gitk. When used with
                        "--show-branch/-b", only show the branch(es) that were
                        merged at the same time as the specified commit.

Examples:
  git when-merged 0a1b                     # Find merge into current branch
  git when-merged 0a1b feature-1 feature-2 # Find merge into given branches
  git when-merged 0a1b -p feature-[0-9]+   # Specify branches by regex
  git when-merged 0a1b -n releases         # Use whenmerged.releases.pattern
  git when-merged 0a1b -s                  # Use whenmerged.default.pattern

  git when-merged 0a1b -r feature-1        # If merged indirectly, show all
                                           # merges involved.

  git when-merged 0a1b -l feature-1        # Show log for the merge commit
  git when-merged 0a1b -d feature-1        # Show diff for the merge commit
  git when-merged 0a1b -v feature-1        # Display merge commit in gitk

Configuration:
  whenmerged.<name>.pattern
      Regular expressions that match reference names for the pattern
      called <name>.  A regexp is sought in the full reference name,
      in the form "refs/heads/master".  This option can be
      multivalued, in which case references matching any of the
      patterns are considered.  Typically you will use pattern(s) that
      match master and/or significant release branches, or perhaps
      their remote-tracking equivalents.  For example,

          git config whenmerged.default.pattern \
                  '^refs/heads/master$'

      or

          git config whenmerged.releases.pattern \
                  '^refs/remotes/origin/release\-\d+\.\d+$'

  whenmerged.abbrev
      If this value is set to a positive integer, then Git SHA-1s are
      abbreviated to this number of characters (or longer if needed to
      avoid ambiguity).  This value can be overridden using --abbrev=N
      or --no-abbrev.
```

`git when-merged` is originally based on [the suggestion here](http://stackoverflow.com/questions/8475448/find-merge-commit-which-include-a-specific-commit).

