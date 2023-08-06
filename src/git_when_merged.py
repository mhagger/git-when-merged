#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

# Copyright (c) 2013 Michael Haggerty
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>

# Run "git when-merged --help for the documentation.
# See https://github.com/mhagger/git-when-merged for the project.

"""Find when a commit was merged into one or more branches.

Find the merge commit that brought COMMIT into the specified
BRANCH(es). Specifically, look for the oldest commit on the
first-parent history of each BRANCH that contains the COMMIT as an
ancestor.

"""

USAGE = r"""git when-merged [OPTIONS] COMMIT [BRANCH...]
"""

EPILOG = r"""
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

Originally based on:
  http://stackoverflow.com/questions/8475448/find-merge-commit-which-include-a-specific-commit
"""

import sys
import re
import subprocess
import argparse


if not (0x02060000 <= sys.hexversion):
    sys.exit('Python version 2.6 or later is required')


# Backwards compatibility:
try:
    from subprocess import CalledProcessError
except ImportError:
    # Use definition from Python 2.7 subprocess module:
    class CalledProcessError(Exception):
        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output
        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (self.cmd, self.returncode)

try:
    from subprocess import check_output
except ImportError:
    # Use definition from Python 2.7 subprocess module:
    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            try:
                raise CalledProcessError(retcode, cmd, output=output)
            except TypeError:
                # Python 2.6's CalledProcessError has no 'output' kw
                raise CalledProcessError(retcode, cmd)
        return output


class Failure(Exception):
    pass


def _decode_output(value):
    """Decodes Git output into a unicode string.

    On Python 2 this is a no-op; on Python 3 we decode the string as
    suggested by [1] since we know that Git treats paths as just a sequence
    of bytes and all of the output we ask Git for is expected to be a file
    system path.

    [1] http://docs.python.org/3/c-api/unicode.html#file-system-encoding

    """
    if sys.hexversion < 0x3000000:
        return value
    return value.decode(sys.getfilesystemencoding(), 'surrogateescape')


def check_git_output(*popenargs, **kwargs):
    return _decode_output(check_output(*popenargs, **kwargs))


def read_refpatterns(name):
    key = 'whenmerged.%s.pattern' % (name,)
    try:
        out = check_git_output(['git', 'config', '--get-all', '--null', key])
    except CalledProcessError:
        raise Failure('There is no configuration setting for %r!' % (key,))
    retval = []
    for value in out.split('\0'):
        if value:
            try:
                retval.append(re.compile(value))
            except re.error as e:
                sys.stderr.write(
                    'Error compiling branch pattern %r; ignoring: %s\n'
                    % (value, e,)
                    )
    return retval


def iter_commit_refs():
    """Iterate over the names of references that refer to commits.

    (This includes references that refer to annotated tags that refer
    to commits.)"""

    process = subprocess.Popen(
        [
            'git', 'for-each-ref',
            '--format=%(refname) %(objecttype) %(*objecttype)',
            ],
        stdout=subprocess.PIPE,
        )
    for line in process.stdout:
        words = _decode_output(line).strip().split()
        refname = words.pop(0)
        if words == ['commit'] or words == ['tag', 'commit']:
            yield refname

    retcode = process.wait()
    if retcode:
        raise Failure('git for-each-ref failed')


def matches_any(refname, refpatterns):
    return any(
        refpattern.search(refname)
        for refpattern in refpatterns
        )


def rev_parse(arg, abbrev=None):
    if abbrev:
        cmd = ['git', 'rev-parse', '--verify', '-q', '--short=%d' % (abbrev,), arg]
    else:
        cmd = ['git', 'rev-parse', '--verify', '-q', arg]

    try:
        return check_git_output(cmd).strip()
    except CalledProcessError:
        raise Failure('%r is not a valid commit!' % (arg,))


def describe(arg, contains=False):
    cmd = ['git', 'describe']
    if contains:
        cmd += ['--contains']
    cmd += [arg]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    retcode = process.poll()
    if retcode:
        return None
    else:
        return _decode_output(out).strip()


def rev_list(*args):
    """Iterate over (commit, [parent,...]) for the selected commits.

    args are passed as arguments to "git rev-list" to select which
    commits should be iterated over.

    """

    process = subprocess.Popen(
        ['git', 'rev-list'] + list(args) + ['--'],
        stdout=subprocess.PIPE,
        )
    for line in process.stdout:
        yield _decode_output(line).strip()

    retcode = process.wait()
    if retcode:
        raise Failure('git rev-list %s failed' % (' '.join(args),))


def rev_list_with_parents(*args):
    cmd = ['git', 'log', '--format=%H %P'] + list(args) + ['--']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for line in process.stdout:
        words = _decode_output(line).strip().split()
        yield (words[0], words[1:])

    retcode = process.wait()
    if retcode:
        raise Failure('command "%s" failed' % (' '.join(cmd),))


class CommitGraph:
    def __init__(self, *args):
        self.commits = dict(rev_list_with_parents(*args))

    def __contains__(self, commit):
        return commit in self.commits

    def __getitem__(self, commit):
        return self.commits[commit]

    def first_parent_path(self, commit):
        """Iterate over the commits in the first-parent ancestry of commit.

        Iterate over the commits that are within this CommitGraph that
        are also in the first-parent ancestry of the specified commit.
        commit must be a full 40-character SHA-1.

        """

        while True:
            try:
                parents = self[commit]
            except KeyError:
                return
            yield commit
            if not parents:
                return
            commit = parents[0]


class MergeNotFoundError(Exception):
    def __init__(self, refname):
        self.refname = refname


class InvalidCommitError(MergeNotFoundError):
    msg = 'Is not a valid commit!'


class DoesNotContainCommitError(MergeNotFoundError):
    msg = 'Does not contain commit.'


class DirectlyOnBranchError(MergeNotFoundError):
    msg = 'Commit is directly on this branch.'


class MergedViaMultipleParentsError(MergeNotFoundError):
    def __init__(self, refname, parents):
        MergeNotFoundError.__init__(self, refname)
        self.msg = 'Merged via multiple parents: %s' % (' '.join(parents),)


def find_merge(commit_sha1, branch):
    """Return the SHA-1 of the commit that merged commit into branch.

    It is assumed that content is always merged in via the second or
    subsequent parents of a merge commit."""

    try:
        branch_sha1 = rev_parse('%s^{commit}' % (branch,))
    except Failure:
        raise InvalidCommitError(branch)

    if branch_sha1 == commit_sha1:
        raise DirectlyOnBranchError(branch)

    commit_graph = CommitGraph('--ancestry-path', '%s..%s' % (commit_sha1, branch_sha1))

    while True:
        branch_commits = list(commit_graph.first_parent_path(branch_sha1))

        if not branch_commits:
            raise DoesNotContainCommitError(branch)

        # The last entry in branch_commits is the one that merged in
        # commit.
        last = branch_commits[-1]
        parents = commit_graph[last]

        if parents[0] == commit_sha1:
            raise DirectlyOnBranchError(branch)

        yield last

        if commit_sha1 in parents:
            # The commit was merged in directly:
            return

        # Find which parent(s) merged in the commit:
        parents = [
            parent
            for parent in parents
            if parent in commit_graph
            ]
        assert(parents)
        if len(parents) > 1:
            raise MergedViaMultipleParentsError(branch, parents)

        [branch_sha1] = parents


def get_full_name(branch):
    """Return the full name of the specified commit.

    If branch is a symbolic reference, return the name of the
    reference that it refers to.  If it is an abbreviated reference
    name (e.g., "master"), return the full reference name (e.g.,
    "refs/heads/master").  Otherwise, just verify that it is valid,
    but return the original value."""

    try:
        full = check_git_output(
            ['git', 'rev-parse', '--verify', '-q', '--symbolic-full-name', branch]
            ).strip()
        # The above call exits successfully, with no output, if branch
        # is not a reference at all.  So only use the value if it is
        # not empty.
        if full:
            return full
    except CalledProcessError:
        pass

    # branch was not a reference, so just verify that it is valid but
    # leave it in its original form:
    rev_parse('%s^{commit}' % (branch,))
    return branch


FIRST_FORMAT = '%(refname)-38s %(name)s'
OTHER_FORMAT = FIRST_FORMAT % dict(refname='', name='via %(name)s')

COMMIT_FORMAT = '%(name)s'
BRANCH_FORMAT = '%(name)s^1..%(name)s'

WARN_FORMAT = '%(refname)-38s %(msg)s'


def name_commit(sha1, options):
    if options.describe:
        return describe(sha1) or sha1
    elif options.describe_contains:
        return describe(sha1, contains=True) or sha1
    elif options.abbrev is not None:
        return rev_parse(sha1, abbrev=options.abbrev)
    else:
        return sha1


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog='git when-merged',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
        usage=USAGE,
        epilog=EPILOG,
        )

    try:
        default_abbrev = int(
            check_git_output(['git', 'config', '--int', 'whenmerged.abbrev']).strip()
            )
    except CalledProcessError:
        default_abbrev = None

    parser.add_argument(
        '--pattern', '-p', metavar='PATTERN',
        action='append', dest='patterns', default=[],
        help=(
            'Show when COMMIT was merged to the references matching '
            'the specified regexp. If the regexp has parentheses for '
            'grouping, then display in the output the part of the '
            'reference name matching the first group.'
            ),
        )
    parser.add_argument(
        '--name', '-n', metavar='NAME',
        action='append', dest='names', default=[],
        help=(
            'Show when COMMIT was merged to the references matching the '
            'configured pattern(s) with the given name (see '
            'whenmerged.<name>.pattern below under CONFIGURATION).'
            ),
        )
    parser.add_argument(
        '--default', '-s',
        action='append_const', dest='names', const='default',
        help='Shorthand for "--name=default".',
        )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Follow merges back recursively.',
        )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--show-commit', '-c', action='store_true',
        help=(
            'Display only the SHA-1 of the merge commit. '
            'Exit with a nonzero exit code if the commit was not merged '
            'via a merge commit.'
            ),
        )
    group.add_argument(
        '--show-branch', '-b', action='store_true',
        help=(
            'Display the range of commits that were merged '
            'at the same time as the specified commit. '
            'Exit with a nonzero exit code if the commit was not merged '
            'via a merge commit. '
            'This option also affects the behavior of --log and '
            '--visualize.'
            ),
        )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--abbrev', metavar='N',
        action='store', type=int, default=default_abbrev,
        help=(
            'Abbreviate commit SHA-1s to the specified number of characters '
            '(or more if needed to avoid ambiguity).  '
            'See also whenmerged.abbrev below under CONFIGURATION.'
            ),
        )
    group.add_argument(
        '--no-abbrev', dest='abbrev', action='store_const', const=None,
        help='Do not abbreviate commit SHA-1s.',
        )
    group.add_argument(
        '--describe', action='store_true',
        help=(
            'Describe the merge commit in terms of the most recent tag '
            'reachable from the commit (see git-describe(1))'
            ),
        )
    group.add_argument(
        '--describe-contains', action='store_true',
        help=(
            'Describe the merge commit in terms of a nearby tag '
            'that contains it (see git-describe(1))'
            ),
        )
    parser.add_argument(
        '--log', '-l', action='store_true', default=False,
        help=(
            'Show the log for the merge commit. '
            'When used with "--show-branch/-b", show the log for all of '
            'the commits that were merged at the same time as the specified '
            'commit.'
            ),
        )
    parser.add_argument(
        '--diff', '-d', action='store_true', default=False,
        help='Show the diff for the merge commit.',
        )
    parser.add_argument(
        '--visualize', '-v', action='store_true', default=False,
        help=(
            'Visualize the merge commit using gitk. '
            'When used with "--show-branch/-b", only show the branch(es) '
            'that were merged at the same time as the specified commit.'
            ),
        )
    parser.add_argument(
        'commit',
        help='The commit whose destiny you would like to determine.',
        )
    parser.add_argument(
        'branch', nargs='*',
        help=(
            'The destination branch(es) into which <commit> might have been '
            'merged.  (Actually, BRANCH can be an arbitrary commit, specified '
            'in any way that is understood by git-rev-parse(1).) If neither '
            '<branch> nor --pattern/-p nor --default/-s is specified, then '
            'HEAD is used.'
            ),
        )

    options = parser.parse_args(args)

    if options.abbrev is not None and options.abbrev <= 0:
        options.abbrev = None

    if options.show_commit:
        first_format = other_format = COMMIT_FORMAT
        warn = sys.exit
    elif options.show_branch:
        first_format = other_format = BRANCH_FORMAT
        warn = sys.exit
    else:
        first_format = FIRST_FORMAT
        other_format = OTHER_FORMAT
        warn = lambda msg: sys.stdout.write(msg + '\n')

    # Convert commit into a SHA-1:
    try:
        commit_sha1 = rev_parse('%s^{commit}' % (options.commit,))
    except Failure as e:
        sys.exit(str(e))

    refpatterns = []

    for value in options.patterns:
        try:
            refpatterns.append(re.compile(value))
        except re.error as e:
            sys.stderr.write(
                'Error compiling pattern %r; ignoring: %s\n'
                % (value, e,)
                )

    for value in options.names:
        try:
            refpatterns.extend(read_refpatterns(value))
        except Failure as e:
            sys.exit(str(e))

    branches = set()

    if refpatterns:
        branches.update(
            refname
            for refname in iter_commit_refs()
            if matches_any(refname, refpatterns)
            )

    for branch in options.branch:
        try:
            branches.add(get_full_name(branch))
        except Failure as e:
            sys.exit(str(e))

    if not branches:
        branches.add(get_full_name('HEAD'))

    for branch in sorted(branches):
        first = True
        try:
            for sha1 in find_merge(commit_sha1, branch):
                name = name_commit(sha1, options)

                if first:
                    format = first_format
                else:
                    format = other_format

                sys.stdout.write(
                    format % dict(refname=branch, sha1=sha1, name=name) + '\n',
                    )

                if options.log:
                    cmd = ['git', '--no-pager', 'log']
                    if options.show_branch:
                        cmd += ['--topo-order', '%s^1..%s' % (sha1, sha1)]
                    else:
                        cmd += ['--no-walk', sha1]
                    subprocess.check_call(cmd)

                if options.diff:
                    cmd = ['git', '--no-pager', 'diff', '%s^1..%s' % (sha1, sha1)]
                    subprocess.check_call(cmd)

                if options.visualize:
                    cmd = ['gitk']

                    if options.show_branch:
                        cmd += ['%s^1..%s' % (sha1, sha1)]
                        cmd += ['--select-commit=%s' % (commit_sha1,)]
                    else:
                        cmd += ['--all']
                        cmd += ['--select-commit=%s' % (sha1,)]

                    subprocess.check_call(cmd)

                if options.recursive:
                    first = False
                else:
                    break

        except DirectlyOnBranchError as e:
            if first:
                warn(WARN_FORMAT % dict(refname=e.refname, msg=e.msg))
        except MergedViaMultipleParentsError as e:
            if first:
                warn(WARN_FORMAT % dict(refname=e.refname, msg=e.msg))
            else:
                warn(WARN_FORMAT % dict(refname='', msg=e.msg))
        except MergeNotFoundError as e:
            warn(WARN_FORMAT % dict(refname=e.refname, msg=e.msg))
        except Failure as e:
            sys.exit('%s' % (e,))


if __name__ == '__main__':
    main()
