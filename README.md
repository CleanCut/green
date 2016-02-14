# Green
## A clean, colorful, fast python test runner.

[![Version](https://img.shields.io/pypi/v/green.svg?style=flat)](https://pypi.python.org/pypi/green)
[![Posix Build Status](https://img.shields.io/travis/CleanCut/green.svg?style=flat)](https://travis-ci.org/CleanCut/green)
[![Windows Build Status](http://img.shields.io/appveyor/ci/CleanCut/green.svg?style=flat)](https://ci.appveyor.com/project/CleanCut/green)
[![Coverage Status](https://img.shields.io/coveralls/CleanCut/green.svg?style=flat)](https://coveralls.io/r/CleanCut/green?branch=master)
[![Join the chat at https://gitter.im/CleanCut/green](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/CleanCut/green?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

#### Table of Contents

1. [Features](https://github.com/CleanCut/green#features)
2. [Screenshots](https://github.com/CleanCut/green#screenshots)
3. [Getting Help](https://github.com/CleanCut/green#getting-help)
4. [Basic Usage](https://github.com/CleanCut/green#basic-usage)
5. [Basic Troubleshooting](https://github.com/CleanCut/green#basic-troubleshooting)
6. [Verbosity Levels](https://github.com/CleanCut/green#verbosity-levels)
7. [Canned Examples](https://github.com/CleanCut/green#canned-examples)
8. [Advanced Usage](https://github.com/CleanCut/green#advanced-usage)
9. [Integration](https://github.com/CleanCut/green#integration)
  - [Bash and Zsh](https://github.com/CleanCut/green#bash-and-zsh)
  - [coverage](https://github.com/CleanCut/green#coverage)
  - [Django](https://github.com/CleanCut/green#django)
  - [nose-parameterized](https://github.com/CleanCut/green#nose-parameterized)
10. [Unit Test Structure Tutorial](https://github.com/CleanCut/green#unit-test-structure-tutorial)
11. [Origin Story](https://github.com/CleanCut/green#origin-story)


Features
--------

- **Clean** - Low redundancy in output. Result statistics for each test is vertically aligned.
- **Colorful** - Terminal output makes good use of color when the terminal supports it.
- **Fast** - Tests run in independent processes.  (Only 1 by default for compatibility, try `-s 0` for best results)
- **Powerful** - Multi-target + auto-discovery.
- **Traditional** - Use the normal `unittest` classes and methods for your unit tests.
- **Descriptive** - Four verbosity levels, from just dots to full docstring output.
- **Convenient** - Bash-completion and ZSH-completion of options and test targets.
- **Thorough** - Built-in, optional integration with
  [coverage](http://nedbatchelder.com/code/coverage/).
- **Modern** - Supports Python 2.7, 3.4+, [PyPy](http://pypy.org), and [PyPy3](http://pypy.org).
- **Portable** - Completely supports OS X, Linux, and BSDs (and Windows on Python 2.7 and mostly on 3.4+).
- **Living** - This project grows and changes.  See the
  [changelog](https://github.com/CleanCut/green/blob/master/CHANGELOG.md)


Screenshots
-----------

#### Top: With Green!  Bottom: Without Green :-(

![Python Unit Test Output](https://raw.githubusercontent.com/CleanCut/green/master/screenshot.png)


Getting Help
------------

Submit **questions** about Green to [Stack
Overflow](http://stackoverflow.com/questions/ask?tags=python-green).  That gives a
large audience a chance to participate, and also make it much more likely that
the question will show up in search engines.

For **feature requests** and **bug reports** [submit an issue
](https://github.com/CleanCut/green/issues/new) to the GitHub issue tracker for
Green.


Basic Usage
-----------

You may need to prepend the installation command with `sudo` or run it as root
if your normal user cannot write to the local Python package directory.

```bash
pip3 install green    # To upgrade: "pip3 install --upgrade green"
```

Now run green...

```bash
# From inside your code directory
green

# From outside your code directory
green code_directory

# A specific file
green test_stuff.py

# A specific test inside a large package.
#
# Assuming you want to run TestClass.test_function inside
# package/test/test_module.py ...
green package.test.test_module.TestClass.test_function
```

Basic Troubleshooting
---------------------

One easy way to avoid common importing problems is to navigate to the *parent*
directory of the directory your python code is in.  Then pass green the
directory your code is in and let it autodiscover the tests (see the Tutorial below
for tips on making your tests discoverable).

```bash
cd /parent/directory
green code_directory
```

Another way to address importing problems is to carefully set up your
`PYTHONPATH` environment variable to include the parent path of your code
directory.  Then you should be able to just run `green` from _inside_ your code
directory directory.

```bash
export PYTHONPATH=/parent/directory
cd /parent/directory/code_directory
green
```

Verbosity Levels
----------------

By default, Green mimics the verbosity levels of vanilla unittest, meaning that
output is mostly just dots.  For Green we recommend adding more verbosity by
using the `-v` or `-vv` options.

Levels:
- `default` - Dots, tracebacks, and summary line.
- `-v` - Add module/class heirarchy and function names
- `-vv` - Version information added. Function names are replaced with first line of docstring.
- `-vvv` - Highest verbosity level recognized.  Details coming soon.

See the section entitled [Running Green](#running-green) for example output.

Canned Examples
---------------

To see all examples of all the failures, errors, etc. that could occur:

    green green.examples


To run Green's own internal unit tests:

    green green


Advanced Usage
--------------

See the [complete command-line
options](https://github.com/CleanCut/green/blob/master/cli-options.txt) or run
`green --help`.


Integration
-----------

### Bash and Zsh

To enable Bash-completion and Zsh-completion of options and test targets when
you press `Tab` in your terminal, add the following line to the Bash or Zsh
config file of your choice (usually `~/.bashrc` or `~/.zshrc`)

```bash
which green >& /dev/null && source "$( green --completion-file )"
```

### Coverage

Green has built-in integration support for the
[coverage](http://coverage.readthedocs.org/) module.  Just make sure `coverage`
is installed, and then add `-r` or `--run-coverage` when you run green.

### Django

Django can use green as the test runner for running tests.

- To just try it out, use the --testrunner option of `manage.py`:
```
./manage.py test --testrunner=green.djangorunner.DjangoRunner
```
- Make it persistent by adding the following line to your `settings.py`:
```python
TEST_RUNNER="green.djangorunner.DjangoRunner"
```

### nose-parameterized

Green will run generated tests created by
[nose-parameterized](https://github.com/wolever/nose-parameterized).  They have
lots of examples of how to generate tests, so follow the link above if you're
interested.


Unit Test Structure Tutorial
----------------------------

This tutorial *does* cover:

- External structure of your project (directory and file layout)
- Skeleton of a real test module
- How to import stuff from from your project into your test module
- Gotchas about naming...everything.
- Where to run green from and what the output could look like.

This tutorial *does not* cover:

- [Why you should write unit tests at
  all](http://stackoverflow.com/questions/67299/is-unit-testing-worth-the-effort)
- The benefits of [Test-Driven
  Development](http://en.wikipedia.org/wiki/Test-driven_development)
- How to use the [unittest](https://docs.python.org/library/unittest.html) module.
- How to write
  [good](http://stackoverflow.com/questions/61400/what-makes-a-good-unit-test)
  unit tests.

### External Structure ###

This is what your project layout should look like with just one module in your
package:


    proj                  # 'proj' is the package
    ├── __init__.py
    ├── foo.py            # 'foo' (or proj.foo) is the only "real" module
    └── test              # 'test' is a sub-package
        ├── __init__.py
        └── test_foo.py   # 'test_foo' is the only "test" module

Notes:

1. There is an `__init__.py` in every directory.  Don't forget it.  It can be
   an empty file, but it needs to exist.

2. `proj` itself is a directory that you will be storing somewhere.  We'll
   pretend it's in `/home/user`

3. The `test` directory needs to start with `test`.

4. The test modules need to start with `test`.


When your project starts adding code in sub-packages, you will need to make a
choice on where you put their tests.  I prefer to create a `test` subdirectory
in each sub-package.

    proj
    ├── __init__.py
    ├── foo.py
    ├── subpkg
    │   ├── __init__.py
    │   ├── bar.py
    │   └── test              # test subdirectory in every sub-package
    │       ├── __init__.py
    │       └── test_bar.py
    └── test
        ├── __init__.py
        └── test_foo.py


The other option is to start mirroring your subpackage layout from within a single test directory.

    proj
    ├── __init__.py
    ├── foo.py
    ├── subpkg
    │   ├── __init__.py
    │   ├── bar.py
    └── test
        ├── __init__.py
        ├── subpkg            # mirror sub-package layout inside test dir
        │   ├── __init__.py
        │   └── test_bar.py
        └── test_foo.py


### Skeleton of Test Module ###

Assume `foo.py` contains the following contents:

```python
def answer():
    return 42

class School():

    def food(self):
        return 'awful'

    def age(self):
        return 300
```

Here's a possible version of `test_foo.py` you could have.

```python
# Import stuff you need for the unit tests themselves to work
import unittest

# Import stuff that you want to test.  Don't import extra stuff if you don't
# have to.
from proj.foo import answer, School

# If you need the whole module, you can do this:
#     from proj import foo
#
# Here's another reasonable way to import the whole module:
#     import proj.foo as foo
#
# In either case, you would obviously need to access objects like this:
#     foo.answer()
#     foo.School()

# Then write your tests

class TestAnswer(unittest.TestCase):

    def test_type(self):
        "answer() returns an integer"
        self.assertEqual(type(answer()), int)

    def test_expected(self):
        "answer() returns 42"
        self.assertEqual(answer(), 42)

class TestSchool(unittest.TestCase):

    def test_food(self):
        school = School()
        self.assertEqual(school.food(), 'awful')

    def test_age(self):
        school = School()
        self.assertEqual(school.age(), 300)
```

Notes:

1. Your test class must subclass `unittest.TestCase`.  Technically, neither
   unittest nor Green care what the test class is named, but to be consistent
   with the naming requirements for directories, modules, and methods we
   suggest you start your test class with `Test`.

2. Start all your test method names with `test`.

3. What a test class and/or its methods _actually test_ is entirely up to you.
   In some sense it is an artform.  Just use the test classes to group a bunch
   of methods that seem logical to go together.  We suggest you try to test one
   thing with each method.

4. The methods of `TestAnswer` have docstrings, while the methods on
   `TestSchool` do not.  For more verbose output modes, green will use the
   method docstring to describe the test if it is present, and the name of the
   method if it is not.  Notice the difference in the output below.

### Running Green ###

To run the unittests, we would change to the parent directory of the project
(`/home/user` in this example) and then run `green proj`.

**In a real terminal, this output is syntax highlighted**

    $ green proj
    ....
    Ran 4 tests in 0.000s

    OK (passes=4)

Okay, so that's the classic short-form output for unit tests.  Green really
shines when you start getting more verbose:

**In a real terminal, this output is syntax highlighted**

    $ green -vv proj
    proj.test.test_foo
      TestAnswer
    .   answer() returns 42
    .   answer() returns an integer
      TestSchool
    .   test_age
    .   test_food

    Ran 4 tests in 0.001s

    OK (passes=4)

Notes:

1. Green outputs clean, heirarchical output.

2. Test status is aligned on the _left_ (the four periods correspond to four
   passing tests)

3. Method names are replaced with docstrings when present.  The first two tests
   have docstrings you can see.

4. Green always outputs a summary of statuses that will add up to the total
   number of tests that were run.  For some reason, many test runners forget
   about statuses other than Error and Fail, and even the built-in unittest runner
   forgets about passing ones.

5. Possible values for test status (these match the `unittest` short status characters exactly)
 - `.` Pass
 - `F` Failure
 - `E` Error
 - `s` Skipped
 - `x` Expected Failure
 - `u` Unexpected pass


Origin Story
------------

Green grew out of a desire to see pretty colors.  Really!  A big part of the
whole the **Red/Green/Refactor** process in test-driven-development is
_actually getting to see red and green output_.  Most python unit testing
actually goes **Gray/Gray/Refactor** (at least on my terminal, which is gray
text on black background).  That's a shame.  Even TV is in color these days.
Why not terminal output?  Even worse, the default output for most test runners
is cluttered, hard-to-read, redundant, and the dang status indicators are not
lined up in a vertical column!  Green fixes all that.

But how did Green come to be?  Why not just use one of the existing test
runners out there?  It's an interesting story, actually.  And it starts with
trial.

**trial**

Honestly, I really like Twisted's trial, though I don't really have any need
for the rest of the Twisted event-driven networking engine library.  I started
professionally developing in Python when version 2.3 was the latest, greatest
version and none of us in my small shop had ever even heard of unit testing
(gasp!).  As we grew, we matured and started testing and we chose trial to do
the test running.  If most of my projects at my day job hadn't moved to Python
3,  I probably would have just stuck with trial, but at the time I wrote green
[trial didn't run on Python 3](http://twistedmatrix.com/trac/ticket/5965)
(but since 15.4.0 it does). Trial was and is the foundation for my
inspiration for having better-than-unittest output in the first place.  It's a
great example of reducing redundancy (report module/class once, not on every
line), lining up status vertically, and using color.  I feel like Green trumps
trial in two important ways: 1) It's not part of an immense event-driven
networking engine (probably not ever going to change), and 2) it is not stuck
in Python 2 (which will hopefully be fixed someday).  Green will never replace
trial, as trial has features necessary to run asynchronous unit tests on
Twisted code.  But I couldn't use it for my increasing amount of Python 3 code.
Which led me to...

**nose**

I had really high hopes for nose.  It seemed to be widely accepted.  It seemed
to be powerful.  The output was just horrible (exactly the same as unittest's
output).  But it had a plugin system!  I tried all the plugins I could find
that mentioned improving upon the output.  When I couldn't find one I liked, I
started developing Green (yes, this Green) *as a plugin for nose*.  I chose the
name Green for three reasons: 1) It was available on PyPi! 2) I like to focus
on the positive aspect of testing (everything passes!), and 3) It made a nice
counterpoint to several nose plugins that had "Red" in the name.  I made steady
progress on my plugin until I hit a serious problem in the nose plugin API.
That's when I discovered that [nose is in maintenance
mode](https://github.com/nose-devs/nose/issues/45#issuecomment-40827502) --
abandoned by the original developers, handed off to someone who won't fix
anything if it changes the existing behavior.  What a downer.  Despite the huge
user base, I already consider nose dead and gone.  A project which will not
change (even to fix bugs!) will die.  Even the maintainer keeps pointing
everyone to...

**nose2**

So I pivoted to nose2!  I started over developing Green (same repo -- it's in
the history).  I can understand the allure of a fresh rewrite as much as the
other guy.  Nose had made less-than-ideal design decisions, and this time they
would be done right!  Hopefully.  I had started reading nose code while writing
the plugin for it, and so I dived deep into nose2.  And ran into a mess.  Nose2
is alpha.  That by itself is not necessarily a problem, if the devs will
release early and often and work to fix things you run into.  I submitted a
3-line pull request to [fix some
problems](https://github.com/nose-devs/nose2/pull/171) where the behavior did
not conform to the already-written documentation which broke my plugin.  The
pull request wasn't accepted because I (ironically) didn't write unit tests for
it.  While reading code for nose and nose2 I kept thinking, "I can write a
better test runner than *this*".  I got tired of battering on a seemingly
closed door with the nose/nose2 devs and decided to see what it would take to
write my own test runner.  That brought be to...

**unittest**

I finally went and started reading unittest (Python 2.7 and 3.4) source code.
unittest is its own special kind of mess, but it's universally built-in, and
most importantly, subclassing or replacing unittest objects to customize the
output looked a lot *easier* than writing a plugin for nose and nose2.  And it
was, for the output portion!  Writing the rest of the test runner other turned
out to be quite a project, though.  I started over on Green *again*, starting
down the road to what we have now.  A custom runner that subclasses or replaces
bits of unittest to provide exactly the output (and other feature creep) that I
wanted.


I had three initial goals for Green:

1. Colorful, clean output (at least as good as trial's)

2. Run on Python 3

3. Try to avoid making it a huge bundle of tightly-coupled, hard-to-read code.


I contend that I nailed **1.** and **2.**, and ended up implementing a bunch of
other useful features as well.  Whether I succeeded with **3.** is debatable.
I continue to try to refactor and simplify whenever I touch the code.  I'm not
sure that I'm convinced that [community acceptance of my
project](https://github.com/kennethreitz/python-guide/pull/459#issuecomment-46914167)
really hinges on full internal adherence to the PEP-8 and PEP-257 coding
styles, but I'm willing to get 98% of the way there just to see. (Hey, I *like*
vertically aligning equal signs!)  :-)

Wait!  What about the other test runners?

- **pytest** -- Somehow I never realized pytest existed until a few weeks
  before I released Green 1.0.  All I know is that apparently many people
  appear to like and use it.  Hey, don't give me that look!  I'm not
  omniscient!

- **tox** -- I think I first ran across tox only a few weeks before I heard of
  pytest.  It's homepage didn't mention anything about color, so I didn't try
  using it.

- **the ones I missed** -- Er, haven't heard of them yet either.

I'd love to hear **your** feedback regarding Green.  Like it?  Hate it?  Have
some awesome suggestions?  Whatever the case, go submit it as an
[Issue](https://github.com/CleanCut/green/issues?state=open).  I'm
not picky about what goes into the Issue tracker.  Questions, comments, bugs,
feature requests, just letting me know that I should go look at some other cool
tool.  Go for it.


